import json
from datetime import datetime, timezone
from eskit.utils.config import load_config, get_host_config
from eskit.core.host import get_current_host_name, check_host_name, print_host
from eskit.clients.es_client import connect_es
from eskit.cache.store import write_cache, read_cache
from eskit.transport.ssh import SSHConnection
from eskit.transport.process import SynchronousProcess
from eskit.archive.model import ESKitArchiveState
from eskit.utils.archive import list_archives, delete_archive, write_archive
from eskit.utils.view import build_field_list, apply_view


def pull(config_path, host_name, kind=None):

    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)
    print_host(host_name)

    config = load_config(config_path)
    host_config = get_host_config(config, host_name)

    pull_all = kind is None or len(kind) == 0

    if pull_all or "es" in kind:
        transport, es = connect_es(host_config)
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
        transport.close()

    # pull archive status
    if pull_all or "archive" in kind:
        print("pull archive metadata")
        pull_archive_metadata(host_config, host_name)

    print("\nCache updated.\n")


def pull_archive_metadata(host_config, host_name):

    archives = host_config.get("archives")

    if not archives:
        print("no archives to pull metadata")
        return

    for archive in archives:
        pull_archive_stat(host_config, host_name, archive)

    # clean stale cache
    cached_archives = list_archives(host_name)

    for cache in cached_archives:
        exists = any(d.get("name") == cache["name"] for d in archives)
        if not exists:
            delete_archive(host_name, ESKitArchiveState.from_dict(cache))


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


def write_archive_all(config, host):
    host_config = get_host_config(config, host)
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


def pull_archive_stat(host_config, host_name, archive_config):

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
    write_archive(host_name, archive)


def cat(config_path, host_name, kind, views, fields, flat):
    # config, kind, host_name, views, fields, flat
    config = load_config(config_path)

    mapping = {"repo": "repos", "snap": "snapshots", "index": "indices"}
    kind = mapping[kind]

    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)

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
