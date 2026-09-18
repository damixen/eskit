from collections.abc import Callable
from dataclasses import replace
from typing import Any
from uuid import uuid4

from eskit.events.event import Event

EventListener = Callable[[Event], Any]


class EventBus:
    def __init__(self) -> None:
        self.flow_id = uuid4().hex
        self._listeners: list[EventListener] = []
        self._next_sequence_id = 1

    def subscribe(self, listener: EventListener) -> None:
        self._listeners.append(listener)

    def emit(self, event: Event) -> None:
        event = replace(
            event,
            flow_id=self.flow_id,
            sequence_id=self._next_sequence_id,
        )

        self._next_sequence_id += 1

        for listener in tuple(self._listeners):
            listener(event)
