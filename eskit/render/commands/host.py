#from eskit.render.projection import normalize_projection, project
from eskit.render.generic import render_fields, render_heading, render_table, render_context
from eskit.render.display_fields import DisplayField, DisplaySchema
from eskit.projection import project
from eskit.resource.host import HOST_SCHEMA, SSH_SCHEMA, ELASTIC_SCHEMA
from eskit.resource.archive import ARCHIVE_SCHEMA

GENERAL_DISPLAY = DisplaySchema(
    [
        DisplayField(("name",)),
        DisplayField(("ip",), label="IP"),
    ])

SSH_DISPLAY = DisplaySchema(
    [
        DisplayField(("user",), label="User"),
        DisplayField(("port",), label="Port"),
        DisplayField(("use_sshpass",), label="Use sshpass"),

    ])

ELASTIC_DISPLAY = DisplaySchema(
    [
        DisplayField(("user", "name"), label="User"),
        DisplayField(("port",), label="Port"),
    ])

ARCHIVES_DISPLAY = DisplaySchema(
    [
        DisplayField(("name",), label="Name"),
        DisplayField(("type",), label="Type"),
        DisplayField(("remote_src",), label="Type"),
        DisplayField(("local_dst",), label="Type"),

    ])

def render_host_show(host: dict, context = None):
    render_heading("Host Configuration")

    #
    # General
    #

    render_heading("General")
    render_fields(
        project(host, GENERAL_DISPLAY.paths()),
        GENERAL_DISPLAY,
        HOST_SCHEMA
    )

    #
    # SSH
    #

    render_heading("SSH")
    render_fields(
        project(host["ssh"], SSH_DISPLAY.paths()),
            SSH_DISPLAY,
            SSH_SCHEMA
    )

    #
    # Elasticsearch
    #

    render_heading("Elastic")
    render_fields(
        project(host["elastic"], ELASTIC_DISPLAY.paths()),
            ELASTIC_DISPLAY,
            ELASTIC_SCHEMA
    )
    

    #
    # Archives
    #

    render_heading("Archives")
    render_table(
        project(host["archives"], ARCHIVES_DISPLAY.paths()),
        ARCHIVES_DISPLAY,
        ARCHIVE_SCHEMA
    )

    render_context(context)
