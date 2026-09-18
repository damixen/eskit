from eskit.events import Event, EventBus
from eskit.events.ai_cli_listener import AIConsoleListener

def main():
    bus = EventBus()
    bus.subscribe(AIConsoleListener(verbose=True))

    bus.emit(Event.create(
        1,
        "tool_call",
        {"tool": "index_status", "arguments": {"host": "HP-DO"}}
    ))

    bus.emit(Event.create(
        2,
        "tool_result",
        {"tool": "index_status", "duration_ms": 312}
    ))


if __name__ == "__main__":
    main()
