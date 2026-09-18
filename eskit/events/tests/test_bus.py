# tests/events/test_bus.py

from eskit.events import Event, EventBus


def test_event_bus_notifies_listener() -> None:
    received = []
    bus = EventBus()

    bus.subscribe(received.append)

    event = Event.create(
        event_id=1,
        event_type="test_event",
        data={"value": 42},
    )

    bus.emit(event)

    assert received == [event]


def test_event_bus_notifies_multiple_listeners() -> None:
    first = []
    second = []

    bus = EventBus()
    bus.subscribe(first.append)
    bus.subscribe(second.append)

    event = Event.create(
        event_id=1,
        event_type="test_event",
    )

    bus.emit(event)

    assert first == [event]
    assert second == [event]


def test_event_bus_with_no_listeners_does_nothing() -> None:
    bus = EventBus()

    bus.emit(
        Event.create(
            event_id=1,
            event_type="test_event",
        )
    )
