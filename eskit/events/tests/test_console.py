from eskit.events import Event
from eskit.events.ai_cli_listener import AIConsoleListener


def test_console_listener_shows_tool_name(capsys) -> None:
    listener = AIConsoleListener()

    event = Event.create(
        event_id=1,
        event_type="tool_call",
        data={
            "tool": "index_status",
            "arguments": {"host": "HP-DO"},
        },
    )

    listener(event)

    captured = capsys.readouterr()

    assert captured.out == "→ Using index_status\n"


def test_console_listener_verbose_shows_arguments(capsys) -> None:
    listener = AIConsoleListener(verbose=True)

    event = Event.create(
        event_id=1,
        event_type="tool_call",
        data={
            "tool": "index_status",
            "arguments": {"host": "HP-DO"},
        },
    )

    listener(event)

    captured = capsys.readouterr()

    assert "index_status" in captured.out
    assert "HP-DO" in captured.out


def test_console_listener_hides_tool_result_by_default(capsys) -> None:
    listener = AIConsoleListener()

    event = Event.create(
        event_id=1,
        event_type="tool_result",
        data={
            "tool": "index_status",
            "duration_ms": 312,
        },
    )

    listener(event)

    captured = capsys.readouterr()

    assert captured.out == ""


def test_console_listener_shows_tool_result_when_verbose(capsys) -> None:
    listener = AIConsoleListener(verbose=True)

    event = Event.create(
        event_id=1,
        event_type="tool_result",
        data={
            "tool": "index_status",
            "duration_ms": 312,
        },
    )

    listener(event)

    captured = capsys.readouterr()

    assert "index_status" in captured.out
    assert "312 ms" in captured.out
