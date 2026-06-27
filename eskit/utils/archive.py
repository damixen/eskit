import json
from pathlib import Path
from dataclasses import dataclass, asdict

from eskit.utils.paths import archive_dir, ensure_archive_dir
from eskit.archive.model import ESKitArchiveState


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


def list_archives(host):
    if not archive_dir(host).exists():
        return []

    archives = []
    for f in archive_dir(host).glob("*.json"):
        archives.append(json.load(open(f)))

    archives.sort(key=lambda x: x["created_at"], reverse=True)
    return archives
