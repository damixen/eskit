import json
import logging
from datetime import datetime, UTC
from dataclasses import asdict
from eskit.utils.paths import cache_dir, archive_dir, ensure_job_dir, job_dir
from eskit.jobs.job import ESKitJob
from eskit.version import __cache_format_version__

logger = logging.getLogger(__name__)


def read_archive(host, archive_id):
    path = archive_dir(host) / f"{archive_id}.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_cache(host):
    cache_dir(host).mkdir(parents=True, exist_ok=True)


def cache_date(path):
    if not path.exists():
        return None

    return datetime.fromtimestamp(
        path.stat().st_mtime,
        tz=UTC,
    ).isoformat(timespec="seconds")


def write_cache(host, name, data):
    ensure_cache(host)
    with open(cache_dir(host) / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def read_cache(host, name):
    p = cache_dir(host) / f"{name}.json"
    if not p.exists():
        logger.info("Cached:%s information not found. Run: eskit pull %s", name, host)
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write_job(host, job: ESKitJob):
    ensure_job_dir(host)
    with open(
        job_dir(host) / f"{job.get_output_id()}.json", "w", encoding="utf-8"
    ) as f:
        json.dump(asdict(job), f, indent=2)


def check_cache_version(host):
    if not (cache_dir(host) / "version.json").exists():
        return False

    version = read_cache(host, "version")
    if not version:
        return False

    version_meta = version.get("_meta", None)

    if not version_meta:
        return False

    cache_format_version = version_meta.get("cache_format_version", None)
    if not cache_format_version or cache_format_version < __cache_format_version__:
        return False

    return True
