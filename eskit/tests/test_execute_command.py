from unittest.mock import Mock, patch

from eskit.ai.tool import ToolCall, ToolDefinition, to_argparse
from eskit.result import ResultCode, Result  # Adjust import
from eskit.cli import execute_command  # Adjust import
from types import SimpleNamespace


def test_execute_command_invalid_argument():
    tool_call = ToolCall(
        id="abc",
        name="cat",
        arguments={"kind": "repo", "name": "*"},
    )

    events = Mock()
    context_builder = Mock()
    tools = [ToolDefinition(name="cat", description="", input_schema={})]

    with (
        patch("eskit.cli.build_parser") as mock_build_parser,
        patch("eskit.cli.describe_parser") as mock_describe_parser,
        patch(
            "eskit.ai.tool.to_argparse",
            side_effect=ValueError(
                "Argument 'name' not found for command 'cat'"
            ),
        ),
        patch("eskit.cli.result_to_ai_response") as mock_response,
    ):
        mock_build_parser.return_value = Mock()
        mock_describe_parser.return_value = {"commands": {}}
        mock_response.return_value = "Invalid argument"

        response = execute_command(
            tool_call,
            tools,
            events,
            context_builder,
        )

    assert response == "Invalid argument"

    events.function_call_completed.assert_called_once()

    name, source, result = (
        events.function_call_completed.call_args.args
    )

    assert name == "cat"
    assert source == "eskit"
    assert result.code == ResultCode.INVALID_ARGUMENT
    assert result.message == (
        "Argument 'name' not found for command 'cat'"
    )

    events.tool_result.assert_called_once()

    result_payload = events.tool_result.call_args.args[1]

    assert result_payload["code"] == ResultCode.INVALID_ARGUMENT
    assert result_payload["message"] == result.message

    mock_response.assert_called_once_with(result)



def test_execute_command_success():
    tool_call = ToolCall(
        id="abc",
        name="cat",
        arguments={
            "kind": "index",
            "json": True,
        },
    )

    events = Mock()
    context_builder = Mock()
    tools = [SimpleNamespace(name="cat")]

    command_result = Result(
        code=ResultCode.SUCCESS,
        message="",
        value=[{"index": "test-index", "store.size": "1gb"}],
    )

    # Only needed if your Result doesn't initialize this attribute.
    command_result.command_context = None

    fake_parser = Mock()
    fake_parsed_args = SimpleNamespace(
        function=Mock(return_value=command_result)
    )
    fake_parser.parse_args.return_value = fake_parsed_args

    with (
        patch("eskit.cli.build_parser", return_value=fake_parser),
        patch(
            "eskit.cli.describe_parser",
            return_value={"commands": {}},
        ),
        patch(
            "eskit.ai.tool.to_argparse",
            return_value=["cat", "index", "--json"],
        ),
        patch(
            "eskit.cli.result_to_ai_response",
            return_value='[{"index": "test-index"}]',
        ) as mock_response,
    ):
        response = execute_command(
            tool_call,
            tools,
            events,
            context_builder,
        )

    fake_parser.parse_args.assert_called_once_with(
        ["cat", "index", "--json"]
    )

    fake_parsed_args.function.assert_called_once_with(
        fake_parsed_args
    )

    assert response == '[{"index": "test-index"}]'

    events.function_call_completed.assert_called_once_with(
        "cat", "eskit", command_result
    )

    events.tool_result.assert_called_once()

    payload = events.tool_result.call_args.args[1]

    assert payload["code"] == ResultCode.SUCCESS
    assert payload["value"] == command_result.value

    mock_response.assert_called_once_with(command_result)
