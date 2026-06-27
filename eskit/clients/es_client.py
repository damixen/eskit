import json

from eskit.core.host import get_current_host_name, check_host_name
from eskit.utils.config import get_host_config
from eskit.transport.process import SynchronousProcess
from eskit.transport.ssh import SSHConnection
from eskit.error import ElasticsearchError, CurlError


def connect_es(host_coinfig):

    is_localhost = host_coinfig.get("localhost") or False

    transport = None

    if is_localhost:
        transport = SynchronousProcess()
    else:
        transport = SSHConnection(host_coinfig)
        transport.connect()
    elastic_config = {}
    if "elastic" in host_coinfig:
        elastic_config = host_coinfig["elastic"]
    return transport, ESClient(transport, elastic_config)


class ESClient:
    def __init__(self, transport, config):
        self.transport = transport
        self.config = config

    def request(self, method, path, body=None):
        port = 9200
        if self.config and "port" in self.config:
            port = self.config["port"]

        username = None
        password = None
        if self.config and "user" in self.config:
            username = self.config["user"].get("name")
            password = self.config["user"].get("password")
        cmd = "curl "
        cmd += "-w '\\n%{http_code}' "

        if username and password:
            cmd += f" -u {username}:{password}"

        cmd += f" -s -X {method.upper()} 'http://localhost:{port}{path}'"

        if body is not None:
            payload = json.dumps(body).replace("'", "'\"'\"'")
            cmd += f" -H 'Content-Type: application/json' -d '{payload}'"

        safe_cmd = cmd
        if password:
            safe_cmd = safe_cmd.replace(password, "******")

        print("Making Request to ES")
        print(f"transport:{self.transport.name}")
        print(f"cmd:{safe_cmd}\n")

        result = self.transport.run(cmd)
        body, status = result.rsplit("\n", 1)
        status = int(status)

        if status == 0:
            raise CurlError(f"Curl command Failed with:{cmd}")

        if body:
            body = json.loads(body)

        if status >= 400:
            raise ElasticsearchError(status, body)

        return body
