from dataclasses import asdict, dataclass
import json
from typing import Any
from eskit.ai.response import ToolCall


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


def tools_to_json(tools: list[ToolDefinition]) -> str:
    return json.dumps(
        [tool.to_dict() for tool in tools],
        indent=2,
    )


def add_ask_user_tool(tools):
    ask_user_tool = ToolDefinition(
        name="ask_user",
        description=(
            "Ask the user a question and wait for their answer. "
            "Use this tool whenever you need information, clarification, "
            "confirmation, or a decision from the user before continuing. "
            "Do not ask the user a question in your response text when the "
            "answer is needed to continue; call this tool instead."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user.",
                }
            },
            "required": ["question"],
        },
    )
    tools.append(ask_user_tool)


def add_wait_tool(tools):
    add_wait_tool = ToolDefinition(
        name="wait_tool",
        description=(
            "Use this tool whenever you need to wait when user instructs to do so for a certain period."
            "You may be given a time to wait or simply be told to wait between repetitive operations."
            "Do not ask a user for a confirmation to proceed after calling this tool."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "duration": {
                    "type": "integer",
                    "description": "The duration of time to wait.",
                },
                "previous_tool": {
                    "type": "string",
                    "description": "Name of the previous tool used before this wait.",
                },
                "next_tool": {
                    "type": "string",
                    "description": "Name of the next tool to be executed after this wait.",
                },
            },
            "required": ["previous_tool", "next_tool"],
        },
    )
    tools.append(add_wait_tool)


def build_tool_definitions(
    command_data: dict[str, Any],
) -> list[ToolDefinition]:
    """Build a flat list of tool definitions from ESKit command data."""
    tools: list[ToolDefinition] = []

    common_arguments = command_data.get("common_arguments", {})

    for name, command in command_data.get("commands", {}).items():
        command = _expand_common_arguments(
            command,
            common_arguments,
        )

        _collect_tools(
            tools=tools,
            name=name,
            command=command,
            path=[name],
        )

    add_ask_user_tool(tools)
    add_wait_tool(tools)

    return tools


def _expand_common_arguments(
    command: dict[str, Any],
    common_arguments: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Expand common argument names into argument definitions."""
    common_names = command.get("common_arguments", [])

    if not common_names:
        return command

    arguments = list(command.get("arguments", []))

    for name in common_names:
        argument = common_arguments.get(name)

        if argument is not None:
            arguments.append(argument)

    expanded = dict(command)
    expanded["arguments"] = arguments

    return expanded


def _collect_tools(
    tools: list[ToolDefinition],
    name: str,
    command: dict[str, Any],
    path: list[str],
) -> None:
    commands = command.get("commands", {})

    if commands:
        for child_name, child_command in commands.items():
            _collect_tools(
                tools=tools,
                name=child_name,
                command=child_command,
                path=[*path, child_name],
            )
        return

    tools.append(
        ToolDefinition(
            name="_".join(path),
            description=command.get("description", ""),
            input_schema=_build_input_schema(command),
        )
    )


def _build_input_schema(
    command: dict[str, Any],
) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []

    for argument in command.get("arguments", []):
        name = argument["name"]

        properties[name] = {
            "type": _json_schema_type(argument.get("type")),
            "description": argument.get("description", ""),
        }

        if argument.get("choices"):
            properties[name]["enum"] = argument["choices"]

        if argument.get("default") is not None:
            properties[name]["default"] = argument["default"]

        if argument.get("required"):
            required.append(name)

        flags = argument.get("flags")
        if flags is not None and len(flags) == 0:
            properties[name]["positional"] = True

    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
    }

    if required:
        schema["required"] = required

    return schema


def _json_schema_type(argument_type: str | None) -> str:
    return {
        "str": "string",
        "string": "string",
        "int": "integer",
        "float": "number",
        "boolean": "boolean",
    }.get(argument_type or "", "string")


def find_command_description(
    commands: dict,
    tool_name: str,
) -> tuple[dict, list[str]] | None:
    """Find command description and CLI path from a flattened tool name."""

    for name, command in commands.items():
        # Direct command match.
        if name == tool_name:
            return command, [name]

        nested_commands = command.get("commands", {})

        if not nested_commands:
            continue

        # Check whether this command is the first component
        # of the flattened tool name.
        prefix = f"{name}_"

        if tool_name.startswith(prefix):
            child_name = tool_name[len(prefix) :]

            result = find_command_description(
                nested_commands,
                child_name,
            )

            if result is not None:
                child_command, child_path = result
                return child_command, [name, *child_path]

    return None


def to_argparse(
    llm_tool_output: ToolCall,
    command_descriptions: dict,
    tools_definitions: list[ToolDefinition],
) -> list[str]:
    """Convert an LLM tool call back into argparse-style CLI arguments."""

    tool_definition = next(
        (tool for tool in tools_definitions if tool.name == llm_tool_output.name),
        None,
    )

    if tool_definition is None:
        raise ValueError(f"Tool definition not found: {llm_tool_output.name}")

    result = find_command_description(
        command_descriptions,
        tool_definition.name,
    )

    if result is None:
        raise ValueError(f"Command description not found: {tool_definition.name}")

    command, command_path = result

    argument_definitions = {
        argument["name"]: argument for argument in command.get("arguments", [])
    }

    args = list(command_path)

    for name, value in llm_tool_output.arguments.items():
        argument = argument_definitions.get(name)

        if argument is None:
            raise ValueError(
                f"Argument '{name}' not found for command " f"'{tool_definition.name}'"
            )

        flags = argument.get("flags", [])

        # Positional argument
        if not flags:
            if isinstance(value, list):
                args.extend(str(item) for item in value)
            else:
                args.append(str(value))

            continue

        # Prefer long form.
        flag = next(
            (item for item in flags if item.startswith("--")),
            flags[0],
        )

        # Boolean flag
        if argument.get("type") == "boolean":
            if value:
                args.append(flag)

            continue

        # Optional argument with a value.
        args.append(flag)

        if isinstance(value, list):
            args.extend(str(item) for item in value)
        else:
            args.append(str(value))

    return args
