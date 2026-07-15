import logging
from datetime import datetime, timezone
from eskit.utils.config import get_host_config
from eskit.core.host import check_host_name
from eskit.clients.es_client import connect_es
from eskit.cache.store import write_cache, read_cache
from eskit.transport.ssh import SSHConnection
from eskit.transport.process import SynchronousProcess
from eskit.archive.model import ESKitArchiveState
from eskit.utils.archive import list_archives, delete_archive, write_archive
from eskit.result import Result, ResultCode
from eskit.config.types import FileStat

logger = logging.getLogger(__name__)


def pull_metadata(config, host_name, kind=None):
    """
    Public API
    """

    check_host_name(host_name)

    host_config = get_host_config(config, host_name)

    pull_all = kind is None or len(kind) == 0

    if pull_all or "es" == kind:
        transport, es = connect_es(host_config)
        repos = es.request("GET", "/_snapshot")
        write_cache(host_name, "repos", repos)

        snapshots = {}
        if isinstance(repos, dict):
            for repo in repos.keys():
                snapshots[repo] = es.request("GET", f"/_snapshot/{repo}/_all")
        write_cache(host_name, "snapshots", snapshots)

        indices = es.request("GET", "/_cat/indices?format=json")

        # get index version
        index_settings = es.request(
            "GET", "/_all/_settings?filter_path=*.settings.index.version.created"
        )
        # print(f"index_settings:{json.dumps(index_settings, indent=2)}")
        for index in indices:
            index_name = index.get("index")
            if index_name in index_settings:
                index["version"] = index_settings[index_name]["settings"]["index"][
                    "version"
                ]

        write_cache(host_name, "indices", indices)

        version = es.request("GET", "/")
        write_cache(host_name, "version", version)
        transport.close()

    # pull archive status
    if pull_all or "archive" == kind:
        logger.info("pull archive metadata")
        pull_archive_metadata(host_config, host_name)

    return Result.ok()


def pull_archive_metadata(host_config, host_name):

    archives = host_config.get("archives")

    if not archives:
        logger.info("No archive in the config")
        return

    for archive in archives:
        pull_archive_stat(host_config, host_name, archive)

    # clean stale cache
    cached_archives = list_archives(host_name)

    for cache in cached_archives:
        exists = any(d.get("name") == cache["name"] for d in archives)
        if not exists:
            logger.info("Deleting an archive that's not in the config.")
            delete_archive(host_name, ESKitArchiveState.from_dict(cache))


def parse_stat_line(line: str):
    parts = line.strip().split("|")
    return dict(kv.split("=", 1) for kv in parts)


def parse_stat(line: str) -> FileStat:
    raw = parse_stat_line(line)

    return {
        "name": raw["name"],
        "mode": raw["mode"],
        "owner": raw["owner"],
        "group": raw["group"],
        "mtime_ms": int(raw["mtime_ms"]) * 1000,
        "atime_ms": int(raw["atime_ms"]) * 1000,
        "ctime_ms": int(raw["ctime_ms"]) * 1000,
        "mtime_iso": raw["mtime_iso"],
        "atime_iso": raw["atime_iso"],
        "ctime_iso": raw["ctime_iso"],
        "size": 0,
    }


def get_file_stats(path, transport) -> FileStat | None:

    stas_format = "name=%n|mode=%a|owner=%U|group=%G|mtime_ms=%Y|atime_ms=%X|ctime_ms=%W|mtime_iso=%y|atime_iso=%x|ctime_iso=%w"

    cmd = f"TZ=UTC stat -c '{stas_format}' {path}"

    logger.info("Getting File Stat")
    logger.debug("transport:%s", transport.name)
    logger.debug("cmd:%s\n", cmd)

    out = transport.run(cmd)

    if not out:
        logger.warning("path:%s does not exist or failed to get stat", path)
        return None

    stat = parse_stat(out)

    cmd = f"du -sb {path}"
    # print(f"cmd:{cmd}")
    file_size = transport.run(cmd)
    # print(f"file_size:{file_size}")
    stat["size"] = int(file_size.split("\t")[0])
    # print(stat)

    return stat


def pull_archive_stat(host_config, host_name, archive_config):

    rsync_src = archive_config["remote_src"]
    rsync_dst = archive_config["local_dst"]

    # update cache/stats
    # src - remote
    transport = SSHConnection(host_config)
    transport.connect()
    src_stats = get_file_stats(rsync_src, transport)
    transport.close()
    # print(json.dumps(src_stats, indent=2))

    # dst - local
    transport = SynchronousProcess(shell=True)
    dst_stats = get_file_stats(rsync_dst, transport)
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


def get_metadata(config, host_name, kind):
    """
    Public API
    """

    mapping = {"repo": "repos", "snap": "snapshots", "index": "indices"}
    kind = mapping[kind]

    check_host_name(host_name)

    data = read_cache(host_name, kind)

    if not data:
        return Result.fail(ResultCode.NOT_FOUND, "Resource not found.")

    out = {}
    if kind == "snapshots":
        snap_list = []
        for repo, repo_data in data.items():
            snapshots = repo_data.get("snapshots", {})

            for s in snapshots:
                snap_list.append(s)

        out = snap_list
    elif kind == "repos":
        out = {}
        for repo, repo_data in data.items():
            out[repo] = repo_data
    elif kind == "indices":
        out = data
        out.sort(key=lambda x: x["index"])
    elif kind == "recovery":
        out = data

    return Result.ok(out)
