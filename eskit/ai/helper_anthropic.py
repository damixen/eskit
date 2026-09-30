import json
import os
from dotenv import load_dotenv
from anthropic import Anthropic
from eskit.ai.usage import print_usage, get_usage
from eskit.ai.tool import ToolDefinition
from eskit.ai.response import LLMResponse, ToolCall
from eskit.events.generated import EventEmitter

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

When you need information, clarification, confirmation, or a decision from the user
in order to continue executing their request:
- You MUST call the ask_user tool.
- Do not ask such questions in your text response. The ask_user tool is the mechanism
for interactive user input.
- After receiving the user's answer through ask_user, continue with the original task.

When handling a request:

1. If the current command context does not contain the commands needed
   to complete the request, check the available contexts.

2. If a required context is available, you MUST call add_context tool
   before telling the user that the command is unavailable.

3. Calling add_context is an internal agent action. NEVER ask the user
   for permission to load an available context.

4. After calling add_context, continue working on the original request
   using the newly available commands.

5. Only tell the user that a command is unavailable if the required
   context is not among the available contexts.
   
6. Loading a context does not complete the user's request.
   After loading the required contexts, use the available commands
   to actually complete the request when the user has asked you to
   perform the operation.
   
7. Do not merely describe commands that could accomplish the request
   when those commands are available as tools and the user asked you
   to execute the operation.
   
8. Do not ask for the confirmation to execute commands after adding/loading context
   if you have enough context to do so.
   
The currently loaded commands are only a subset of the available ESKit
commands. Do not assume that a required command is unavailable simply
because it is not in the current command context.

If the command needed to fulfill the request is not currently loaded,
check the available contexts and use add_context before proceeding.

If your answer will include a concrete ESKit command or command syntax,
make sure the relevant command context is loaded before providing it.
The overview may be used to identify the relevant context, but do not
construct command syntax from the overview alone. The "context_level" in the 
ESKit command description shows if the command context is at overview or loaded.

Tool results are internal agent context and are not shown to the user or terminal.

After a tool call, do not assume the user can see the tool result. Use the
result to determine what to tell the user and, when appropriate, present
the relevant information in a clear, user-friendly form.

The tools ask_user, wait_tool, and add_context are agent-control tools.
Their results do not need to be presented to the user.

ESKit command description:

"""


def ask(
    messages,
    command_description,
    model,
    tools,
    dump_json,
    events: EventEmitter,
    count_input_token,
    active_contexts,
):

    if not messages:
        return LLMResponse("no question asked.")

    load_dotenv()

    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    anthropic_tools = to_anthropic_tools(tools)

    if dump_json:
        with open("anthropic_tools.json", "w", encoding="UTF-8") as f:
            json.dump(anthropic_tools, f, indent=2)

    prompt = SYSTEM_PROMPT + json.dumps(command_description)

    input_token_counts = {}
    if count_input_token:
        _messages = [
            {
                "role": "user",
                "content": "hi",
            }
        ]

        # command_ir
        response = client.messages.count_tokens(
            model=model,
            system=json.dumps(
                command_description,
            ),
            messages=_messages,
        )
        input_token_counts["command_ir"] = response.input_tokens
        # print("command_ir:", input_token_counts["command_ir"])

        # prompt
        response = client.messages.count_tokens(
            model=model,
            system=prompt,
            messages=_messages,
        )
        input_token_counts["prompt"] = response.input_tokens
        # print("prompt:", input_token_counts["prompt"])

        # messages
        response = client.messages.count_tokens(
            model=model,
            messages=messages,
        )
        input_token_counts["messages"] = response.input_tokens
        # print("messages:", response.input_tokens)

        # tools
        response = client.messages.count_tokens(
            model=model,
            tools=anthropic_tools,
            messages=_messages,
        )
        input_token_counts["tools"] = response.input_tokens
        # print("tools:", response.input_tokens)

        # all
        response = client.messages.count_tokens(
            model=model,
            system=prompt,
            messages=messages,
            tools=anthropic_tools,
        )
        input_token_counts["all"] = response.input_tokens
        # print("all:", response.input_tokens)

    events.llm_prompt(
        system_prompt=prompt,
        messages=messages,
        tool_def=tools,
        input_token_counts=input_token_counts,
        active_contexts=list(active_contexts),
    )

    response = client.messages.create(
        model=model,
        max_tokens=10000,
        system=prompt,
        messages=messages,
        tools=anthropic_tools,
    )

    usage = get_usage(response, model)

    texts = [block.text for block in response.content if block.type == "text"]

    text = "\n".join(texts) if texts else None

    tool_calls = [
        ToolCall(
            id=block.id,
            name=block.name,
            arguments=block.input,
        )
        for block in response.content
        if block.type == "tool_use"
    ]

    stop_reason = "final_response"
    if len(tool_calls) > 0:
        stop_reason = "tool_call"

    res = LLMResponse(tool_calls=tool_calls, text=text, content=response.content)

    events.llm_response(response=res, stop_reason=stop_reason, usage=usage)

    return res


def to_anthropic_tools(tools: list[ToolDefinition]):

    if not tools:
        return []

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
