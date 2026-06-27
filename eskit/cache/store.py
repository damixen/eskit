import json
from datetime import datetime
from eskit.utils.paths import cache_dir
from eskit.archive.model import ESKitArchiveState

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

def ensure_cache(host):
    cache_dir(host).mkdir(parents=True, exist_ok=True)


def cache_date(path):
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).strftime(
        "%A, %B %d, %Y at %I:%M %p"
    )


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
