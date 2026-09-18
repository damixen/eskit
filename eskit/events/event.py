from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Event:
    type_id: int
    timestamp: datetime
    data: dict[str, Any] = field(default_factory=dict)
    flow_id: str | None = None
    sequence_id: int | None = None

    @classmethod
    def create(
        cls,
        type_id: int,
        data: dict[str, Any] | None = None,
    ) -> "Event":
        return cls(
            type_id=type_id,
            timestamp=datetime.now(timezone.utc),
            data=data or {},
        )
