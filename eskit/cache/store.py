import json
from datetime import datetime
from eskit.utils.paths import cache_dir


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
