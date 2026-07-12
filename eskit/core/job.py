#!/usr/bin/env python3
from datetime import datetime
from eskit.utils.config import load_config
from eskit.utils.view import build_field_list, apply_view
from eskit.core.host import get_current_host_name, check_host_name
from eskit.jobs.job_manager import get as get_jbm
from eskit.result import Result, ResultCode
from eskit.resource_type import ResourceType


def get_list(config_path, host_name, local, views, fields, flat):

    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)

    config = load_config(config_path)

    data = get_jbm().list_dicts(host_name, local)
    data.sort(key=lambda x: datetime.fromisoformat(x["updated_at"]), reverse=True)

    target_fields = build_field_list(config, views, fields)
    out = []

    if len(target_fields) > 0:
        for job in data:
            out.append(apply_view(job, target_fields, flat))
    else:
        out = data

    # print(json.dumps(out, indent=2))

    return Result.ok(out)


def get(config_path, host_name, job_search_id, views, fields, flat):

    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)

    config = load_config(config_path)

    target_fields = build_field_list(config, views, fields)
    out = {}

    data = get_jbm().load_dict(host_name, job_search_id)

    if not data:
        return Result.fail(
            ResultCode.NOT_FOUND,
            "Job not found.",
            {"resource": ResourceType.JOB, "name": job_search_id},
        )

    if len(target_fields) > 0:
        out = apply_view(data, target_fields, flat)
    else:
        out = data

    # print(json.dumps(out, indent=2))

    return Result.ok(out)
