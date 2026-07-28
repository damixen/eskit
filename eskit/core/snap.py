import logging
from eskit.utils.config import get_host_config
from eskit.core.host import get_current_host_name, check_host_name, check_push_protected
from eskit.cache.store import read_cache
from eskit.clients.es_client import connect_es
from eskit.utils.input import confirm_delete
from eskit.result import Result, ResultCode, Argument

logger = logging.getLogger(__name__)


def create(
    config,
    host_name,
    spec,
    indices,
    include_global_state,
    ignore_unavailable,
    dry_run,
    push,
    wait,
):
    """
    Public API
    """

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)

    repo, delim, snap = spec.partition("/")
    if not repo or not snap:
        # logger.error("Snapshot:%s is not in valid format. <repo>/<snapshot>", spec)
        return Result.fail(
            ResultCode.INVALID_ARGUMENT,
            "Invalid resource name.",
            context=Argument(name="spec", value=spec),
        )

    if find_snapshot(host_name, repo, snap):
        # logger.error("Snapshot:%s found in cache. Please pull latest.", spec)
        return Result.fail(ResultCode.ALREADY_EXISTS, "Resource already exists.")

    body = {}
    if indices:
        body["indices"] = indices
    body["include_global_state"] = include_global_state
    body["ignore_unavailable"] = ignore_unavailable

    url = f"/_snapshot/{repo}/{snap}"

    if wait:
        url = url + "?wait_for_completion=true"

    if dry_run:
        # print_dry_run()
        # print("PUT", f"/_snapshot/{repo}/{snap}")
        # print(json.dumps(body, indent=2))
        return Result.ok(
            {
                "executed": False,
                "command": {
                    "method": "PUT",
                    "url": url,
                    "body": body,
                },
            }
        )

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("PUT", url, body)
        from eskit.core.metadata import pull_metadata

        pull_metadata(config, host_name)
    finally:
        ssh.close()

    return Result.ok()


def delete(config, host_name, spec, dry_run, push, force):
    """
    Public API
    """

    repo, delim, snap = spec.partition("/")
    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)

    if not find_snapshot(host_name, repo, snap):
        # logger.error("Snapshot:%s not found in cache. Please pull the latest.", spec)
        return Result.fail(ResultCode.NOT_FOUND, "Resource not found.")

    if not dry_run and not force:
        if not confirm_delete("snapshot", spec):
            # print("Cancelled.")
            return Result.fail(ResultCode.CANCELED, "Canceled.")

    if dry_run:
        # print_dry_run()
        # print("DELETE", f"/_snapshot/{repo}/{snap}")
        return Result.ok(
            {
                "executed": False,
                "command": {"method": "DELETE", "url": f"/_snapshot/{repo}/{snap}"},
            }
        )
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("DELETE", f"/_snapshot/{repo}/{snap}")
        # print(f"Snapshot:{spec} deleted. Updating Cache.")
        from eskit.core.metadata import pull_metadata

        pull_metadata(config, host_name)
    finally:
        ssh.close()

    return Result.ok()


def restore(config, host_name, spec, index, dry_run, push, ilm, remove_ilm, wait):
    """
    Public API
    """

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)

    body = {}

    repo, delim, snap = spec.partition("/")

    if index:
        body["indices"] = index
    else:
        body["indices"] = "*"
    body["include_global_state"] = False

    if ilm or remove_ilm:
        ilm_name = ilm
        if remove_ilm:
            ilm_name = None
        body["index_settings"] = {
            "index.lifecycle.name": ilm_name,
            "index.lifecycle.rollover_alias": None,
        }

    url = f"/_snapshot/{repo}/{snap}/_restore"

    if wait:
        url = url + "?wait_for_completion=true"

    if dry_run:
        # print_dry_run()
        # print("POST", f"/_snapshot/{repo}/{snap}/_restore")
        # print(json.dumps(body, indent=2))
        return Result.ok(
            {
                "executed": False,
                "command": {
                    "method": "POST",
                    "url": url,
                },
            }
        )
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("POST", url, body)
        # print(f"Snapshot:{spec} restore requested. Updating Cache...")
        from eskit.core.metadata import pull_metadata

        pull_metadata(config, host_name)
    finally:
        ssh.close()

    return Result.ok()


# Internal
def find_snapshot(host, repo, snapshot):
    snapshots_cache = read_cache(host, "snapshots")
    if not snapshots_cache:
        return False
    if not repo in snapshots_cache:
        return False
    snap_list = snapshots_cache[repo]["snapshots"]
    for s in snap_list:
        if snapshot == s["snapshot"]:
            return True

    return False
