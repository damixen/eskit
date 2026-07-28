from eskit.projection import project
from eskit.resource.ilm import ILM_SCHEMA
from eskit.render.generic import render_table, render_fields, render_context
from eskit.render.display_fields import DisplayField, DisplaySchema
from eskit.render.generic import render_heading

ILM_DISPLAY = DisplaySchema(
    [
        DisplayField(
            path=("name",),
            label="Name",
        ),
        DisplayField(
            path=(
                "policy",
                "_meta",
                "managed",
            ),
            label="Managed",
            empty_value="No",
        ),
        DisplayField(
            path=("version",),
            label="Version",
        ),
        DisplayField(
            path=("modified_date",),
            label="Modified Date",
        ),
        DisplayField(
            path=("policy", "phases", "hot", "actions", "rollover", "max_age"),
            label="Rollover",
            empty_value="-",
        ),
        DisplayField(
            path=(
                "policy",
                "phases",
                "delete",
                "min_age",
            ),
            label="Retention",
            empty_value="-",
        ),
        DisplayField(
            path=(
                "in_use_by",
                "indices",
            ),
            label="Used",
            preview=True,
            preview_single="idx",
            preview_plural="idx",
            width=40,
            preview_allow_zero=True,
        ),
    ]
)

GENERAL_DISPLAY = DisplaySchema(
    [
        DisplayField(
            path=("name",),
            label="Name",
        ),
        DisplayField(
            path=(
                "policy",
                "_meta",
                "managed",
            ),
            label="Managed",
            empty_value="No",
        ),
        DisplayField(
            path=("version",),
            label="Version",
        ),
        DisplayField(
            path=("modified_date",),
            label="Modified Date",
        ),
    ]
)

LIFECYCLE_HOT_DISPLAY = DisplaySchema(
    [
        DisplayField(
            path=(
                "policy",
                "phases",
                "hot",
                "min_age",
            ),
            label="Min Age",
            empty_value="(none)",
        ),
        DisplayField(
            path=("policy", "phases", "hot", "actions", "rollover", "max_age"),
            label="Rollover Age",
            empty_value="(none)",
        ),
        DisplayField(
            path=(
                "policy",
                "phases",
                "hot",
                "actions",
                "rollover",
                "max_primary_shard_size",
            ),
            label="Rollover Size",
            empty_value="(none)",
        ),
    ]
)

LIFECYCLE_DELETE_DISPLAY = DisplaySchema(
    [
        DisplayField(
            path=(
                "policy",
                "phases",
                "delete",
                "min_age",
            ),
            label="Retention",
            empty_value="-",
        ),
    ]
)

USED_BY_INDEX_DISPLAY = DisplaySchema(
    [
        DisplayField(
            path=(
                "in_use_by",
                "indices",
            ),
            label=None,
        ),
    ]
)


def render_cat_ilm(ilms, context=None):
    render_table(project(ilms, ILM_DISPLAY.paths()), ILM_DISPLAY, ILM_SCHEMA)

    render_context(context)


def render_show_ilm(ilm, context=None):
    render_heading("ILM Policy")
    render_fields(project(ilm, GENERAL_DISPLAY.paths()), GENERAL_DISPLAY, ILM_SCHEMA)

    render_heading("Lifecycle")

    render_heading("Hot Phase:", skip_underline=True, skip_newline=True)
    render_fields(
        project(ilm, LIFECYCLE_HOT_DISPLAY.paths()), LIFECYCLE_HOT_DISPLAY, ILM_SCHEMA
    )

    render_heading("Cold Phase:", skip_underline=True)
    render_fields(
        project(ilm, LIFECYCLE_DELETE_DISPLAY.paths()),
        LIFECYCLE_DELETE_DISPLAY,
        ILM_SCHEMA,
    )

    render_heading("Used By")
    render_heading(
        f"Index: count({len(ilm["in_use_by"]["indices"])})", skip_underline=True
    )
    render_fields(
        project(ilm, USED_BY_INDEX_DISPLAY.paths()), USED_BY_INDEX_DISPLAY, ILM_SCHEMA
    )

    render_context(context)
