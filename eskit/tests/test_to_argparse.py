import pytest

from eskit.ai.tool import ToolCall, to_argparse, ToolDefinition
from eskit.cli import build_parser, describe_parser


def test_to_argparse_rejects_unknown_argument():
    tool_call = ToolCall(
        id="abc",
        name="cat",
        arguments={
            "kind": "repo",
            "name": "*",
        },
    )

    parser = build_parser()
    command_descriptions = describe_parser(parser)

    tools = [ToolDefinition(name="cat", description="", input_schema={})]

    with pytest.raises(
        ValueError,
        match="Argument 'name' not found",
    ):
        to_argparse(
            tool_call,
            command_descriptions["commands"],
            tools,
        )

def test_to_argparse_success():
    parser = build_parser()
    command_ir = describe_parser(parser)

    tool_call = ToolCall(
        id="abc",
        name="cat",
        arguments={
            "kind": "index",
            "json": True,
            "flat": False,
        },
    )

    tools = [ToolDefinition(name="cat", description="", input_schema={})]

    args = to_argparse(
        tool_call,
        command_ir["commands"],
        tools,
    )

    assert args[:2] == ["cat", "index"]
    assert "--json" in args
    assert "--flat" not in args

    parsed_args = parser.parse_args(args)

    assert parsed_args.json is True
    assert parsed_args.flat is False