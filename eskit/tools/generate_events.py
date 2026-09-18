import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "eskit" / "events" / "registry.json"
OUTPUT = ROOT / "eskit" / "events" / "generated.py"


TYPE_MAP = {
    "str": "str",
    "dict": "dict",
    "Any": "Any",
    "int": "int",
    "bool": "bool",
    "list": "list",
}

EVENT_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


def load_registry() -> dict:
    with REGISTRY.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_registry(registry: dict) -> None:
    if not isinstance(registry, dict):
        raise ValueError("Registry must be an object")

    if not isinstance(registry.get("version"), int):
        raise ValueError("Registry version must be an integer")

    events = registry.get("events")

    if not isinstance(events, dict):
        raise ValueError("Registry must contain an 'events' object")

    seen_types = set()
    seen_ids = set()

    for event_id, event in events.items():
        # Event ID
        try:
            numeric_id = int(event_id)
        except (TypeError, ValueError):
            raise ValueError(f"Invalid event ID: {event_id!r}")

        if numeric_id <= 0:
            raise ValueError(f"Event ID must be positive: {event_id!r}")

        if numeric_id in seen_ids:
            raise ValueError(f"Duplicate event ID: {numeric_id}")

        seen_ids.add(numeric_id)

        # Event definition
        if not isinstance(event, dict):
            raise ValueError(f"Event {event_id} must be an object")

        event_type = event.get("type")

        if not isinstance(event_type, str):
            raise ValueError(f"Event {event_id} must have a string 'type'")

        # Event type format
        if not EVENT_TYPE_PATTERN.match(event_type):
            raise ValueError(f"Invalid event type: {event_type!r}")

        # Unique event type
        if event_type in seen_types:
            raise ValueError(f"Duplicate event type: {event_type!r}")

        seen_types.add(event_type)

        # Description
        if not isinstance(event.get("description"), str):
            raise ValueError(f"Event {event_type} must have a string 'description'")

        # Parameters
        parameters = event.get("parameters", {})

        if not isinstance(parameters, dict):
            raise ValueError(f"Parameters for {event_type} must be an object")

        for parameter, type_name in parameters.items():
            if not isinstance(parameter, str):
                raise ValueError(f"Invalid parameter name in {event_type}")

            if not type_name in TYPE_MAP:
                raise ValueError(
                    f"Unsupported parameter type "
                    f"{type_name!r} in "
                    f"{event_type}.{parameter}"
                )


def event_constant(event_type: str) -> str:
    return event_type.upper().replace(".", "_")


def method_name(event_type: str) -> str:
    return event_type.split(".", 1)[1]


def python_type(type_name: str) -> str:
    try:
        return TYPE_MAP[type_name]
    except KeyError:
        raise ValueError(f"Unsupported event parameter type: {type_name}")


def generate_event_constants(registry: dict) -> list[str]:
    lines = []

    for event_id, event in registry["events"].items():
        constant = event_constant(event["type"])
        lines.append(f"{constant} = {event_id}")

    return lines


def generate_event_method(event: dict) -> list[str]:
    event_type = event["type"]
    constant = event_constant(event_type)
    name = method_name(event_type)
    parameters = event.get("parameters", {})

    lines = []

    if parameters:
        lines.append(f"    def {name}(")
        lines.append("        self,")

        for parameter, type_name in parameters.items():
            lines.append(f"        {parameter}: " f"{python_type(type_name)},")

        lines.append("    ) -> None:")
    else:
        lines.append(f"    def {name}(self) -> None:")

    lines.append("        self._emit(")
    lines.append(f"            {constant},")

    if parameters:
        lines.append("            {")
        for parameter in parameters:
            lines.append(f'                "{parameter}": {parameter},')
        lines.append("            },")
    else:
        lines.append("            {},")

    lines.append("        )")
    lines.append("")

    return lines


def generate_emitter(registry: dict) -> list[str]:
    lines = [
        "class EventEmitter:",
        "    def __init__(self, bus: EventBus) -> None:",
        "        self._bus = bus",
        "",
        "    def _emit(",
        "        self,",
        "        type_id: int,",
        "        data: dict[str, Any],",
        "    ) -> None:",
        "        self._bus.emit(",
        "            Event.create(",
        "                type_id=type_id,",
        "                data=data,",
        "            )",
        "        )",
        "",
    ]

    for event in registry["events"].values():
        if event["type"].startswith("ai."):
            lines.extend(generate_event_method(event))

    return lines


def generate(registry: dict) -> str:
    lines = [
        "# AUTO-GENERATED FILE.",
        "# DO NOT EDIT.",
        "# Generated by eskit.tools.generate_events.",
        "",
        '"""Generated event definitions."""',
        "",
        "from typing import Any",
        "",
        "from eskit.events.bus import EventBus",
        "from eskit.events.event import Event",
        "",
    ]

    lines.extend(generate_event_constants(registry))
    lines.append("")
    lines.extend(generate_emitter(registry))

    return "\n".join(lines)


def main() -> None:
    registry = load_registry()

    validate_registry(registry)

    output = generate(registry)

    OUTPUT.write_text(output, encoding="utf-8")

    print(f"Generated {OUTPUT}")


if __name__ == "__main__":
    main()
