import json

from eskit.core.host import get_current_host_name, check_host_name
from eskit.utils.config import load_config, is_push_protected
from eskit.utils.paths import cache_dir
from eskit.cache.store import read_cache, cache_date


def get_status(host_name, config_path):
    print("get status")
    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)

    config = load_config(config_path)

    status = {}
    status["host"] = {
        "name": host_name,
        "push-protected": is_push_protected(config, host_name),
    }

    cluster_version = read_cache(host_name, "version")
    status["cluster"] = {}
    if cluster_version:
        status["cluster"] = {
            "name": cluster_version["name"],
            "cluster_name": cluster_version["cluster_name"],
            "version": {
                "number": cluster_version["version"]["number"],
                "build_flavor": cluster_version["version"]["build_flavor"],
            },
        }

    status["caches"] = {}

    cache_root = cache_dir(host_name)

    for name in ["indices", "repos", "snapshots", "version"]:
        path = cache_root / f"{name}.json"
        date = cache_date(path)
        status["caches"][name] = {}
        if date is None:
            status["caches"][name]["last-updated"] = ""
        else:
            status["caches"][name]["last-updated"] = date

    return status
    # print(json.dumps(status, indent=2))

    """ TODO
    jobs = list_jobs(host_name)

    running = sum(1 for j in jobs if j["status"] == "running")
    failed = sum(1 for j in jobs if j["status"] == "failed")
    success = sum(1 for j in jobs if j["status"] == "success")

    print("\nJobs:")
    print(f"  running: {running}")
    print(f"  success: {success}")
    print(f"  failed:  {failed}")
    """
