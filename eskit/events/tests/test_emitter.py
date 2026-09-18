from eskit.events.bus import EventBus
from eskit.events.generated import (
    AIEventEmitter,
    AI_TOOL_CALL,
    AI_TOOL_RESULT,
)


def test_emitter_uses_bus_sequence_ids():
    events = []

    bus = EventBus()
    bus.subscribe(events.append)

    emitter = AIEventEmitter(bus)

    emitter.tool_call(
        tool="index_status",
        arguments={"index": "logs-*"},
    )

    emitter.tool_result(
        tool="index_status",
        result={"status": "green"},
    )

    assert len(events) == 2

    assert events[0].type_id == AI_TOOL_CALL
    assert events[0].sequence_id == 1

    assert events[1].type_id == AI_TOOL_RESULT
    assert events[1].sequence_id == 2