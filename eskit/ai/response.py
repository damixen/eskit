from dataclasses import dataclass


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str | None = None
    tool_call: ToolCall | None = None
