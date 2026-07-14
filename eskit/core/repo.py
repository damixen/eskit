import logging
from eskit.utils.config import get_host_config
from eskit.utils.view import build_field_list, apply_view
from eskit.utils.input import confirm_delete
from eskit.core.host import (
    check_host_name,
    check_push_protected,
)
from eskit.cache.store import read_cache
from eskit.clients.es_client import connect_es
from eskit.result import Result, ResultCode, ResourceTarget
from eskit.resource_type import ResourceType

logger = logging.getLogger(__name__)


def get(config, host_name, name, views, fields, flat):
    """
    Public API
    """

    check_host_name(host_name)

    repo, sep, snap = name.partition("/")
    if repo and snap:
        data = get_snap(config, host_name, name, views, fields, flat)
        if not data:
            return Result.fail(ResultCode.NOT_FOUND, "Snapshot not found.")
        return Result.ok(data)
    else:
        data = get_repo(config, host_name, repo, views, fields, flat)
        if not data:
            return Result.fail(ResultCode.NOT_FOUND, "Repository not found.")
        return Result.ok(data)


def create(config, host_name, name, repo_type, location, dry_run, push):
    """
    Public API
    """

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)

    if find_repo(host_name, name):
        # logger.error("Repository:%s found in cache. Please pull latest.", name)
        return Result.fail(ResultCode.ALREADY_EXISTS, "Repository already exists.")

    body = {"type": repo_type, "settings": {"location": location, "compress": True}}
    if dry_run:
        # print_dry_run()
        # print("PUT", f"/_snapshot/{name}")
        # print(json.dumps(body, indent=2))
        return Result.ok(
            {
                "executed": False,
                "command": {"method": "PUT", "url": f"/_snapshot/{name}", "body": body},
            }
        )
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("PUT", f"/_snapshot/{name}", body)
        # print(f"Repository:{name} created. Updating Cache...")
        from eskit.core.metadata import pull_metadata

        pull_metadata(config, host_name)
    finally:
        ssh.close()

    return Result.ok()


def delete(config, host_name, name, dry_run, push, force):
    """
    Public API
    """

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)

    if not find_repo(host_name, name):
        # logger.error("Repository:%s not found in cache. Please pull latest.", name)
        return Result.fail(ResultCode.NOT_FOUND, "Repository not found.")

    if not dry_run and not force:
        if not confirm_delete("repo", name):
            return Result.fail(ResultCode.CANCELED, "Canceled.")

    if dry_run:
        # print_dry_run()
        # print("DELETE", f"/_snapshot/{name}")
        return Result.ok(
            {
                "executed": False,
                "command": {"method": "DELETE", "url": f"/_snapshot/{name}"},
            }
        )
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("DELETE", f"/_snapshot/{name}")
        # print(f"Repository:{name} deleted. updating cache...")
        from eskit.core.metadata import pull_metadata

        pull_metadata(config, host_name)
    finally:
        ssh.close()

    return Result.ok()


# Internal
def find_repo(host, repo):
    repos_cache = read_cache(host, "repos")
    if not repos_cache:
        return False

    for repo_name, repo_data in repos_cache.items():
        if repo == repo_name:
            return True

    return False


def get_repo(config, host_name, repo, views, fields, flat):

    data = read_cache(host_name, "repos")
    if not data:
        # logger.error("No repository data found.")
        return None

    out = {}

    repo_data = data.get(repo, {})
    if not repo_data:
        # logger.error("Repository:%s not found in cache.", repo)
        return None

    out = repo_data

    snapshots = read_cache(host_name, "snapshots")

    if not snapshots:
        return out

    snapshots = snapshots.get(repo, {}).get("snapshots", {})
    snap_list = []
    for s in snapshots:
        snap_list.append(s["snapshot"])

    out["snapshots"] = snap_list

    target_fields = build_field_list(config, views, fields)

    if len(target_fields) > 0:
        return apply_view(out, target_fields, flat)
    else:
        return out


def get_snap(config, host_name, path, views, fields, flat):

    target_fields = build_field_list(config, views, fields)

    repo, snap = path.split("/", 1)
    data = read_cache(host_name, "snapshots")
    if not data:
        return None
    for s in data.get(repo, {}).get("snapshots", []):
        if s.get("snapshot") == snap:
            if len(target_fields) > 0:
                return apply_view(s, target_fields, flat)
            else:
                return s
    return None
