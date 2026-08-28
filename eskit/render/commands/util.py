
import json
from eskit.render.generic import render_dry_run, render_host
from eskit.render.commands.job import render_show_job

def render_command_execution(result, context, msg):

    dry_run = False
    host = ""
    job = None
    if result:
        dry_run = result.get("mode", "") == "dry_run"
        host = result.get("host", "")
        job = result.get("job", None) 

    if job:
        render_show_job(job, context)
        return

    if not dry_run:
        print(msg)
    else:
        render_dry_run()
        render_host(host)
        print(json.dumps(result, indent=2))
