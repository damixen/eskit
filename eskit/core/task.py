import json
from eskit.utils.config import load_config, get_host_config
from eskit.core.host import get_current_host_name, check_host_name, print_host
from eskit.clients.es_client import connect_es

HTTP_METHOD_GET = "GET"


def get(config_path, host_name, task_id):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    print_host(host_name)

    url = f"/_tasks/{task_id}"

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(e)
    finally:
        ssh.close()
