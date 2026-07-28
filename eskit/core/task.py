from eskit.utils.config import get_host_config
from eskit.core.host import check_host_name
from eskit.clients.es_client import connect_es
from eskit.result import Result, ResultCode, DataSource

HTTP_METHOD_GET = "GET"


def get(config, host_name, task_id):

    check_host_name(host_name)

    url = f"/_tasks/{task_id}"

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        return Result.ok(res, context={"sources":[DataSource.ELASTICSEARCH]})
    except Exception as e:
        print(e)
    finally:
        ssh.close()

    return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to get task.")
