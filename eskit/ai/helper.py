from eskit.ai.helper_anthropic import (
    ask as ask_claude,
    append_tool_messages as add_message_claude,
)
from eskit.ai.helper_ollama import (
    ask as ask_ollama,
    append_tool_messages as add_message_ollama,
)
from eskit.events.generated import EventEmitter

MODEL_HANDLERS = {
    "claude-sonnet-4-6": ask_claude,
    "claude-sonnet-5": ask_claude,
    "claude-haiku-4-5-20251001": ask_claude,
    "qwen3:4b": ask_ollama,
    "qwen3:8b": ask_ollama,
    "qwen3:14b": ask_ollama,
    "gemma3:4b": ask_ollama,
    "mistral:7b": ask_ollama,
}

MESSAGE_HANDLERS = {
    "claude-sonnet-4-6": add_message_claude,
    "claude-sonnet-5": add_message_claude,
    "claude-haiku-4-5-20251001": add_message_claude,
    "qwen3:4b": add_message_ollama,
    "qwen3:8b": add_message_ollama,
    "qwen3:14b": add_message_ollama,
    "gemma3:4b": add_message_ollama,
    "mistral:7b": add_message_ollama,
}


def ask(
    messages,
    command_description,
    model,
    tools,
    events,
    count_input_token,
    active_contexts,
    tool_call_output_mode,
):
    handler = MODEL_HANDLERS.get(model)

    if handler is None:
        raise ValueError(f"Unsupported model: {model}")

    return handler(
        messages,
        command_description,
        model,
        tools=tools,
        dump_json=False,
        events=events,
        count_input_token=count_input_token,
        active_contexts=active_contexts,
        tool_call_output_mode=tool_call_output_mode,
    )


def run_agent(
    question,
    context_builder,
    model,
    executor,
    events: EventEmitter,
    count_input_token,
    tool_call_output_mode,
):
    messages = [{"role": "user", "content": question}]

    handler = MODEL_HANDLERS[model]

    while True:
        command_description, tools, active_contexts = context_builder.get_context()

        response = ask(
            messages=messages,
            command_description=command_description,
            model=model,
            tools=tools,
            events=events,
            count_input_token=count_input_token,
            active_contexts=active_contexts,
            tool_call_output_mode=tool_call_output_mode,
        )

        if not response.tool_calls:
            events.final_response(response.text)
            return response.text

        tool_results = []

        for tool_call in response.tool_calls:
            result = executor(tool_call, tools, events, context_builder)
            tool_results.append((tool_call, result))

        MESSAGE_HANDLERS[model](
            messages,
            response,
            tool_results,
        )
