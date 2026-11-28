import pytest

from types import SimpleNamespace

from eskit.ai.tool import ToolCall
from eskit.result import Result, ResultCode
from eskit.cli import (
    resolve_projection_key,
    project_tool_result,
    resolve_tool_call_projections,
)


@pytest.mark.parametrize(
    "name, arguments, expected",
    [
        ("cat", {"kind": "index"}, "cat-index"),
        ("cat", {"kind": "repo"}, "cat-repo"),
        ("cat", {"kind": "snap"}, "cat-snap"),
        ("index_show", {}, "index-show"),
        ("index_status", {}, "index-status"),
        ("repo_show", {}, "repo-show"),
        ("status", {}, "status"),
    ],
)
def test_resolve_projection_key(name, arguments, expected):
    tool_call = ToolCall(
        id="abc",
        name=name,
        arguments=arguments,
    )

    assert resolve_projection_key(tool_call) == expected


def test_project_tool_result_cat_index():
    tool_call = ToolCall(
        id="abc",
        name="cat",
        arguments={"kind": "index"},
    )

    original_value = [
        {
            "index": "test-index-1",
            "docs.count": "100",
            "store.size": "1gb",
            "health": "green",
        },
        {
            "index": "test-index-2",
            "docs.count": "200",
            "store.size": "2gb",
            "health": "yellow",
        },
    ]

    result = Result(
        code=ResultCode.SUCCESS,
        message="",
        value=original_value,
    )

    options = {
        "tool_call_projections": {
            "cat-index": [
                ("index",),
                ("docs.count",),
            ],
        },
    }

    projected = project_tool_result(
        tool_call,
        result,
        options,
    )

    assert projected.value == [
        {
            "index": "test-index-1",
            "docs.count": "100",
        },
        {
            "index": "test-index-2",
            "docs.count": "200",
        },
    ]

    assert projected.code == result.code
    assert projected.message == result.message
    assert projected.success == result.success

    # Projection must not modify the original result.
    assert projected is not result

    assert result.value == [
        {
            "index": "test-index-1",
            "docs.count": "100",
            "store.size": "1gb",
            "health": "green",
        },
        {
            "index": "test-index-2",
            "docs.count": "200",
            "store.size": "2gb",
            "health": "yellow",
        },
    ]