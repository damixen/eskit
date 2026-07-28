from datetime import datetime
from eskit.core.host import check_host_name
from eskit.jobs.job_manager import get as get_jbm
from eskit.result import Result, ResultCode, DataSource


def get_list(host_name, local):

    check_host_name(host_name)

    jbm = get_jbm()
    assert jbm is not None
    data = jbm.list_dicts(host_name, local)
    data.sort(key=lambda x: datetime.fromisoformat(x["updated_at"]), reverse=True)
    return Result.ok(data, context={"sources": [DataSource.CACHE]})


def get(host_name, job_search_id):

    check_host_name(host_name)

    jbm = get_jbm()
    assert jbm is not None
    data = jbm.load_dict(host_name, job_search_id)

    if not data:
        return Result.fail(ResultCode.NOT_FOUND, "Job not found.")

    return Result.ok(data, context={"sources": [DataSource.CACHE]})
