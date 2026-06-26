from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PACKAGE_ROOT / "data"
DEMO_DIR = DATA_DIR / "demo"
CONFIG_TEMPLATE_DIR = DATA_DIR / "config_template"
CACHE_ROOT = Path(".eskit")

def cache_dir(host):
    return CACHE_ROOT / host / "cache"

def root_dir():
    return CACHE_ROOT

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
