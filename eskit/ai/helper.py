import json
from dataclasses import asdict
from eskit.ai.helper_anthropic import ask as ask_claude
from eskit.ai.helper_ollama import ask as ask_ollama

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


def ask(messages, command_description, model, tools):
    handler = MODEL_HANDLERS.get(model)

    if handler is None:
        raise ValueError(f"Unsupported model: {model}")

    return handler(messages, command_description, model, tools=tools, dump_json=False)


def run_agent(question, command_description, tools, model, executor):
    messages = [
        {
            "role": "user",
            "content": question,
        }
    ]

    while True:
        response = ask(
            messages=messages,
            command_description=command_description,
            tools=tools,
            model=model,
        )

        if not response.tool_calls:
            return response.text

        if response.text:
            print(response.text)

        # append Claude's response
        messages.append(
            {
                "role": "assistant",
                "content": response.content,
            }
        )

        for tool_call in response.tool_calls:

            if tool_call.name == "ask_user":
                answer = input(tool_call.arguments["question"] + "\n> ")

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": answer,
                            }
                        ],
                    }
                )

            else:
                result = executor(tool_call, tools)

                messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_call.id,
                                "content": result,
                            }
                        ],
                    }
                )
