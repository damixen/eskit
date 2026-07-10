import json
import logging
from eskit.utils.config import load_config, get_host_config
from eskit.core.host import (
    get_current_host_name,
    check_host_name,
    check_push_protected,
    print_host,
    print_dry_run,
)
from eskit.cache.store import read_cache
from eskit.clients.es_client import connect_es
from eskit.utils.input import confirm_delete
from eskit.exit_code import ExitCode

logger = logging.getLogger(__name__)

def create(
    config_path,
    host_name,
    spec,
    indices,
    include_global_state,
    ignore_unavailable,
    dry_run,
    push,
):

    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    repo, delim, snap = spec.partition("/")
    if not repo or not snap:
        logger.error("Snapshot:%s is not in valid format. <repo>/<snapshot>", spec)
        return ExitCode.FAILURE

    if find_snapshot(host_name, repo, snap):
        logger.error("Snapshot:%s found in cache. Please pull latest.", spec)
        return ExitCode.FAILURE

    body = {}
    if indices:
        body["indices"] = indices
    body["include_global_state"] = include_global_state
    body["ignore_unavailable"] = ignore_unavailable
    if dry_run:
        print_dry_run()
        print("PUT", f"/_snapshot/{repo}/{snap}")
        print(json.dumps(body, indent=2))
        return ExitCode.SUCCESS

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("PUT", f"/_snapshot/{repo}/{snap}", body)
        from eskit.core.metadata import pull

        pull(config_path, host_name)
    finally:
        ssh.close()

    return ExitCode.SUCCESS


def delete(config_path, host_name, spec, dry_run, push, force):
    config = load_config(config_path)
    repo, delim, snap = spec.partition("/")
    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    if not find_snapshot(host_name, repo, snap):
        logger.error("Snapshot:%s not found in cache. Please pull the latest.", spec)
        return ExitCode.FAILURE

    if not dry_run and not force:
        if not confirm_delete("snapshot", spec):
            print("Cancelled.")
            return ExitCode.CANCELED

    if dry_run:
        print_dry_run()
        print("DELETE", f"/_snapshot/{repo}/{snap}")
        return ExitCode.SUCCESS
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("DELETE", f"/_snapshot/{repo}/{snap}")
        print(f"Snapshot:{spec} deleted. Updating Cache.")
        from eskit.core.metadata import pull

        pull(config_path, host_name)
    finally:
        ssh.close()

    return ExitCode.SUCCESS


def restore(config_path, host_name, spec, index, dry_run, push):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    body = {}

    repo, delim, snap = spec.partition("/")

    if index:
        body["indices"] = index
    else:
        body["indices"] = "*"
    body["include_global_state"] = False

    if dry_run:
        print_dry_run()
        print("POST", f"/_snapshot/{repo}/{snap}/_restore")
        print(json.dumps(body, indent=2))
        return ExitCode.SUCCESS
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("POST", f"/_snapshot/{repo}/{snap}/_restore", body)
        print(f"Snapshot:{spec} restore requested. Updating Cache...")
        from eskit.core.metadata import pull

        pull(config_path, host_name)
    finally:
        ssh.close()

    return ExitCode.SUCCESS


# Internal
def find_snapshot(host, repo, snapshot):
    snapshots_cache = read_cache(host, "snapshots")
    if not repo in snapshots_cache:
        return False
    snap_list = snapshots_cache[repo]["snapshots"]
    for s in snap_list:
        if snapshot == s["snapshot"]:
            return True

    return False
