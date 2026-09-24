import json

from eskit.events.event import Event
from eskit.events.registry import EventRegistry


class AICLIListener:
    def __init__(
        self,
        verbose: bool = False,
        registry: EventRegistry | None = None,
    ) -> None:
        self.verbose = verbose
        self.registry = registry or EventRegistry()

    def __call__(self, event: Event) -> None:
        event_type = self.registry.get_type(event.type_id)

        if event_type == "ai.run_started":
            self._run_started(event)
        elif event_type == "ai.tool_call":
            self._tool_call(event)
        elif event_type == "ai.tool_result":
            self._tool_result(event)
        elif event_type == "ai.llm_prompt":
            self._prompt(event)
        elif event_type == "ai.llm_response":
            self._response(event)
        elif event_type == "ai.final_response":
            self._final_response(event)
        elif event_type == "ai.user_input_requested":
            self._user_input_requested(event)
        elif event_type == "ai.user_input_received":
            self._user_input_received(event)
        elif event_type == "ai.function_call_started":
            self._function_call_started(event)
        elif event_type == "ai.function_call_completed":
            self._function_call_completed(event)

    def _run_started(self, event: Event) -> None:
        model = event.data.get("model", "unknown")
        print(f"AI flow started ({model})")

        if self.verbose:
            print(f"  Flow ID: {event.flow_id}")

    def _tool_call(self, event: Event) -> None:
        tool = event.data.get("tool", "unknown")

        if self.verbose:
            arguments = event.data.get("arguments", {})
            print(f"→ Using {tool} {arguments}")
        else:
            print(f"→ Using {tool}")

    def _tool_result(self, event: Event) -> None:
        # print("event:", event)
        tool = event.data.get("tool", "unknown")
        print("← Received response from:", tool)

        result = event.data.get("result", "n/a")
        # print("result:", result)
        print("\tResult:", result.get("code", "n/a"))
        print("\tMessage:", result.get("message", "n/a"))

        if not self.verbose:
            return

        duration = event.data.get("duration_ms")

        if duration is not None:
            print(f"← {tool} completed ({duration} ms)")
        else:
            print(f"← {tool} completed")

    def _prompt(self, event: Event) -> None:
        print("AI prompt being sent")

        if not self.verbose:
            return

    def _response(self, event: Event) -> None:
        print("AI response received")

        usage = event.data.get("usage")

        if usage:
            print(
                f"\tUsage: {usage.get('input_tokens', 0)} input tokens, "
                f"{usage.get('output_tokens', 0)} output tokens"
                f"\n\testimate: Input Cost - ${usage.get('input_cost', 0):.6f}, "
                f"Output Cost - ${usage.get('output_cost', 0):.6f}"
            )

        print(f"\tstop_reason: {event.data.get('stop_reason', 'n/a')}")

        if not self.verbose:
            return

    def _final_response(self, event: Event) -> None:
        print("AI final response received")

        if not self.verbose:
            return

    def _user_input_requested(self, event: Event) -> None:
        if not self.verbose:
            return

    def _user_input_received(self, event: Event) -> None:
        if not self.verbose:
            return

    def _function_call_started(self, event: Event) -> None:
        if not self.verbose:
            return

    def _function_call_completed(self, event: Event) -> None:
        if not self.verbose:
            return
