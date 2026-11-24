from eskit.ai.tool import ToolCall, ToolDefinition, to_argparse
from eskit.ai.context import ContextToolBuilder
from eskit.result import ResultCode, Result  # Adjust import
from eskit.cli import execute_command  # Adjust import
from eskit.cli import build_parser, describe_parser
from unittest.mock import Mock, patch


def test_execute_command_invalid_argument():
    tool_call = ToolCall(
        id="abc",
        name="cat",
        arguments={"kind": "index"},
    )


    parser = build_parser()
    command_ir = describe_parser(parser)

    contexts = {"cat"}
    builder = ContextToolBuilder(command_ir, contexts)

    command_description, tools, active_contexts = builder.get_context()

    events = Mock()
    print(tools)
    resutl = execute_command(
        tool_call,
        tools,
        events,
        builder
    )

    print(resutl)
