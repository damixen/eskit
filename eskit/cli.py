#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import paramiko
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import uuid
import time
import shutil
from eskit.jobs.job import ESKitJob
from eskit.archive.model import ESKitArchive, ESKitArchiveState
from eskit.jobs.executers import RsyncExecutor, LocalExecutor, ElasticsearchExecutor
from eskit.jobs.job_manager import ESKitJobManager
from eskit.transport.process import SynchronousProcess
from eskit.transport.ssh import SSHConnection
from eskit.clients.es_client import ESClient
from eskit.core.host import get_current_host_name

from .paths import DEMO_DIR
from .error import ConfigError

job_manager = None


__version__ = "0.1.0"
__cache_version__ = "v1"

DEFAULT_CONFIG = ".eskit/config.json"
CACHE_ROOT = Path(".eskit")
HTTP_METHOD_DELETE = "DELETE"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_POST = "POST"
HTTP_METHOD_GET = "GET"
CURRENT_HOST = ".current_host"


def print_host(host):
    print(f"\n=== ESKit HOST: {host} ===\n")


def print_dry_run():
    print("\n*Dry Run*\n")


def print_preview():
    print("\n*Preview*\n")


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_host(config, name):
    for h in config.get("hosts", []):
        if h["name"] == name:
            return h
    raise SystemExit(f"Host not found: {name}")


def get_rsync_config(config, name):
    for h in config.get("rsync-configs", []):
        if h["name"] == name:
            return h
    raise SystemExit(f"Host not found: {name}")


def check_host(host):
    if host is None:
        raise SystemExit(
            "Host not found. Please specify the host or set the host by the host set command."
        )
    return


def check_push_protected(config, host, dry_run, push):
    host_config = get_host(config, host)
    if (
        "push-protected" in host_config
        and host_config["push-protected"]
        and not dry_run
        and not push
    ):
        print_host(host)
        raise SystemExit(
            f"Host:{host} is push protected. Please use --push to make a change or --dry-run to check command."
        )
    return


def is_push_protected(config, host):
    host_config = get_host(config, host)
    return "push-protected" in host_config and host_config["push-protected"]


def confirm_delete(kind, name):
    print(f"About to delete {kind}: {name}\n")
    x = input("Confirm delete by typing:")
    print("\n")
    return x == name


def get_current_host():
    if not (CACHE_ROOT / CURRENT_HOST).exists():
        return

    with open(CACHE_ROOT / CURRENT_HOST, "r", encoding="utf-8") as f:
        for line in f:
            return line


def cache_dir(host):
    return CACHE_ROOT / host / "cache"


def root_dir():
    return CACHE_ROOT


def cache_age(path):
    if not path.exists():
        return None
    age_sec = time.time() - path.stat().st_mtime
    return age_sec


def cache_date(path):
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).strftime(
        "%A, %B %d, %Y at %I:%M %p"
    )


def job_dir(host):
    return CACHE_ROOT / host / "cache" / "jobs"


def archive_dir(host):
    return CACHE_ROOT / host / "cache" / "arvhices"


def ensure_root():
    CACHE_ROOT.mkdir(parents=True, exist_ok=True)


def ensure_cache(host):
    cache_dir(host).mkdir(parents=True, exist_ok=True)


def ensure_job_dir(host):
    job_dir(host).mkdir(parents=True, exist_ok=True)


def ensure_archive_dir(host):
    archive_dir(host).mkdir(parents=True, exist_ok=True)


def ensure_host(host):
    if host is None:
        host = get_current_host()

    check_host(host)
    return host


def write_cache(host, name, data):
    ensure_cache(host)
    with open(cache_dir(host) / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def read_cache(host, name):
    p = cache_dir(host) / f"{name}.json"
    if not p.exists():
        print(f"Cached:{name} information not found. Run: eskit pull {host}")
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write_job(host, job: ESKitJob):
    ensure_job_dir(host)
    with open(job_dir(host) / f"{job.get_output_id()}.json", "w") as f:
        json.dump(asdict(job), f, indent=2)


def write_archive_all(config, host):
    host_config = get_host(config, host)
    archives = host_config.get("archives")

    if not archives:
        return

    for archive in archives:
        pull_archive_stat(config, host, archive)

    # clean stale cache
    cached_archives = list_archives(host)

    for cache in cached_archives:
        exists = any(d.get("name") == cache["name"] for d in archives)
        if not exists:
            delete_archive(host, ESKitArchiveState.from_dict(cache))


def delete_archive(host, archive: ESKitArchiveState):
    ensure_archive_dir(host)
    Path(archive_dir(host) / f"{archive.name}.json").unlink(missing_ok=True)


def write_archive(host, archive: ESKitArchiveState):
    ensure_archive_dir(host)
    with open(archive_dir(host) / f"{archive.name}.json", "w") as f:
        json.dump(asdict(archive), f, indent=2)


def read_archive(host, archive_id):
    path = archive_dir(host) / f"{archive_id}.json"
    if not path.exists():
        return None
    return json.load(open(path))


def list_archives(host):
    if not archive_dir(host).exists():
        return []

    archives = []
    for f in archive_dir(host).glob("*.json"):
        archives.append(json.load(open(f)))

    archives.sort(key=lambda x: x["created_at"], reverse=True)
    return archives


def is_agent_available():
    try:
        agent = paramiko.Agent()
        return len(agent.get_keys()) > 0
    except Exception:
        return False


def find_index(host, index):
    index_cache = read_cache(host, "indices")
    if not index_cache:
        return False

    for i in index_cache:
        if index == i["index"]:
            return True

    return False


def find_repo(host, repo):
    repos_cache = read_cache(host, "repos")
    for repo_name, repo_data in repos_cache.items():
        if repo == repo_name:
            return True

    return False


def find_snapshot(host, repo, snapshot):
    snapshots_cache = read_cache(host, "snapshots")
    if not repo in snapshots_cache:
        return False
    snap_list = snapshots_cache[repo]["snapshots"]
    for s in snap_list:
        if snapshot == s["snapshot"]:
            return True

    return False


def get_reindex_mapping(config, host, name):
    reindex_configs = config.get("reindex-configs")
    if not reindex_configs:
        return None
    for c in reindex_configs:
        if c["name"] == name:
            return c["mappings"]
    return None


def get_path(data, path):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        part = part.replace("$", ".")
        if part not in current:
            return None
        current = current[part]
    return current


def set_path(data, path, value):
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        part = part.replace("$", ".")
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1].replace("$", ".")] = value


def apply_view(data, fields, flat):
    out = {}

    for field in fields:
        value = get_path(data, field)
        if flat:
            out[field] = value
        elif value is not None:
            set_path(out, field, value)

    return out


def get_view(config, views):
    views_config = config.get("views", {})
    out = []
    for name in views:
        if name not in views_config:
            raise ConfigError(f"view not found: {name}")
        out.extend(views_config[name])
    return out


def build_field_list(config, views, fields):
    result = []

    for view in views:
        result.extend(config["views"].get(view, []))

    if fields:
        result.extend(fields.split(","))

    return list(dict.fromkeys(result))


def build_projection(data, field_paths):
    out = {}

    for path in field_paths:
        value = get_path(data, path)

        if value is not None:
            out[path] = value

    return out


def pull_host(config, host_name, es, kind=None):

    print(f"kind:{kind}")

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)
    print_host(host_name)

    all = len(kind) == 0 or kind == None

    if "es" in kind or all:
        repos = es.request("GET", "/_snapshot")
        write_cache(host_name, "repos", repos)

        snapshots = {}
        if isinstance(repos, dict):
            for repo in repos.keys():
                snapshots[repo] = es.request("GET", f"/_snapshot/{repo}/_all")
        write_cache(host_name, "snapshots", snapshots)

        indices = es.request("GET", "/_cat/indices?format=json")
        write_cache(host_name, "indices", indices)

        version = es.request("GET", "/")
        write_cache(host_name, "version", version)

    # pull archive status
    if "archive" in kind or all:
        write_archive_all(config, host_name)

    print("\nCache updated.\n")


def connect_es(config, host_name):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    host_cfg = get_host(config, host_name)

    is_localhost = host_cfg.get("localhost") or False

    transport = None

    if is_localhost:
        transport = SynchronousProcess()
    else:
        transport = SSHConnection(host_cfg)
        transport.connect()
    elastic_config = {}
    if "elastic" in host_cfg:
        elastic_config = host_cfg["elastic"]
    return transport, ESClient(transport, elastic_config)


def cmd_host(args):
    from eskit.core.host import get_hosts

    hosts = get_hosts(args.host, args.config)
    print(json.dumps(hosts, indent=2))


def cmd_host_set(args):
    from eskit.core.host import set_current_host_name

    set_current_host_name(args.host)


def cmd_host_get(args):
    print(get_current_host_name())


def cmd_list_job(args):
    host_name = args.host
    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    config = None
    if "config" in args:
        config = load_config(args.config)

    local = args.local

    data = job_manager.list_dicts(host_name, local)
    data.sort(key=lambda x: datetime.fromisoformat(x["updated_at"]), reverse=True)

    views = args.view
    fields = args.fields
    flat = args.flat
    target_fields = build_field_list(config, views, fields)
    out = []

    if len(target_fields) > 0:
        for job in data:
            out.append(apply_view(job, target_fields, flat))
    else:
        out = data

    print(json.dumps(out, indent=2))


def cmd_read_job(args):

    host_name = args.host
    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    config = None
    if "config" in args:
        config = load_config(args.config)

    views = args.view
    fields = args.fields
    flat = args.flat
    job_search_id = args.job_search_id
    target_fields = build_field_list(config, views, fields)
    out = {}

    data = job_manager.load_dict(host_name, job_search_id)

    if len(target_fields) > 0:
        out = apply_view(data, target_fields, flat)
    else:
        out = data

    print(json.dumps(out, indent=2))

    return


def cmd_status(args):

    from eskit.core.status import get_status

    status = get_status(args.host, args.config)

    print(json.dumps(status, indent=2))


def cmd_pull(args):
    from eskit.core.metadata import pull
    pull(args.config, args.host, args.kind)
    


def cmd_cat2(args):

    # config, kind, host_name, views, fields, flat
    config = None
    if "config" in args:
        config = load_config(args.config)

    mapping = {"repo": "repos", "snap": "snapshots", "index": "indices"}
    kind = mapping[args.kind]
    views = args.view
    fields = args.fields
    flat = args.flat

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    target_fields = build_field_list(config, views, fields)
    data = read_cache(host_name, kind)

    if not data:
        return

    out = {}
    if kind == "snapshots":
        for repo, repo_data in data.items():
            snapshots = repo_data.get("snapshots", {})
            snap_list = []
            for s in snapshots:
                if len(target_fields) > 0:
                    snap_list.append(apply_view(s, target_fields, flat))
                else:
                    snap_list.append(s)
            out = snap_list
    elif kind == "repos":
        out = {}
        for repo, repo_data in data.items():
            out_repo = repo_data
            if len(target_fields) > 0:
                out_repo = apply_view(repo_data, target_fields, flat)

            out[repo] = out_repo
    elif kind == "indices":
        out = data
        if len(target_fields) > 0:
            # add index by default
            if "index" not in target_fields:
                target_fields.insert(0, "index")
            out = []
            for i in data:
                out.append(apply_view(i, target_fields, flat))
        out.sort(key=lambda x: x["index"])
    elif kind == "recovery":
        out = data

    print(json.dumps(out, indent=2))


def cmd_cat(kind, host_name):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    data = read_cache(host_name, kind)
    if data is not None:
        print(json.dumps(data, indent=2))


def cmd_repo_show2(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    views = args.view
    fields = args.fields
    flat = args.flat

    repo, sep, snap = name.partition("/")
    if repo and snap:
        cmd_snap_show(config, host_name, name, views, fields, flat)
    else:
        cmd_repo_show(config, host_name, repo, views, fields, flat)


def cmd_delete_repo(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    dry_run = args.dry_run
    push = args.push
    force = args.force

    delete_repo(config, host_name, name, dry_run, push, force)


def cmd_create_repo(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    dry_run = args.dry_run
    push = args.push
    repo_type = args.type
    location = args.location

    create_repo(config, host_name, name, repo_type, location, dry_run, push)


def cmd_repo_show(config, host_name, repo, views, fields, flat):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

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


def cmd_snap_show(config, host_name, spec, views, fields, flat):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    target_fields = build_field_list(config, views, fields)

    repo, snap = spec.split("/", 1)
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


def cmd_reindex_mapping(args):
    config = None
    if "config" in args:
        config = load_config(args.config)
    print(json.dumps(config["reindex-configs"], indent=2))


def cmd_create_snapshot(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    indices = args.index
    dry_run = args.dry_run
    push = args.push
    include_global_state = args.include_global_state
    ignore_unavailable = args.ignore_unavailable

    create_snapshot(
        config,
        host_name,
        name,
        indices,
        include_global_state,
        ignore_unavailable,
        dry_run,
        push,
    )


def cmd_delete_snapshot(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    dry_run = args.dry_run
    push = args.push
    force = args.force

    delete_snapshot(config, host_name, name, dry_run, push, force)


def cmd_restore_snapshot(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    dry_run = args.dry_run
    push = args.push
    index = args.index

    restore_snapshot(config, host_name, name, index, dry_run, push)


def cmd_restore_status(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    index = args.index

    show_recovery(config, host_name, index, args.view, args.fields, args.flat)


def cmd_delete_index(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    index = args.index
    dry_run = args.dry_run
    push = args.push
    force = args.force

    delete_index(config, host_name, index, dry_run, push, force)


def cmd_create_index(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    index = args.index
    mapping = args.mapping
    dry_run = args.dry_run
    push = args.push

    create_index(config, host_name, index, mapping, dry_run, push)


def cmd_show_index(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    index = args.index
    views = args.view
    fields = args.fields
    flat = args.flat

    show_index(config, host_name, index, views, fields, flat)


def cmd_reindex(args):

    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    src = args.src
    dst = args.dst
    mapping = args.mapping
    dry_run = args.dry_run
    push = args.push

    reindex(config, host_name, src, dst, mapping, dry_run, push)


def cmd_get_task(args):
    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host
    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    task_id = args.task_id
    get_task(config, host_name, task_id)


def cmd_init(args):
    from eskit.core.init import init

    init(args.demo)


def cmd_list_archive(args):

    host_name = args.host
    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    config = None
    if "config" in args:
        config = load_config(args.config)

    data = list_archives(host_name)

    views = args.view
    fields = args.fields
    flat = args.flat
    target_fields = build_field_list(config, views, fields)
    out = []

    if len(target_fields) > 0:
        for job in data:
            out.append(apply_view(job, target_fields, flat))
    else:
        out = data

    print(json.dumps(out, indent=2))


def cmd_pull_archive(args):
    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    pull_archive(
        config,
        host_name,
        args.name,
        args.contents,
        args.dry_run,
        False,
        False,
        args.preview,
    )


def cmd_sync_archive(args):
    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    pull_archive(
        config,
        host_name,
        args.name,
        args.contents,
        args.dry_run,
        False,
        True,
        args.preview,
    )


def cmd_push_archive(args):
    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    push_archive(
        config,
        host_name,
        args.name,
        args.dst,
        args.contents,
        args.dry_run,
        args.preview,
    )


def cmd_show_archive(args):
    host_name = args.host
    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    config = None
    if "config" in args:
        config = load_config(args.config)

    views = args.view
    fields = args.fields
    flat = args.flat
    archive_name = args.name
    target_fields = build_field_list(config, views, fields)
    out = {}

    data = read_archive(host_name, archive_name)

    if len(target_fields) > 0:
        out = apply_view(data, target_fields, flat)
    else:
        out = data

    print(json.dumps(out, indent=2))


def show_recovery(config, host, index, views, fields, flat):
    if host is None:
        host = get_current_host()

    check_host(host)

    target_fields = build_field_list(config, views, fields)

    ssh, es = connect_es(config, host)
    try:
        out = []
        data = es.request("GET", f"/_cat/recovery/{index}?format=json")
        for r in data:
            if len(target_fields) > 0:
                out.append(apply_view(r, target_fields, flat))
            else:
                out.append(r)
        out.sort(key=lambda x: x["index"])
        print(json.dumps(out, indent=2))
    finally:
        ssh.close()


def create_repo(config, host, name, repo_type, location, dry_run, push):

    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if find_repo(host, name):
        print(f"Repository:{name} found in cache. Please pull latest.")
        return

    body = {"type": repo_type, "settings": {"location": location, "compress": True}}
    if dry_run:
        print_dry_run()
        print("PUT", f"/_snapshot/{name}")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("PUT", f"/_snapshot/{name}", body)
        print(f"Repository:{name} created. Updating Cache...")
        pull_host(config, host, es)
    finally:
        ssh.close()


def delete_repo(config, host, name, dry_run, push, force):

    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if not find_repo(host, name):
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
    ssh, es = connect_es(config, host)
    try:
        es.request("DELETE", f"/_snapshot/{name}")
        print(f"Repository:{name} deleted. updating cache...")
        pull_host(config, host, es)
    finally:
        ssh.close()


def create_snapshot(
    config, host, spec, indices, include_global_state, ignore_unavailable, dry_run, push
):

    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    repo, delim, snap = spec.partition("/")
    if not repo or not snap:
        print(f"Snapshot:{spec} is not in valid format. <repo>/<snapshot>")
        return

    if find_snapshot(host, repo, snap):
        print(f"Snapshot:{spec} found in chace. please pull latest.")
        return

    body = {}
    if indices:
        body["indices"] = indices
    body["include_global_state"] = include_global_state
    body["ignore_unavailable"] = ignore_unavailable
    if dry_run:
        print_dry_run()
        print("PUT", f"/_snapshot/{repo}/{snap}")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("PUT", f"/_snapshot/{repo}/{snap}", body)
        pull_host(config, host, es)
    finally:
        ssh.close()


def delete_snapshot(config, host, spec, dry_run, push, force):

    repo, delim, snap = spec.partition("/")
    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if not find_snapshot(host, repo, snap):
        print(f"Snapshot:{spec} not found in chace. Please pull the latest.")
        return

    if not dry_run and not force:
        if not confirm_delete("snapshot", spec):
            print("Cancelled.")
            return

    if dry_run:
        print_dry_run()
        print("DELETE", f"/_snapshot/{repo}/{snap}")
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("DELETE", f"/_snapshot/{repo}/{snap}")
        print(f"Snapshot:{spec} created. Updating Cache.")
        pull_host(config, host, es)
    finally:
        ssh.close()


def restore_snapshot(config, host, spec, index, dry_run, push):
    repo, delim, snap = spec.partition("/")
    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    body = {}
    if index:
        body["indices"] = index
    else:
        body["indices"] = "*"
    body["include_global_state"] = False

    if dry_run:
        print_dry_run()
        print("POST", f"/_snapshot/{repo}/{snap}/_restore")
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        es.request("POST", f"/_snapshot/{repo}/{snap}/_restore", body)
        print(f"Snapshot:{spec} restored. Updating Cache.")
        pull_host(config, host, es)
    finally:
        ssh.close()


def delete_index(config, host, index, dry_run, push, force):
    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if not find_index(host, index):
        print(f"Index:{index} not found in cache. Please pull the latest.")
        return

    if not dry_run and not force:
        if not confirm_delete("index", index):
            print("Cancelled.")
            return

    url = f"/{index}"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_DELETE, url)
        return
    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_DELETE, url)
        print(res)
        print(f"Index:{index} deleted. Updating Cache.")
        pull_host(config, host, es)
    except Exception as e:
        print(e)
    finally:
        ssh.close()


def create_index(config, host, index, mapping, dry_run, push):

    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    if find_index(host, index):
        print(
            f"Index:{index} already exists in the cache. Please pull the latest or delete the index."
        )
        return

    body = {}
    if mapping:
        m = get_reindex_mapping(config, host, mapping)
        if m:
            body["mappings"] = m

    url = f"/{index}"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_PUT, url)
        print(json.dumps(body, indent=2))
        return
    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_PUT, url, body)
        print(res)
        print(f"Index:{index} created. Updating Cache.")
        pull_host(config, host, es)
    except Exception as e:
        print(e)
    finally:
        ssh.close()


def reindex(config, host, src, dst, mapping, dry_run, push):

    if host is None:
        host = get_current_host()

    check_host(host)
    check_push_protected(config, host, dry_run, push)
    print_host(host)

    body = {}
    m = None
    if mapping:
        m = get_reindex_mapping(config, host, mapping)
        if m:
            body["mappings"] = m
        else:
            print(f"Mapping:{mapping} does not exist in the config.")
            return

    dst_exists = find_index(host, dst)
    if m and dst_exists:
        print(
            "Mapping specified, but index already exists in cache. Please pull latest or delete the index."
        )
        return

    if not dst_exists:
        print(f"Creating a new index:{dst}.")
        create_index(config, host, dst, mapping, dry_run, push)

    job = ESKitJob(
        id=str(uuid.uuid4()),
        name=dst,
        type="reindex",
        host=host,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": src, "dst": dst},
    )

    body = {}
    body["source"] = {"index": src}
    body["dest"] = {"index": dst}

    # default: don't wait
    url = f"/_reindex?wait_for_completion=false"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_POST, url)
        print(json.dumps(body, indent=2))
        return

    write_job(host, job)
    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_POST, url, body)
        # print(json.dumps(res, indent=2))
        # print("check status with task-get command with the id")

        job.status = "running"
        job.result = {"task_id": res.get("task")}
        job.updated_at = datetime.now(timezone.utc).isoformat()

        write_job(host, job)

        print(
            f"[{host}] reindex job started search id/output name: {job.get_output_id()}"
        )

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        write_job(host, job)
        print(e)
    finally:
        ssh.close()


def get_task(config, host, task_id):

    if host is None:
        host = get_current_host()

    check_host(host)
    print_host(host)

    url = f"/_tasks/{task_id}"

    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(e)
    finally:
        ssh.close()


def show_index(config, host, index, views, fields, flat):
    if host is None:
        host = get_current_host()

    check_host(host)
    print_host(host)

    if not find_index(host, index):
        print(
            f"Index:{index} not found in cache or does not exist. Please update cache and try again."
        )
        return

    url = f"/{index}"

    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        index_data = res[index]
        target_fields = build_field_list(config, views, fields)

        if len(target_fields) > 0:
            print(json.dumps(apply_view(index_data, target_fields, flat), indent=2))
        else:
            print(json.dumps(index_data, indent=2))

    except Exception as e:
        print(e)
    finally:
        ssh.close()


def parse_stat_line(line: str):
    parts = line.strip().split("|")
    return dict(kv.split("=", 1) for kv in parts)


def get_file_stats(path, transport):

    stas_format = "name=%n|mode=%a|owner=%U|group=%G|mtime_ms=%Y|atime_ms=%X|ctime_ms=%W|mtime_iso=%y|atime_iso=%x|ctime_iso=%w"

    cmd = f"TZ=UTC stat -c '{stas_format}' {path}"

    print("Getting File Stat")
    print(f"transport:{transport.name}")
    print(f"cmd:{cmd}\n")

    out = transport.run(cmd)

    if not out:
        print(f"path:{path} does not exist or failed to get stat")
        return {}

    stat = parse_stat_line(out)
    stat["mtime_ms"] = int(stat["mtime_ms"]) * 1000
    stat["ctime_ms"] = int(stat["ctime_ms"]) * 1000
    stat["atime_ms"] = int(stat["atime_ms"]) * 1000

    cmd = f"du -sb {path}"
    # print(f"cmd:{cmd}")
    file_size = transport.run(cmd)
    # print(f"file_size:{file_size}")
    stat["size"] = file_size.split("\t")[0]
    # print(stat)

    return stat


def get_ssh_config_from_remote_target(config, remote_target):
    remote_host, sep, remote_path = remote_target.partition(":")

    if not sep:
        return None

    # print(f"remote_host:{remote_host}")
    if remote_host:
        return get_host(config, remote_host).get("ssh")

    return None


# <eskit_host>:<dst> to <ssh_host>:<dst>
def convert_remote_host(config, remote_target):

    remote_host, sep, remote_path = remote_target.partition(":")

    if not sep:
        return remote_target

    remote_host_config = get_host(config, remote_host)
    # print(f"remote_host_config:{remote_host_config}")

    ssh_config = remote_host_config.get("ssh")
    user = ssh_config.get("user")

    return f"{user}@{remote_host_config["ip"]}:{remote_path}"


def get_ssh_command(config, remote_target):

    ssh_config = get_ssh_config_from_remote_target(config, remote_target)
    if not ssh_config:
        return None

    # print(f"ssh_config:{ssh_config}")
    ssh_cmd = ""

    password = ssh_config.get("password")
    if password and ssh_config.get("use_sshpass"):
        ssh_cmd = f"sshpass -p {password} "

    ssh_cmd += f"ssh -p {ssh_config.get("port")}"

    identity = ssh_config.get("identity")
    if identity:
        ssh_cmd += f" -i {identity}"

    # print(f"ssh_cmd:{ssh_cmd}")

    return ssh_cmd


def pull_archive_stat(config, host, archive_config):

    host_config = get_host(config, host)
    rsync_src = archive_config["remote_src"]
    rsync_dst = archive_config["local_dst"]

    # update cache/stats
    # src - remote
    transport = SSHConnection(host_config)
    transport.connect()
    try:
        src_stats = get_file_stats(rsync_src, transport)
    except RuntimeError as e:
        print(f"\nfailed to get file stats for remote_src:{e}")
        return
    transport.close()
    # print(json.dumps(src_stats, indent=2))

    # dst - local
    transport = SynchronousProcess(shell=True)
    try:
        dst_stats = get_file_stats(rsync_dst, transport)
    except RuntimeError as e:
        print(f"failed to get file stats for local_dst:{e}")
        return
    # print(json.dumps(dst_stats, indent=2))

    archive = ESKitArchiveState(
        name=archive_config["name"],
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        created_at_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
        updated_at_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
        last_pull=datetime.now(timezone.utc).isoformat(),
        remote_src_stat=src_stats,
        local_dst_stat=dst_stats,
    )
    # print(f"archive:{archive}")
    write_archive(host, archive)


def pull_archive(config, host, name, contents, dry_run, all, sync, preview):

    host_config = get_host(config, host)

    print_host(host)

    archives = host_config.get("archives") or {}

    archive = None
    for a in archives:
        if a["name"] == name:
            archive = a

    if not archive:
        print(f"archive:{name} is not found for host:{host}")
        return

    archive_type = archive["type"]
    job = None
    if archive_type == "snapshot":
        job = pull_snapshot(
            config, host, name, archive, contents, dry_run, sync, preview
        )

    if not dry_run:
        print(
            f"job started:\nid:{job.id}\ncache:{job.cache_path}\nlog:{job.log_path}\npid:{job.pid}"
        )


def pull_snapshot(config, host, name, archive, contets, dry_run, sync, preview):

    rsync_src = archive["remote_src"]
    rsync_dst = archive["local_dst"]

    if contets:
        rsync_src += "/"

    # append the current host to create the remote dst foramt
    remote_host = f"{host}:{rsync_src}"
    ssh_cmd = get_ssh_command(config, remote_host)
    remote_rsync_src = convert_remote_host(config, remote_host)

    cmd = ["rsync", "-av", "--progress"]

    if preview:
        print_preview()
        cmd.append("-n")

    if sync:
        cmd.append("--delete")

    if ssh_cmd:
        cmd.append("-e")
        cmd.append(ssh_cmd)
    cmd.append(remote_rsync_src)
    cmd.append(rsync_dst)

    job = ESKitJob(
        id=str(uuid.uuid4()),
        name="snapshots",
        type="rsync",
        host=host,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": rsync_src, "dst": rsync_dst, "cmd": cmd},
    )
    if dry_run:
        print_dry_run()
        print(f"dry-run job:{json.dumps(job.to_dict(),indent=2)}")
    else:
        job = job_manager.submit(job, LocalExecutor())

    pull_archive_stat(config, host, archive)

    return job


def push_archive(config, host, name, dst, contents, dry_run, preview):

    host_config = get_host(config, host)

    print_host(host)

    archives = host_config.get("archives") or {}

    archive = None
    for a in archives:
        if a["name"] == name:
            archive = a

    if not archive:
        print(f"archive:{name} is not found for host:{host}")
        return

    archive_type = archive["type"]
    job = None
    if archive_type == "snapshot":
        job = push_snapshot(
            config, host, name, archive, dst, contents, dry_run, preview
        )

    if not dry_run:
        print(
            f"job started:\nid:{job.id}\ncache:{job.cache_path}\nlog:{job.log_path}\npid:{job.pid}"
        )


def push_snapshot(config, host, name, archive, remote_dst, contents, dry_run, preview):

    # archive's local dst become source for push
    rsync_src = archive["local_dst"]

    if contents:
        rsync_src = rsync_src + "/"

    rsync_dst = remote_dst

    ssh_cmd = get_ssh_command(config, rsync_dst)
    rsync_dst = convert_remote_host(config, rsync_dst)

    cmd = [
        "rsync",
        "-rv",
        "--progress",
        "--delete",
        "--no-owner",
        "--no-group",
        "--no-times",
    ]

    if preview:
        print_preview()
        cmd.append("-n")

    if ssh_cmd:
        cmd.append("-e")
        cmd.append(ssh_cmd)

    cmd.append(rsync_src)
    cmd.append(rsync_dst)

    job = ESKitJob(
        id=str(uuid.uuid4()),
        name="snapshots",
        type="rsync",
        host=host,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": rsync_src, "dst": rsync_dst, "cmd": cmd},
    )
    if dry_run:
        print_dry_run()
        print(f"dry-run job:{json.dumps(job.to_dict(),indent=2)}")
    else:
        job = job_manager.submit(job, LocalExecutor())

    return job


def cmd_root(args):
    if args.version:
        print(__version__)
    else:
        print("Please use -h/--help for more information.")


def build_parser():
    p = argparse.ArgumentParser(
        prog="eskit",
        description="a light-weight Elasticsearch toolkit for managing repo, snapshots, and index.",
    )

    p.add_argument("--version", action="store_true")
    p.set_defaults(function=cmd_root)

    # common parsers
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_CONFIG,
        help="Set config file. Optional as default value is .eskit/config.json",
    )
    common_parser.add_argument(
        "--host",
        help="Specify which host to operate. Optional if found in .current_host file.",
    )

    # Mutating Operation common
    mutating_parser = argparse.ArgumentParser(add_help=False)
    mutating_parser.add_argument(
        "-dry",
        "--dry-run",
        action="store_true",
        help="Shows only request/command w/o executing it",
    )

    mutating_parser.add_argument(
        "--push",
        action="store_true",
        help="Used to confirm to execute a request/command that would modify resources on push-protected host",
    )

    # Destructive Operation common
    destructive_command_parser = argparse.ArgumentParser(add_help=False)
    destructive_command_parser.add_argument(
        "--force", action="store_true", help="Force to execute delete request/command"
    )

    # common viewer
    viewer_command_parser = argparse.ArgumentParser(add_help=False)
    viewer_command_parser.add_argument("--view", action="append", default=[])
    viewer_command_parser.add_argument("--fields")
    viewer_command_parser.add_argument("--flat", action="store_true")

    sub = p.add_subparsers()

    # Init command
    init = sub.add_parser("init", help="Initializes ESKit.")
    init.set_defaults(function=cmd_init)
    init.add_argument(
        "--demo", action="store_true", help="Initialize with demo data set"
    )

    # Host commands
    host_parser = sub.add_parser("host", help="Host related commands.")
    host_parser_sub = host_parser.add_subparsers(required=True)

    host_show_parser = host_parser_sub.add_parser(
        "show", parents=[common_parser], help="Show available hosts in the config"
    )
    host_show_parser.set_defaults(function=cmd_host)

    host_set_parser = host_parser_sub.add_parser("set", help="Set as current host")
    host_set_parser.add_argument("host")
    host_set_parser.set_defaults(function=cmd_host_set)

    host_get_parser = host_parser_sub.add_parser("get", help="Get current host")
    host_get_parser.set_defaults(function=cmd_host_get)
    #

    # Pull
    pull = sub.add_parser(
        "pull",
        parents=[common_parser],
        help="Pulls resource data from the current host.",
    )
    pull.add_argument(
        "kind",
        choices=["es", "archive"],
        nargs="*",
        help="Kind of cache to pull. es - Elasticsearch Cache, archive - Archive Cache.",
    )
    pull.set_defaults(function=cmd_pull)

    # Cat
    cat = sub.add_parser(
        "cat",
        parents=[common_parser, viewer_command_parser],
        help="Show cached information.",
    )
    cat.add_argument("kind", choices=["repo", "snap", "index"])
    cat.set_defaults(function=cmd_cat2)

    # Repo sub command
    common_repo_parser = argparse.ArgumentParser(add_help=False)
    common_repo_parser.add_argument(
        "name", help="Name of repo or snapshot. <repo> or <repo>/<snapshot>"
    )

    repo = sub.add_parser("repo", parents=[common_parser], help="Repository commands.")

    repo_sub = repo.add_subparsers(required=True)

    repo_show_parser = repo_sub.add_parser(
        "show", parents=[common_parser, common_repo_parser, viewer_command_parser]
    )
    repo_show_parser.set_defaults(function=cmd_repo_show2)

    repo_create = repo_sub.add_parser(
        "create", parents=[common_parser, common_repo_parser, mutating_parser]
    )
    repo_create.add_argument("--type", default="fs")
    repo_create.add_argument("--location", required=True)
    repo_create.set_defaults(function=cmd_create_repo)

    repo_delete = repo_sub.add_parser(
        "delete",
        parents=[
            common_parser,
            common_repo_parser,
            mutating_parser,
            destructive_command_parser,
        ],
    )
    repo_delete.set_defaults(function=cmd_delete_repo)

    # Snapshot Sub Commands
    snap = sub.add_parser("snap", parents=[common_parser], help="Snapshot commands")
    snap_sub = snap.add_subparsers(required=True)

    # common snap parser
    common_snap_parser = argparse.ArgumentParser(add_help=False)
    common_snap_parser.add_argument(
        "name", help="Name to snapshot. must be <repo>/<snapshot>"
    )

    # common snapshot index parser
    common_snap_index_parser = argparse.ArgumentParser(add_help=False)
    common_snap_index_parser.add_argument(
        "--index",
        help="Index to add to the snapshot. * is allowed as a wildcard. Multiple indices allowed by comma separated.",
    )
    common_snap_index_parser.add_argument(
        "--include_global_state", default=False, action="store_true"
    )
    common_snap_index_parser.add_argument(
        "--ignore_unavailable", type=bool, default=True
    )

    snap_create = snap_sub.add_parser(
        "create",
        parents=[
            common_parser,
            common_snap_parser,
            common_snap_index_parser,
            mutating_parser,
        ],
    )
    snap_create.set_defaults(function=cmd_create_snapshot)

    snap_delete = snap_sub.add_parser(
        "delete",
        parents=[
            common_parser,
            common_snap_parser,
            mutating_parser,
            destructive_command_parser,
        ],
    )
    snap_delete.set_defaults(function=cmd_delete_snapshot)

    snap_restore = snap_sub.add_parser(
        "restore",
        parents=[
            common_parser,
            common_snap_parser,
            common_snap_index_parser,
            mutating_parser,
        ],
    )
    snap_restore.set_defaults(function=cmd_restore_snapshot)

    # Index commands
    common_index_parser = argparse.ArgumentParser(add_help=False)
    common_index_parser.add_argument("index")

    index_mapper_parser = argparse.ArgumentParser(add_help=False)
    index_mapper_parser.add_argument(
        "-m", "--mapping", help="Name of mapping in the config."
    )

    index_parser = sub.add_parser("index", help="Index commands.")
    index_sub = index_parser.add_subparsers(required=True)

    index_delete = index_sub.add_parser(
        "delete",
        parents=[
            common_parser,
            common_index_parser,
            mutating_parser,
            destructive_command_parser,
        ],
    )
    index_delete.set_defaults(function=cmd_delete_index)

    index_create = index_sub.add_parser(
        "create",
        parents=[
            common_parser,
            common_index_parser,
            index_mapper_parser,
            mutating_parser,
        ],
    )
    index_create.set_defaults(function=cmd_create_index)

    index_show = index_sub.add_parser(
        "show", parents=[common_parser, common_index_parser, viewer_command_parser]
    )
    index_show.set_defaults(function=cmd_show_index)

    index_status = index_sub.add_parser(
        "status", parents=[common_parser, common_index_parser, viewer_command_parser]
    )
    index_status.set_defaults(function=cmd_restore_status)

    # Reindex Commands
    reindex = sub.add_parser(
        "reindex",
        parents=[common_parser, index_mapper_parser, mutating_parser],
        help="Reindex command.",
    )
    reindex.add_argument(
        "src",
        help="Source index. it can be multiple by comma separated or * wild card can be used",
    )
    reindex.add_argument("dst", help="destination index")
    reindex.set_defaults(function=cmd_reindex)

    reindex_mapping = sub.add_parser(
        "mapping", help="Shows mappings in the config", parents=[common_parser]
    )
    reindex_mapping.set_defaults(function=cmd_reindex_mapping)

    task = sub.add_parser("task", help="Elasticsearch Task Commands")
    task_sub = task.add_subparsers(required=True)

    task_get = task_sub.add_parser(
        "get", help="Get task status on elasticsearch", parents=[common_parser]
    )
    task_get.add_argument("task_id", help="elasticsearch task id")
    task_get.set_defaults(function=cmd_get_task)

    # TODO: rsync is not currently operational
    rsync = sub.add_parser("rsync", parents=[common_parser])
    rsync.add_argument("config_name")

    job = sub.add_parser("job")

    job_sub = job.add_subparsers(required=True)
    job_list = job_sub.add_parser(
        "list", parents=[common_parser, viewer_command_parser]
    )
    job_list.add_argument(
        "--local",
        default=False,
        action="store_true",
        help="Show local jobs in .eskit/jobs generated by archive commands.",
    )
    job_list.set_defaults(function=cmd_list_job)

    job_show = job_sub.add_parser(
        "show", parents=[common_parser, viewer_command_parser]
    )
    job_show.add_argument(
        "job_search_id", help="Job search id / job output file name in the jobs cache"
    )
    job_show.set_defaults(function=cmd_read_job)

    status = sub.add_parser(
        "status", parents=[common_parser], help="Show current ESKit status."
    )
    status.set_defaults(function=cmd_status)

    archive_common_parser = argparse.ArgumentParser(add_help=False)
    archive_common_parser.add_argument("name", help="Name of the archive")

    archive_common_operation_parser = argparse.ArgumentParser(add_help=False)
    archive_common_operation_parser.add_argument(
        "--contents",
        default=False,
        action="store_true",
        help="Copy the contents of the archive directory into the destination, equivalent to using a trailing / on the rsync source path.",
    )
    archive_common_operation_parser.add_argument(
        "--preview",
        action="store_true",
        help="Execute internal commands such as rsync with dry-run mode.",
    )

    # Archive Command
    archive = sub.add_parser(
        "archive", parents=[common_parser], help="Archive commands."
    )

    archive_sub = archive.add_subparsers(required=True)

    archive_list_parser = archive_sub.add_parser(
        "list",
        parents=[common_parser, viewer_command_parser],
    )
    archive_list_parser.set_defaults(function=cmd_list_archive)

    archive_pull_parser = archive_sub.add_parser(
        "pull",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
        ],
    )
    archive_pull_parser.set_defaults(function=cmd_pull_archive)

    archive_sync_parser = archive_sub.add_parser(
        "sync",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
        ],
    )
    archive_sync_parser.set_defaults(function=cmd_sync_archive)

    archive_push_parser = archive_sub.add_parser(
        "push",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
        ],
    )
    archive_push_parser.add_argument(
        "--dst",
        required=True,
        help="Destination host. <eskit_host>:<path> can be used to target remote host. e.g. Host1:/home/user/data.",
    )
    archive_push_parser.set_defaults(function=cmd_push_archive)

    archive_show_parser = archive_sub.add_parser(
        "show", parents=[common_parser, viewer_command_parser, archive_common_parser]
    )
    archive_show_parser.set_defaults(function=cmd_show_archive)

    return p


def main():

    args = build_parser().parse_args()

    global job_manager
    job_manager = ESKitJobManager(CACHE_ROOT)

    args.function(args)
    return
