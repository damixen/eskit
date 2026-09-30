from typing import Any

from eskit.events.event import Event
from eskit.events.registry import EventRegistry


class AICLIListener:
    """Render AI events as a human-readable CLI transcript."""

    def __init__(
        self,
        verbose: bool = False,
        registry: EventRegistry | None = None,
    ) -> None:
        self.verbose = verbose
        self.registry = registry or EventRegistry()

    def __call__(self, event: Event) -> None:
        event_type = self.registry.get_type(event.type_id)

        handlers = {
            "ai.run_started": self._run_started,
            "ai.tool_call": self._tool_call,
            "ai.tool_result": self._tool_result,
            "ai.llm_prompt": self._prompt,
            "ai.llm_response": self._response,
            "ai.final_response": self._final_response,
            "ai.user_input_requested": self._user_input_requested,
            "ai.user_input_received": self._user_input_received,
            "ai.function_call_started": self._function_call_started,
            "ai.function_call_completed": self._function_call_completed,
        }

        handler = handlers.get(event_type)

        if handler:
            handler(event)

    # ------------------------------------------------------------------
    # Flow
    # ------------------------------------------------------------------

    def _run_started(self, event: Event) -> None:
        model = event.data.get("model", "unknown")

        print(f"AI flow started ({model})")

        if self.verbose:
            print(f"  flow_id: {event.flow_id}")
            print(f"  client: {event.data.get('client', 'unknown')}")

    def _final_response(self, event: Event) -> None:
        # The actual response text is rendered by _response().
        # Keep this event mostly as a lifecycle marker.
        if self.verbose:
            print("AI flow completed")

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    def _response(self, event: Event) -> None:
        response = event.data.get("response")

        if response is None:
            return

        # Text accompanying a tool call is still useful to the user.
        #
        # Example:
        #   "I'll load the necessary command context first."
        #
        # The tool result itself is intentionally not printed here.
        # It is internal context for the LLM.
        response_text = getattr(response, "text", None)

        if self.verbose:
            print()
            print("[trace] LLM response")
    
            usage = event.data.get("usage")
    
            if usage:
                self._print_usage(usage)
    
            stop_reason = event.data.get("stop_reason")
    
            if stop_reason:
                print(f"  stop_reason: {stop_reason}")

        if response_text:
            print()
            print("AI >>")
            print(response_text)
        

    def _prompt(self, event: Event) -> None:
        if not self.verbose:
            return

        print()
        print("[trace] LLM prompt")

        print(f"  input tokens: " f"{event.data.get('input_token_counts', {})}")

        print(f"  active contexts: " f"{event.data.get('active_contexts', [])}")

    def _print_usage(self, usage: dict[str, Any]) -> None:
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        input_cost = usage.get("input_cost", 0)
        output_cost = usage.get("output_cost", 0)

        print(
            f"  usage: " f"{input_tokens:,} input / " f"{output_tokens:,} output tokens"
        )

        print(f"  estimated cost: " f"${input_cost + output_cost:.6f}")

    # ------------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------------

    def _tool_call(self, event: Event) -> None:
        tool = event.data.get("tool", "unknown")
        
        if self.verbose:
            print()
            print("[trace] AI tool call")
            arguments = event.data.get("arguments")
            
            if arguments:
                self._print_arguments(arguments)

        print()
        print(f"→ {tool}")


    def _tool_result(self, event: Event) -> None:
        tool = event.data.get("tool", "unknown")
        result = event.data.get("result")

        # Tool results should normally be normalized dictionaries.
        # Be defensive so a malformed event cannot crash the listener.
        if isinstance(result, dict):
            code = result.get("code", "unknown")
            print(f"✓ {tool} ({code})")

            if self.verbose:
                message = result.get("message")

                if message:
                    print(f"  message: {message}")
        else:
            print(f"✓ {tool}")

            if self.verbose and result is not None:
                print(f"  result: {result!r}")

        if self.verbose:
            duration = event.data.get("duration_ms")

            if duration is not None:
                print(f"  duration: {duration} ms")

    def _print_arguments(self, arguments: Any) -> None:
        if isinstance(arguments, dict):
            for key, value in arguments.items():
                print(f"  {key}: {value}")
        else:
            print(f"  arguments: {arguments}")

    # ------------------------------------------------------------------
    # User interaction
    # ------------------------------------------------------------------

    def _user_input_requested(self, event: Event) -> None:
        message = event.data.get("message")

        if message:
            print()
            print(f"AI: {message}")

    def _user_input_received(self, event: Event) -> None:
        if self.verbose:
            print("[trace] User input received")

    # ------------------------------------------------------------------
    # Function lifecycle
    # ------------------------------------------------------------------

    def _function_call_started(self, event: Event) -> None:
        if not self.verbose:
            return

        function = event.data.get("function", "unknown")
        execution_type = event.data.get("execution_type", "unknown")
        arguments = event.data.get("arguments")

        print()
        print("[trace] function started")
        print(f"  function: {function}")
        print(f"  execution: {execution_type}")

        if arguments:
            print(f"  arguments: {arguments}")

    def _function_call_completed(self, event: Event) -> None:
        if not self.verbose:
            return

        function = event.data.get("function", "unknown")
        execution_type = event.data.get("execution_type", "unknown")
        result = event.data.get("result")

        print("[trace] function completed")
        print(f"  function: {function}")
        print(f"  execution: {execution_type}")

        if result is not None:
            print(f"  result: {result}")
