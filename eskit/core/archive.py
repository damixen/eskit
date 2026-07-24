import uuid
import logging
from datetime import datetime, timezone
from eskit.utils.config import get_host_config
from eskit.utils.archive import list_archives, read_archive
from eskit.core.host import check_host_name
from eskit.core.metadata import pull_archive_stat
from eskit.jobs.job import ESKitJob
from eskit.jobs.executers import LocalExecutor
from eskit.jobs.job_manager import get as get_jbm
from eskit.result import Result, ResultCode
from eskit.config.types import Config

logger = logging.getLogger(__name__)


def get_list(host_name):

    check_host_name(host_name)

    data = list_archives(host_name)

    return Result.ok(data)


def pull(config: Config, host_name, name, contents, dry_run, all, sync, preview):

    check_host_name(host_name)

    host_config = get_host_config(config, host_name)

    archives = host_config.get("archives") or {}

    archive = None
    for a in archives:
        if a["name"] == name:
            archive = a

    if not archive:
        # logger.warning("archive:%s is not found for host:%s", name, host_name)
        return Result.fail(ResultCode.NOT_FOUND, "Resource not found.")

    archive_type = archive["type"]
    job = None
    if archive_type == "snapshot":
        job = pull_snapshot(
            config, host_name, archive, contents, dry_run, sync, preview
        )

    if not job:
        return Result.fail(
            ResultCode.INTERNAL_ERROR, "Failed to pull archive.", context=archive
        )

    return Result.ok(job.to_dict())


def push(config: Config, host_name, name, dst, contents, dry_run, preview):

    check_host_name(host_name)

    host_config = get_host_config(config, host_name)

    archives = host_config.get("archives") or {}

    archive = None
    for a in archives:
        if a["name"] == name:
            archive = a

    if not archive:
        # logger.error("archive:%s is not found for host:%s", name, host_name)
        return Result.fail(ResultCode.NOT_FOUND, "Resource not found.")

    archive_type = archive["type"]
    job = None
    if archive_type == "snapshot":
        job = push_snapshot(config, host_name, archive, dst, contents, dry_run, preview)

    if not job:
        return Result.fail(
            ResultCode.INTERNAL_ERROR, "Failed to pull archive.", context=archive
        )

    return Result.ok(job.to_dict())


def get(host_name, name):
    """
    Public API
    """

    check_host_name(host_name)

    archive_name = name

    data = read_archive(host_name, archive_name)

    if data is None:
        return Result.fail(ResultCode.NOT_FOUND, f"Archive {name} not found.")

    return Result.ok(data)


# Internal
def pull_snapshot(config: Config, host, archive, contets, dry_run, sync, preview):

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
        # print_preview()
        cmd.append("-n")

    if sync:
        cmd.append("--delete")

    if ssh_cmd:
        cmd.append("-e")
        cmd.append(ssh_cmd)
    cmd.append(remote_rsync_src)
    cmd.append(rsync_dst)

    job_id = ""
    job_status = "running"
    if dry_run:
        job_status = "dry-run"
    else:
        job_id = str(uuid.uuid4())

    job = ESKitJob(
        id=job_id,
        name="snapshots",
        type="rsync",
        host=host,
        status=job_status,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": rsync_src, "dst": rsync_dst, "cmd": cmd},
        preview=preview,
    )

    if not dry_run:
        jbm = get_jbm()
        assert jbm is not None
        job = jbm.submit(job, LocalExecutor())
        host_config = get_host_config(config, host)
        pull_archive_stat(host_config, host, archive)

    return job


def push_snapshot(
    config: Config, host, archive, remote_dst, contents, dry_run, preview
):

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
        # print_preview()
        cmd.append("-n")

    if ssh_cmd:
        cmd.append("-e")
        cmd.append(ssh_cmd)

    cmd.append(rsync_src)
    cmd.append(rsync_dst)

    job_id = ""
    job_status = "running"
    if dry_run:
        job_status = "dry-run"
    else:
        job_id = str(uuid.uuid4())

    job = ESKitJob(
        id=job_id,
        name="snapshots",
        type="rsync",
        host=host,
        status=job_status,
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": rsync_src, "dst": rsync_dst, "cmd": cmd},
        preview=preview,
    )
    if not dry_run:
        jbm = get_jbm()
        assert jbm is not None
        job = jbm.submit(job, LocalExecutor())

    return job


# <eskit_host>:<dst> to <ssh_host>:<dst>
def convert_remote_host(config: Config, remote_target):

    remote_host, sep, remote_path = remote_target.partition(":")

    if not sep:
        return remote_target

    remote_host_config = get_host_config(config, remote_host)
    # print(f"remote_host_config:{remote_host_config}")

    ssh_config = remote_host_config.get("ssh")
    user = ssh_config.get("user")

    return f"{user}@{remote_host_config["ip"]}:{remote_path}"


def get_ssh_config_from_remote_target(config: Config, remote_target):
    remote_host, sep, remote_path = remote_target.partition(":")

    if not sep:
        return None

    # print(f"remote_host:{remote_host}")
    if remote_host:
        return get_host_config(config, remote_host).get("ssh")

    return None


def get_ssh_command(config: Config, remote_target):

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
