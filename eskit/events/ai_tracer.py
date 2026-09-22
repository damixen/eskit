import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from eskit.utils.paths import CACHE_ROOT
from eskit.events.event import Event
from eskit.events.registry import EventRegistry


class AITracer:
    def __init__(
        self,
        flow_id: str,
        path: Path | None = None,
        registry: EventRegistry | None = None,
    ) -> None:
        self.path = path or self._generate_path(flow_id)
        self.registry = registry or EventRegistry()

    def _generate_path(self, flow_id: str) -> Path:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = f"{timestamp}_{flow_id[:8]}.jsonl"

        return CACHE_ROOT / "traces" / filename

    def __call__(self, event: Event) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        data = asdict(event)
        data["type"] = self.registry.get_type(event.type_id)

        with self.path.open("a", encoding="utf-8") as f:
            json.dump(data, f, default=str)
            f.write("\n")
