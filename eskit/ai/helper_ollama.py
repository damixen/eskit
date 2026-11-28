import ollama
import json
from eskit.ai.response import LLMResponse
from eskit.ai.tool import ToolDefinition, ToolCall
from eskit.ai.usage import get_usage_ollama
from eskit.ai.options import AgentOptions

SYSTEM_PROMPT = """
You are ESKit AI, an assistant that helps users inspect and manage
Elasticsearch resources using the ESKit command-line toolkit.

You can execute operations through the available ESKit tools and
explain how to use ESKit commands.

The ESKit command description below is the authoritative source for
available commands, arguments, options, and their meanings.
Do not invent commands or options.

## 1. Determine the user's intent

Distinguish between two types of requests:

A. Operation requests:
When the user asks you to show, list, find, retrieve, inspect, or
perform an operation:
- Execute the appropriate available tool.
- Use the actual tool results to answer the request.
- Do not merely explain how to run a command.
- Never claim to have retrieved data without executing a tool.

Examples:
- "Show me the largest index in the cache."
  -> Call cat with kind="index", then identify the largest index.
- "List available snapshots."
  -> Call cat with kind="snap", then report the results.

B. Explanation requests:
When the user asks how to perform an operation or how a command works:
- Explain the relevant command briefly.
- Provide complete ESKit command syntax when possible.
- Do not execute the operation unless the user also requests execution.

Examples:
- "How do I list cached indices?"
  -> Explain the cat command without executing it.
- "What does the snapshot restore command do?"
  -> Explain the restore command without executing it.

## 2. Command context management

Only a subset of ESKit commands may be loaded at any time.

Before executing a command or providing its syntax:
- Check whether its command context is loaded.
- If the required context is available but not loaded, call add_context.
- Do not ask the user for permission to load a context.
- After loading the context, continue the original request.
- Do not treat loading a context as completing the request.
- Only report a command as unavailable if its required context
  is not among the available contexts.

The overview can be used to identify the relevant command context,
but not to construct command syntax.

Use the "context_level" metadata to determine whether a command
is loaded or available only as an overview.

## 3. Safety and user interaction

Respect the risk and safety metadata of ESKit commands.

For operations requiring user input, clarification, confirmation,
or a decision:
- Call the ask_user tool.
- Do not ask these questions in your text response.
- After receiving the answer, continue the original task.

Do not request unnecessary confirmation for read-only operations
or operations that already have sufficient authorization.

Do not bypass safety requirements for destructive operations.

## 4. Tool execution and results

Tool results are internal agent context and are not automatically
shown to the user.

After executing a tool:
- Examine its result.
- Return to the user's original request.
- Perform additional tool calls if necessary.
- Answer using the actual retrieved information.
- If the result is insufficient, explain what is missing.
- Do not invent missing data.

The tools ask_user, wait_tool, and add_context are agent-control tools.
Their results do not normally need to be presented to the user.

## 5. Final response

- Answer the user's specific question.
- Be concise and clear.
- Include relevant information from tool results.
- Do not provide unrelated examples or recommendations.
- Do not substitute CLI instructions for requested execution.

When a tool result contains "projected": true:

- ESKit has selected specific fields from the original
  tool result before returning it to you.
- Additional information may be available through ESKit
  if the result is not projected.
- Do not assume additional information is available
  outside the ESKit system.
- Treat the returned value as partial information.
- Do not make assumptions about omitted fields,
  including their existence, absence, or configuration.
- Explicitly acknowledge that the information is
  projected when presenting the result to the user.
- Do not make statements that imply the returned data
  represents all information in the source data.

ESKit command description:

"""


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


def to_ollama_tools(tools: list[ToolDefinition]):

    if not tools:
        return []

    return [to_ollama_tool(tool) for tool in tools]


def to_ollama_tool(tool):

    if not tool:
        return {}

    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": clean_schema(tool.input_schema),
        },
    }


def to_ollama_tool2(tool):

    if not tool:
        return {}

    return {
        "function": {
            "name": tool.name,
            "arguments": clean_schema(tool.arguments),
        },
    }


def ask(
    messages,
    command_description,
    model,
    tools,
    dump_json,
    events,
    options: AgentOptions,
):

    if not messages:
        return LLMResponse("no messages asked.")

    prompt = SYSTEM_PROMPT + json.dumps(
        command_description,
        indent=2,
    )

    for m in messages:
        if m["role"] == "system":
            messages.remove(m)
            break

    for m in messages:
        if m.get("content") and not isinstance(m["content"], str):
            m["content"] = json.dumps(m["content"])

    messages = [
        {"role": "system", "content": prompt},
        *messages,
    ]

    # print("prompt:", prompt)
    # print(json.dumps([t.to_dict() for t in tools], indent=2))

    # print(json.dumps(messages, indent=2))

    ollama_options = {
        "num_ctx": options.get("context_size") or 32768,
    }

    if options.get("max_output_token") is not None:
        ollama_options["num_predict"] = options["max_output_token"]

    input_token_counts = {}
    usage = {}
    events.llm_prompt(
        system_prompt=prompt,
        messages=messages,
        tool_def=tools,
        input_token_counts=input_token_counts,
        active_contexts=list(options["active_contexts"]),
        provider_options=ollama_options,
    )

    ollma_tools = to_ollama_tools(tools)
    if dump_json:
        with open("ollama_tools.json", "w", encoding="UTF-8") as f:
            json.dump(ollma_tools, f, indent=2)

    response = ollama.chat(
        model=model,
        messages=messages,
        tools=ollma_tools,
        options=ollama_options,
    )

    usage = get_usage_ollama(response, model)

    ollama_message = response["message"]
    tool_calls = [
        ToolCall(
            id=tool.function.name,
            name=tool.function.name,
            arguments=tool.function.arguments,
            output_mode=options["tool_call_output_mode"],
        )
        for tool in ollama_message.tool_calls or []
    ]
    # print("tool_calls:", tool_calls)

    stop_reason = "final_response"
    if len(tool_calls) > 0:
        stop_reason = "tool_call"

    res = LLMResponse(
        tool_calls=tool_calls,
        text=ollama_message.content,
        content=ollama_message.content,
    )

    events.llm_response(response=res, stop_reason=stop_reason, usage=usage)

    return res


def append_tool_messages(messages, response, tool_results):
    messages.append(
        {
            "role": "assistant",
            "tool_calls": [to_ollama_tool2(tool) for tool in response.tool_calls],
        }
    )

    for tool_call, result in tool_results:
        messages.append(
            {
                "role": "tool",
                "tool_name": tool_call.name,
                "content": result,
            }
        )
