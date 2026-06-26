import json
import shutil

from eskit.utils.paths import CACHE_ROOT, ensure_root, root_dir, DEMO_DIR
from eskit.core.version import __cache_version__

def init(is_demo):

    if CACHE_ROOT.exists():
        print(".eskit folder already exists.")
        if is_demo:
            print("If you want to reset, please remove the folder first.")
        return

    ensure_root()

    # write config for startup
    config = {"hosts": []}
    with open(root_dir() / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(".eskit and .eskit/config.json created.")

    if is_demo:
        shutil.copytree(f"{DEMO_DIR}/{__cache_version__}", root_dir(), dirs_exist_ok=True)
        print(f"demo/{__cache_version__} copied to .eskit folder.")