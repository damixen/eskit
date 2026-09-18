import json
from pathlib import Path

_REGISTRY_PATH = Path(__file__).with_name("registry.json")


class EventRegistry:
    def __init__(self, path: Path = _REGISTRY_PATH) -> None:
        with path.open("r", encoding="utf-8") as f:
            registry = json.load(f)

        self.version = registry["version"]
        self._events = registry["events"]

        self._type_to_id = {
            event["type"]: int(event_id) for event_id, event in self._events.items()
        }

    def get_id(self, event_type: str) -> int:
        return self._type_to_id[event_type]

    def get_type(self, event_id: int) -> str:
        return self._events[str(event_id)]["type"]

    def get_description(self, event_type: str) -> str:
        event_id = self._type_to_id[event_type]
        return self._events[str(event_id)]["description"]
