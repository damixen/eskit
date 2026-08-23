import json
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from eskit.ai.usage import print_usage
from eskit.ai.tool import ToolDefinition
from eskit.ai.response import LLMResponse, ToolCall

SYSTEM_PROMPT = """
You are an AI assistant for ESKit.

You help users understand how to use the ESKit command-line interface.

The ESKit command description below is the authoritative source for
available commands, arguments, options, and their meanings.

When answering a question about how to perform an operation:
- Explain the relevant command briefly.
- Provide the complete ESKit command when possible.
- Do not execute commands.
- Do not invent commands or options that are not present in the command description.
- Respect safety metadata and explain destructive operations when relevant.

ESKit command description:

"""


def ask(question, command_description, model, tools, dump_json):

    if not question:
        return LLMResponse("no question asked.")

    load_dotenv()

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    anthropic_tools = to_anthropic_tools(tools)

    if dump_json:
        with open("anthropic_tools.json", "w", encoding="UTF-8") as f:
            json.dump(anthropic_tools, f, indent=2)

    prompt = SYSTEM_PROMPT + json.dumps(
        command_description,
        indent=2,
    )

    response = client.messages.create(
        model=model,
        max_tokens=10000,
        system=prompt,
        messages=[
            {
                "role": "user",
                "content": question,
            }
        ],
        tools=anthropic_tools,
    )

    print_usage(response, model)

    #
    # Final answer
    #
    if response.stop_reason != "tool_use":
        return LLMResponse(text=response.content[0].text)

    #
    # Claude wants a tool
    #

    #print("response.content:", response.content)

    tool = next(block for block in response.content if block.type == "tool_use")

    return LLMResponse(
        tool_call=ToolCall(id=tool.id, name=tool.name, arguments=tool.input)
    )


def to_anthropic_tools(tools: list[ToolDefinition]):

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": clean_schema(tool.input_schema),
        }
        for tool in tools
    ]


def clean_schema(schema):
    if isinstance(schema, dict):
        cleaned = {}

        for key, value in schema.items():
            if key == "description" and value is None:
                continue

            cleaned[key] = clean_schema(value)

        return cleaned

    if isinstance(schema, list):
        return [clean_schema(item) for item in schema]

    return schema


def remove_defaults(value):
    if isinstance(value, dict):
        return {
            key: remove_defaults(val) for key, val in value.items() if key != "default"
        }

    if isinstance(value, list):
        return [remove_defaults(item) for item in value]

    return value
