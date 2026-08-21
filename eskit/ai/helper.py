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

def ask(question, command_description, model):
    handler = MODEL_HANDLERS.get(model)

    if handler is None:
        raise ValueError(f"Unsupported model: {model}")

    return handler(question, command_description, model)