import json

from eskit.events.ai_tracer import AITracer
from eskit.events.bus import EventBus
from eskit.events.generated import AI_TOOL_CALL, EventEmitter


def test_tracer_writes_event(tmp_path):
    path = tmp_path / "trace.jsonl"

    bus = EventBus()
    tracer = AITracer(path)
    bus.subscribe(tracer)

    emitter = EventEmitter(bus)

    emitter.tool_call(
        tool="index_create",
        arguments={"index": "wait_test"},
    )

    lines = path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1

    event = json.loads(lines[0])

    assert event["type_id"] == AI_TOOL_CALL
    assert event["sequence_id"] == 1
    assert event["flow_id"] == bus.flow_id

    assert event["data"]["tool"] == "index_create"
    assert event["data"]["arguments"] == {
        "index": "wait_test",
    }


def test_tracer_appends_events(tmp_path):
    path = tmp_path / "trace.jsonl"

    bus = EventBus()
    tracer = AITracer(path)
    bus.subscribe(tracer)

    emitter = EventEmitter(bus)

    emitter.tool_call(
        tool="index_create",
        arguments={"index": "wait_test"},
    )
    emitter.tool_call(
        tool="wait_tool",
        arguments={
            "duration": 5,
            "previous_tool": "index_create",
            "next_tool": "index_delete",
        },
    )

    lines = path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["sequence_id"] == 1
    assert second["sequence_id"] == 2

    assert first["data"]["tool"] == "index_create"
    assert second["data"]["tool"] == "wait_tool"
