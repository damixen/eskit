from eskit.projection import project
from eskit.resource.job import JOB_SCHEMA
from eskit.render.generic import render_table, render_fields, render_heading
from eskit.render.display_fields import DisplayField, DisplaySchema

JOB_DISPLAY = DisplaySchema(
    [
        DisplayField(("id",)),
        DisplayField(("name",)),
        DisplayField(("type",)),
        DisplayField(("host",)),
        DisplayField(("status",)),
        DisplayField(("created_at",)),
    ]
)

GENERAL_SCHEMA = DisplaySchema(
    [
        DisplayField(("id",)),
        DisplayField(("name",)),
        DisplayField(("type",)),
        DisplayField(("host",)),
    ]
)

EXECUTION_SCHEMA = DisplaySchema(
    [
        DisplayField(("status",)),
        DisplayField(("created_at",)),
        DisplayField(("updated_at",)),
    ]
)

PAYLOAD_SCHEMA = DisplaySchema(
    [
        DisplayField(
            (
                "payload",
                "src",
            )
        ),
        DisplayField(
            (
                "payload",
                "dst",
            )
        ),
    ]
)

RESULT_SCHEMA = DisplaySchema(
    [
        DisplayField(
            (
                "result",
                "task_id",
            )
        ),
        DisplayField(("pid",)),
        DisplayField(("log_path",)),
        DisplayField(("cache_path",)),
        DisplayField(("preview",)),
    ]
)


def render_list_jobs(jobs):

    render_table(project(jobs, JOB_DISPLAY.paths()), JOB_DISPLAY, JOB_SCHEMA)


def render_show_job(job):
    render_heading("General")
    render_fields(project(job, GENERAL_SCHEMA.paths()), GENERAL_SCHEMA, JOB_SCHEMA)

    render_heading("Execution")
    render_fields(project(job, EXECUTION_SCHEMA.paths()), EXECUTION_SCHEMA, JOB_SCHEMA)

    render_heading("Payload")
    render_fields(project(job, PAYLOAD_SCHEMA.paths()), PAYLOAD_SCHEMA, JOB_SCHEMA)

    render_heading("Result")
    render_fields(project(job, RESULT_SCHEMA.paths()), RESULT_SCHEMA, JOB_SCHEMA)
