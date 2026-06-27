import json
from datetime import datetime
from dataclasses import dataclass, asdict
from eskit.utils.paths import cache_dir, archive_dir, ensure_job_dir, job_dir
from eskit.jobs.job import ESKitJob


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


def write_job(host, job: ESKitJob):
    ensure_job_dir(host)
    with open(job_dir(host) / f"{job.get_output_id()}.json", "w") as f:
        json.dump(asdict(job), f, indent=2)
