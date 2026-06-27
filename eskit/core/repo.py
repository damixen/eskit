import json
from eskit.utils.config import load_config, get_host_config
from eskit.utils.view import build_field_list, apply_view
from eskit.utils.input import confirm_delete
from eskit.core.host import (
    get_current_host_name,
    check_host_name,
    print_host,
    check_push_protected,
    print_dry_run,
)
from eskit.cache.store import read_cache
from eskit.clients.es_client import connect_es


def show(config_path, host_name, name, views, fields, flat):

    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)

    repo, sep, snap = name.partition("/")
    if repo and snap:
        show_snap(config, host_name, name, views, fields, flat)
    else:
        show_repo(config, host_name, repo, views, fields, flat)


def create(config_path, host_name, name, repo_type, location, dry_run, push):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)

    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    if find_repo(host_name, name):
        print(f"Repository:{name} found in cache. Please pull latest.")
        return

    body = {"type": repo_type, "settings": {"location": location, "compress": True}}
    if dry_run:
        print_dry_run()
        print("PUT", f"/_snapshot/{name}")
        print(json.dumps(body, indent=2))
        return
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("PUT", f"/_snapshot/{name}", body)
        print(f"Repository:{name} created. Updating Cache...")
        from eskit.core.metadata import pull

        pull(config_path, host_name)
    finally:
        ssh.close()


def delete(config_path, host_name, name, dry_run, push, force):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    if not find_repo(host_name, name):
        print(f"Repository:{name} not found in cache. Please pull latest.")
        return

    if not dry_run and not force:
        if not confirm_delete("repo", name):
            print("Cancelled.")
            return

    if dry_run:
        print_dry_run()
        print("DELETE", f"/_snapshot/{name}")
        return
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        es.request("DELETE", f"/_snapshot/{name}")
        print(f"Repository:{name} deleted. updating cache...")
        from eskit.core.metadata import pull

        pull(config_path, host_name)
    finally:
        ssh.close()


# Internal
def find_repo(host, repo):
    repos_cache = read_cache(host, "repos")
    for repo_name, repo_data in repos_cache.items():
        if repo == repo_name:
            return True

    return False


def show_repo(config, host_name, repo, views, fields, flat):

    data = read_cache(host_name, "repos")
    if not data:
        return

    out = {}

    repo_data = data.get(repo, {})
    if not repo_data:
        print_host(host_name)
        print(f"Repository:{repo} not found in cache.")
        return

    out = repo_data

    snapshots = read_cache(host_name, "snapshots")

    if not snapshots:
        print(json.dumps(data.get(repo, {}), indent=2))
        return
    snapshots = snapshots.get(repo, {}).get("snapshots", {})
    snap_list = []
    for s in snapshots:
        snap_list.append(s["snapshot"])

    out["snapshots"] = snap_list

    target_fields = build_field_list(config, views, fields)

    if len(target_fields) > 0:
        print(json.dumps(apply_view(out, target_fields, flat), indent=2))
    else:
        print(json.dumps(out, indent=2))


def show_snap(config, host_name, path, views, fields, flat):

    target_fields = build_field_list(config, views, fields)

    repo, snap = path.split("/", 1)
    data = read_cache(host_name, "snapshots")
    if not data:
        return
    for s in data.get(repo, {}).get("snapshots", []):
        if s.get("snapshot") == snap:
            if len(target_fields) > 0:
                print(json.dumps(apply_view(s, target_fields, flat), indent=2))
            else:
                print(json.dumps(s, indent=2))
            return
    print("Snapshot not found.")
