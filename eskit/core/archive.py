import json
import uuid
from datetime import datetime, timezone
from eskit.utils.config import load_config, get_host_config
from eskit.utils.view import build_field_list, apply_view
from eskit.utils.archive import list_archives, read_archive
from eskit.core.host import (
    get_current_host_name,
    check_host_name,
    print_host,
    print_dry_run,
    print_preview,
)
from eskit.core.metadata import pull_archive_stat
from eskit.jobs.job import ESKitJob
from eskit.jobs.executers import LocalExecutor
from eskit.jobs.job_manager import get


def list(config_path, host_name, views, fields, flat):

    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)

    config = load_config(config_path)

    data = list_archives(host_name)

    target_fields = build_field_list(config, views, fields)
    out = []

    if len(target_fields) > 0:
        for job in data:
            out.append(apply_view(job, target_fields, flat))
    else:
        out = data

    print(json.dumps(out, indent=2))


def pull(config_path, host_name, name, contents, dry_run, all, sync, preview):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)

    host_config = get_host_config(config, host_name)

    print_host(host_name)

    archives = host_config.get("archives") or {}

    archive = None
    for a in archives:
        if a["name"] == name:
            archive = a

    if not archive:
        print(f"archive:{name} is not found for host:{host_name}")
        return

    archive_type = archive["type"]
    job = None
    if archive_type == "snapshot":
        job = pull_snapshot(
            config, host_name, name, archive, contents, dry_run, sync, preview
        )

    if not dry_run:
        print(
            f"job started:\nid:{job.id}\ncache:{job.cache_path}\nlog:{job.log_path}\npid:{job.pid}"
        )


def push(config_path, host_name, name, dst, contents, dry_run, preview):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)

    host_config = get_host_config(config, host_name)

    print_host(host_name)

    archives = host_config.get("archives") or {}

    archive = None
    for a in archives:
        if a["name"] == name:
            archive = a

    if not archive:
        print(f"archive:{name} is not found for host:{host_name}")
        return

    archive_type = archive["type"]
    job = None
    if archive_type == "snapshot":
        job = push_snapshot(
            config, host_name, name, archive, dst, contents, dry_run, preview
        )

    if not dry_run:
        print(
            f"job started:\nid:{job.id}\ncache:{job.cache_path}\nlog:{job.log_path}\npid:{job.pid}"
        )


def show(config_path, host_name, name, views, fields, flat):
    if host_name is None:
        host_name = get_current_host_name()

    check_host_name(host_name)

    config = load_config(config_path)

    archive_name = name
    target_fields = build_field_list(config, views, fields)
    out = {}

    data = read_archive(host_name, archive_name)

    if len(target_fields) > 0:
        out = apply_view(data, target_fields, flat)
    else:
        out = data

    print(json.dumps(out, indent=2))


# Internal
def pull_snapshot(config, host, name, archive, contets, dry_run, sync, preview):

    rsync_src = archive["remote_src"]
    rsync_dst = archive["local_dst"]

    if contets:
        rsync_src += "/"

    # append the current host to create the remote dst foramt
    remote_host = f"{host}:{rsync_src}"
    ssh_cmd = get_ssh_command(config, remote_host)
    remote_rsync_src = convert_remote_host(config, remote_host)

    cmd = ["rsync", "-av", "--progress"]

    if preview:
        print_preview()
        cmd.append("-n")

    if sync:
        cmd.append("--delete")

    if ssh_cmd:
        cmd.append("-e")
        cmd.append(ssh_cmd)
    cmd.append(remote_rsync_src)
    cmd.append(rsync_dst)

    job = ESKitJob(
        id=str(uuid.uuid4()),
        name="snapshots",
        type="rsync",
        host=host,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": rsync_src, "dst": rsync_dst, "cmd": cmd},
    )
    if dry_run:
        print_dry_run()
        print(f"dry-run job:{json.dumps(job.to_dict(),indent=2)}")
    else:
        job = get().submit(job, LocalExecutor())

    host_config = get_host_config(config, host)
    pull_archive_stat(host_config, host, archive)

    return job


def push_snapshot(config, host, name, archive, remote_dst, contents, dry_run, preview):

    # archive's local dst become source for push
    rsync_src = archive["local_dst"]

    if contents:
        rsync_src = rsync_src + "/"

    rsync_dst = remote_dst

    ssh_cmd = get_ssh_command(config, rsync_dst)
    rsync_dst = convert_remote_host(config, rsync_dst)

    cmd = [
        "rsync",
        "-rv",
        "--progress",
        "--delete",
        "--no-owner",
        "--no-group",
        "--no-times",
    ]

    if preview:
        print_preview()
        cmd.append("-n")

    if ssh_cmd:
        cmd.append("-e")
        cmd.append(ssh_cmd)

    cmd.append(rsync_src)
    cmd.append(rsync_dst)

    job = ESKitJob(
        id=str(uuid.uuid4()),
        name="snapshots",
        type="rsync",
        host=host,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": rsync_src, "dst": rsync_dst, "cmd": cmd},
    )
    if dry_run:
        print_dry_run()
        print(f"dry-run job:{json.dumps(job.to_dict(),indent=2)}")
    else:
        job = get().submit(job, LocalExecutor())

    return job


# <eskit_host>:<dst> to <ssh_host>:<dst>
def convert_remote_host(config, remote_target):

    remote_host, sep, remote_path = remote_target.partition(":")

    if not sep:
        return remote_target

    remote_host_config = get_host_config(config, remote_host)
    # print(f"remote_host_config:{remote_host_config}")

    ssh_config = remote_host_config.get("ssh")
    user = ssh_config.get("user")

    return f"{user}@{remote_host_config["ip"]}:{remote_path}"


def get_ssh_config_from_remote_target(config, remote_target):
    remote_host, sep, remote_path = remote_target.partition(":")

    if not sep:
        return None

    # print(f"remote_host:{remote_host}")
    if remote_host:
        return get_host_config(config, remote_host).get("ssh")

    return None


def get_ssh_command(config, remote_target):

    ssh_config = get_ssh_config_from_remote_target(config, remote_target)
    if not ssh_config:
        return None

    # print(f"ssh_config:{ssh_config}")
    ssh_cmd = ""

    password = ssh_config.get("password")
    if password and ssh_config.get("use_sshpass"):
        ssh_cmd = f"sshpass -p {password} "

    ssh_cmd += f"ssh -p {ssh_config.get("port")}"

    identity = ssh_config.get("identity")
    if identity:
        ssh_cmd += f" -i {identity}"

    # print(f"ssh_cmd:{ssh_cmd}")

    return ssh_cmd
