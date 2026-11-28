from typing import TypedDict


class AgentOptions(TypedDict):
    count_input_token: bool
    tool_call_output_mode: str
    context_size: int | None
    max_output_token: int | None
    active_contexts: list[str]
    tool_call_projections: dict[str, list[tuple[str, ...]]]
