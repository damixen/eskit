import json
import shutil
import logging

from eskit.utils.paths import CACHE_ROOT, ensure_root, root_dir, DEMO_DIR
from eskit.version import __cache_version__
from eskit.result import Result, ResultCode
from eskit.resource_type import ResourceType

logger = logging.getLogger(__name__)


def init(is_demo):

    if CACHE_ROOT.exists():
        return Result.fail(
            ResultCode.ALREADY_EXISTS,
            "The cache folder already exists.",
            {"resource": ResourceType.CACHE, "name": ".eskit"},
        )

    ensure_root()

    # write config for startup
    config = {"hosts": []}
    config_path = root_dir() / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    # print(".eskit and .eskit/config.json created.")

    if is_demo:
        shutil.copytree(
            f"{DEMO_DIR}/{__cache_version__}", root_dir(), dirs_exist_ok=True
        )
        # print(f"demo/{__cache_version__} copied to .eskit folder.")

    return Result.ok({"resource": ResourceType.CACHE, "name": config_path})
