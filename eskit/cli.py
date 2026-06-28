#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from datetime import datetime
from eskit.jobs.job_manager import ESKitJobManager
from eskit.transport.process import SynchronousProcess
from eskit.transport.ssh import SSHConnection
from eskit.clients.es_client import ESClient
from eskit.core.host import get_current_host_name
from .error import ConfigError

job_manager = None


__version__ = "0.1.0"
__cache_version__ = "v1"

DEFAULT_CONFIG = ".eskit/config.json"
CACHE_ROOT = Path(".eskit")
HTTP_METHOD_DELETE = "DELETE"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_POST = "POST"
HTTP_METHOD_GET = "GET"
CURRENT_HOST = ".current_host"


def print_host(host):
    print(f"\n=== ESKit HOST: {host} ===\n")


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_host(config, name):
    for h in config.get("hosts", []):
        if h["name"] == name:
            return h
    raise SystemExit(f"Host not found: {name}")


def check_host(host):
    if host is None:
        raise SystemExit(
            "Host not found. Please specify the host or set the host by the host set command."
        )
    return


def get_current_host():
    if not (CACHE_ROOT / CURRENT_HOST).exists():
        return

    with open(CACHE_ROOT / CURRENT_HOST, "r", encoding="utf-8") as f:
        for line in f:
            return line


def get_path(data, path):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        part = part.replace("$", ".")
        if part not in current:
            return None
        current = current[part]
    return current


def set_path(data, path, value):
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        part = part.replace("$", ".")
        if part not in current:
            current[part] = {}
        current = current[part]
    current[parts[-1].replace("$", ".")] = value


def apply_view(data, fields, flat):
    out = {}

    for field in fields:
        value = get_path(data, field)
        if flat:
            out[field] = value
        elif value is not None:
            set_path(out, field, value)

    return out


def get_view(config, views):
    views_config = config.get("views", {})
    out = []
    for name in views:
        if name not in views_config:
            raise ConfigError(f"view not found: {name}")
        out.extend(views_config[name])
    return out


def build_field_list(config, views, fields):
    result = []

    for view in views:
        result.extend(config["views"].get(view, []))

    if fields:
        result.extend(fields.split(","))

    return list(dict.fromkeys(result))


def connect_es(config, host_name):

    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    host_cfg = get_host(config, host_name)

    is_localhost = host_cfg.get("localhost") or False

    transport = None

    if is_localhost:
        transport = SynchronousProcess()
    else:
        transport = SSHConnection(host_cfg)
        transport.connect()
    elastic_config = {}
    if "elastic" in host_cfg:
        elastic_config = host_cfg["elastic"]
    return transport, ESClient(transport, elastic_config)


def cmd_host(args):
    from eskit.core.host import get_hosts

    hosts = get_hosts(args.host, args.config)
    print(json.dumps(hosts, indent=2))


def cmd_host_set(args):
    from eskit.core.host import set_current_host_name

    set_current_host_name(args.host)


def cmd_host_get(args):
    print(get_current_host_name())


def cmd_list_job(args):
    host_name = args.host
    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    config = None
    if "config" in args:
        config = load_config(args.config)

    local = args.local

    data = job_manager.list_dicts(host_name, local)
    data.sort(key=lambda x: datetime.fromisoformat(x["updated_at"]), reverse=True)

    views = args.view
    fields = args.fields
    flat = args.flat
    target_fields = build_field_list(config, views, fields)
    out = []

    if len(target_fields) > 0:
        for job in data:
            out.append(apply_view(job, target_fields, flat))
    else:
        out = data

    print(json.dumps(out, indent=2))


def cmd_read_job(args):

    host_name = args.host
    if host_name is None:
        host_name = get_current_host()

    check_host(host_name)

    config = None
    if "config" in args:
        config = load_config(args.config)

    views = args.view
    fields = args.fields
    flat = args.flat
    job_search_id = args.job_search_id
    target_fields = build_field_list(config, views, fields)
    out = {}

    data = job_manager.load_dict(host_name, job_search_id)

    if len(target_fields) > 0:
        out = apply_view(data, target_fields, flat)
    else:
        out = data

    print(json.dumps(out, indent=2))

    return


def cmd_status(args):

    from eskit.core.status import get_status

    status = get_status(args.host, args.config)

    print(json.dumps(status, indent=2))


def cmd_pull(args):
    from eskit.core.metadata import pull

    pull(args.config, args.host, args.kind)


def cmd_cat2(args):
    from eskit.core.metadata import cat

    cat(args.config, args.host, args.kind, args.view, args.fields, args.flat)


def cmd_repo_show2(args):

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    views = args.view
    fields = args.fields
    flat = args.flat

    from eskit.core.repo import show

    show(args.config, host_name, name, views, fields, flat)


def cmd_delete_repo(args):

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    dry_run = args.dry_run
    push = args.push
    force = args.force

    from eskit.core.repo import delete

    delete(args.config, host_name, name, dry_run, push, force)


def cmd_create_repo(args):

    host_name = args.host

    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    name = args.name
    dry_run = args.dry_run
    push = args.push
    repo_type = args.type
    location = args.location

    from eskit.core.repo import create

    create(args.config, host_name, name, repo_type, location, dry_run, push)


def cmd_reindex_mapping(args):
    config = None
    if "config" in args:
        config = load_config(args.config)
    print(json.dumps(config["reindex-configs"], indent=2))


def cmd_create_snapshot(args):

    from eskit.core.snap import create

    create(
        args.config,
        args.host,
        args.name,
        args.index,
        args.include_global_state,
        args.ignore_unavailable,
        args.dry_run,
        args.push,
    )


def cmd_delete_snapshot(args):

    from eskit.core.snap import delete

    delete(args.config, args.host, args.name, args.dry_run, args.push, args.force)


def cmd_restore_snapshot(args):

    from eskit.core.snap import restore

    restore(args.config, args.host, args.name, args.index, args.dry_run, args.push)


def cmd_restore_status(args):

    from eskit.core.index import status

    status(args.config, args.host, args.index, args.view, args.fields, args.flat)


def cmd_delete_index(args):

    from eskit.core.index import delete

    delete(args.config, args.host, args.index, args.dry_run, args.push, args.force)


def cmd_create_index(args):

    from eskit.core.index import create

    create(args.config, args.host, args.index, args.mapping, args.dry_run, args.push)


def cmd_show_index(args):

    index = args.index
    views = args.view
    fields = args.fields
    flat = args.flat

    from eskit.core.index import show

    show(args.config, args.host, index, views, fields, flat)


def cmd_reindex(args):

    from eskit.core.index import reindex

    reindex(
        args.config,
        args.host,
        args.src,
        args.dst,
        args.mapping,
        args.dry_run,
        args.push,
    )


def cmd_get_task(args):
    config = None
    if "config" in args:
        config = load_config(args.config)

    host_name = args.host
    if host_name is None:
        host_name = get_current_host()
    check_host(host_name)

    task_id = args.task_id
    get_task(config, host_name, task_id)


def cmd_init(args):
    from eskit.core.init import init

    init(args.demo)


def cmd_list_archive(args):

    from eskit.core.archive import list

    list(args.config, args.host, args.view, args.fields, args.flat)


def cmd_pull_archive(args):
    from eskit.core.archive import pull

    pull(
        args.config,
        args.host,
        args.name,
        args.contents,
        args.dry_run,
        False,
        False,
        args.preview,
    )


def cmd_sync_archive(args):
    from eskit.core.archive import pull

    pull(
        args.config,
        args.host,
        args.name,
        args.contents,
        args.dry_run,
        False,
        True,
        args.preview,
    )


def cmd_push_archive(args):
    from eskit.core.archive import push

    push(
        args.config,
        args.host,
        args.name,
        args.dst,
        args.contents,
        args.dry_run,
        args.preview,
    )


def cmd_show_archive(args):
    from eskit.core.archive import show

    show(args.config, args.host, args.name, args.view, args.fields, args.flat)


def get_task(config, host, task_id):

    if host is None:
        host = get_current_host()

    check_host(host)
    print_host(host)

    url = f"/_tasks/{task_id}"

    ssh, es = connect_es(config, host)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(e)
    finally:
        ssh.close()


def cmd_root(args):
    if args.version:
        print(__version__)
    else:
        print("Please use -h/--help for more information.")


def build_parser():
    p = argparse.ArgumentParser(
        prog="eskit",
        description="a light-weight Elasticsearch toolkit for managing repo, snapshots, and index.",
    )

    p.add_argument("--version", action="store_true")
    p.set_defaults(function=cmd_root)

    # common parsers
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_CONFIG,
        help="Set config file. Optional as default value is .eskit/config.json",
    )
    common_parser.add_argument(
        "--host",
        help="Specify which host to operate. Optional if found in .current_host file.",
    )

    # Mutating Operation common
    mutating_parser = argparse.ArgumentParser(add_help=False)
    mutating_parser.add_argument(
        "-dry",
        "--dry-run",
        action="store_true",
        help="Shows only request/command w/o executing it",
    )

    mutating_parser.add_argument(
        "--push",
        action="store_true",
        help="Used to confirm to execute a request/command that would modify resources on push-protected host",
    )

    # Destructive Operation common
    destructive_command_parser = argparse.ArgumentParser(add_help=False)
    destructive_command_parser.add_argument(
        "--force", action="store_true", help="Force to execute delete request/command"
    )

    # common viewer
    viewer_command_parser = argparse.ArgumentParser(add_help=False)
    viewer_command_parser.add_argument("--view", action="append", default=[])
    viewer_command_parser.add_argument("--fields")
    viewer_command_parser.add_argument("--flat", action="store_true")

    sub = p.add_subparsers()

    # Init command
    init = sub.add_parser("init", help="Initializes ESKit.")
    init.set_defaults(function=cmd_init)
    init.add_argument(
        "--demo", action="store_true", help="Initialize with demo data set"
    )

    # Host commands
    host_parser = sub.add_parser("host", help="Host related commands.")
    host_parser_sub = host_parser.add_subparsers(required=True)

    host_show_parser = host_parser_sub.add_parser(
        "show", parents=[common_parser], help="Show available hosts in the config"
    )
    host_show_parser.set_defaults(function=cmd_host)

    host_set_parser = host_parser_sub.add_parser("set", help="Set as current host")
    host_set_parser.add_argument("host")
    host_set_parser.set_defaults(function=cmd_host_set)

    host_get_parser = host_parser_sub.add_parser("get", help="Get current host")
    host_get_parser.set_defaults(function=cmd_host_get)
    #

    # Pull
    pull = sub.add_parser(
        "pull",
        parents=[common_parser],
        help="Pulls resource data from the current host.",
    )
    pull.add_argument(
        "kind",
        choices=["es", "archive"],
        nargs="*",
        help="Kind of cache to pull. es - Elasticsearch Cache, archive - Archive Cache.",
    )
    pull.set_defaults(function=cmd_pull)

    # Cat
    cat = sub.add_parser(
        "cat",
        parents=[common_parser, viewer_command_parser],
        help="Show cached information.",
    )
    cat.add_argument("kind", choices=["repo", "snap", "index"])
    cat.set_defaults(function=cmd_cat2)

    # Repo sub command
    common_repo_parser = argparse.ArgumentParser(add_help=False)
    common_repo_parser.add_argument(
        "name", help="Name of repo or snapshot. <repo> or <repo>/<snapshot>"
    )

    repo = sub.add_parser("repo", parents=[common_parser], help="Repository commands.")

    repo_sub = repo.add_subparsers(required=True)

    repo_show_parser = repo_sub.add_parser(
        "show", parents=[common_parser, common_repo_parser, viewer_command_parser]
    )
    repo_show_parser.set_defaults(function=cmd_repo_show2)

    repo_create = repo_sub.add_parser(
        "create", parents=[common_parser, common_repo_parser, mutating_parser]
    )
    repo_create.add_argument("--type", default="fs")
    repo_create.add_argument("--location", required=True)
    repo_create.set_defaults(function=cmd_create_repo)

    repo_delete = repo_sub.add_parser(
        "delete",
        parents=[
            common_parser,
            common_repo_parser,
            mutating_parser,
            destructive_command_parser,
        ],
    )
    repo_delete.set_defaults(function=cmd_delete_repo)

    # Snapshot Sub Commands
    snap = sub.add_parser("snap", parents=[common_parser], help="Snapshot commands")
    snap_sub = snap.add_subparsers(required=True)

    # common snap parser
    common_snap_parser = argparse.ArgumentParser(add_help=False)
    common_snap_parser.add_argument(
        "name", help="Name to snapshot. must be <repo>/<snapshot>"
    )

    # common snapshot index parser
    common_snap_index_parser = argparse.ArgumentParser(add_help=False)
    common_snap_index_parser.add_argument(
        "--index",
        help="Index to add to the snapshot. * is allowed as a wildcard. Multiple indices allowed by comma separated.",
    )
    common_snap_index_parser.add_argument(
        "--include_global_state", default=False, action="store_true"
    )
    common_snap_index_parser.add_argument(
        "--ignore_unavailable", type=bool, default=True
    )

    snap_create = snap_sub.add_parser(
        "create",
        parents=[
            common_parser,
            common_snap_parser,
            common_snap_index_parser,
            mutating_parser,
        ],
    )
    snap_create.set_defaults(function=cmd_create_snapshot)

    snap_delete = snap_sub.add_parser(
        "delete",
        parents=[
            common_parser,
            common_snap_parser,
            mutating_parser,
            destructive_command_parser,
        ],
    )
    snap_delete.set_defaults(function=cmd_delete_snapshot)

    snap_restore = snap_sub.add_parser(
        "restore",
        parents=[
            common_parser,
            common_snap_parser,
            common_snap_index_parser,
            mutating_parser,
        ],
    )
    snap_restore.set_defaults(function=cmd_restore_snapshot)

    # Index commands
    common_index_parser = argparse.ArgumentParser(add_help=False)
    common_index_parser.add_argument("index")

    index_mapper_parser = argparse.ArgumentParser(add_help=False)
    index_mapper_parser.add_argument(
        "-m", "--mapping", help="Name of mapping in the config."
    )

    index_parser = sub.add_parser("index", help="Index commands.")
    index_sub = index_parser.add_subparsers(required=True)

    index_delete = index_sub.add_parser(
        "delete",
        parents=[
            common_parser,
            common_index_parser,
            mutating_parser,
            destructive_command_parser,
        ],
    )
    index_delete.set_defaults(function=cmd_delete_index)

    index_create = index_sub.add_parser(
        "create",
        parents=[
            common_parser,
            common_index_parser,
            index_mapper_parser,
            mutating_parser,
        ],
    )
    index_create.set_defaults(function=cmd_create_index)

    index_show = index_sub.add_parser(
        "show", parents=[common_parser, common_index_parser, viewer_command_parser]
    )
    index_show.set_defaults(function=cmd_show_index)

    index_status = index_sub.add_parser(
        "status", parents=[common_parser, common_index_parser, viewer_command_parser]
    )
    index_status.set_defaults(function=cmd_restore_status)

    # Reindex Commands
    reindex = sub.add_parser(
        "reindex",
        parents=[common_parser, index_mapper_parser, mutating_parser],
        help="Reindex command.",
    )
    reindex.add_argument(
        "src",
        help="Source index. it can be multiple by comma separated or * wild card can be used",
    )
    reindex.add_argument("dst", help="destination index")
    reindex.set_defaults(function=cmd_reindex)

    reindex_mapping = sub.add_parser(
        "mapping", help="Shows mappings in the config", parents=[common_parser]
    )
    reindex_mapping.set_defaults(function=cmd_reindex_mapping)

    task = sub.add_parser("task", help="Elasticsearch Task Commands")
    task_sub = task.add_subparsers(required=True)

    task_get = task_sub.add_parser(
        "get", help="Get task status on elasticsearch", parents=[common_parser]
    )
    task_get.add_argument("task_id", help="elasticsearch task id")
    task_get.set_defaults(function=cmd_get_task)

    # TODO: rsync is not currently operational
    rsync = sub.add_parser("rsync", parents=[common_parser])
    rsync.add_argument("config_name")

    job = sub.add_parser("job")

    job_sub = job.add_subparsers(required=True)
    job_list = job_sub.add_parser(
        "list", parents=[common_parser, viewer_command_parser]
    )
    job_list.add_argument(
        "--local",
        default=False,
        action="store_true",
        help="Show local jobs in .eskit/jobs generated by archive commands.",
    )
    job_list.set_defaults(function=cmd_list_job)

    job_show = job_sub.add_parser(
        "show", parents=[common_parser, viewer_command_parser]
    )
    job_show.add_argument(
        "job_search_id", help="Job search id / job output file name in the jobs cache"
    )
    job_show.set_defaults(function=cmd_read_job)

    status = sub.add_parser(
        "status", parents=[common_parser], help="Show current ESKit status."
    )
    status.set_defaults(function=cmd_status)

    archive_common_parser = argparse.ArgumentParser(add_help=False)
    archive_common_parser.add_argument("name", help="Name of the archive")

    archive_common_operation_parser = argparse.ArgumentParser(add_help=False)
    archive_common_operation_parser.add_argument(
        "--contents",
        default=False,
        action="store_true",
        help="Copy the contents of the archive directory into the destination, equivalent to using a trailing / on the rsync source path.",
    )
    archive_common_operation_parser.add_argument(
        "--preview",
        action="store_true",
        help="Execute internal commands such as rsync with dry-run mode.",
    )

    # Archive Command
    archive = sub.add_parser(
        "archive", parents=[common_parser], help="Archive commands."
    )

    archive_sub = archive.add_subparsers(required=True)

    archive_list_parser = archive_sub.add_parser(
        "list",
        parents=[common_parser, viewer_command_parser],
    )
    archive_list_parser.set_defaults(function=cmd_list_archive)

    archive_pull_parser = archive_sub.add_parser(
        "pull",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
        ],
    )
    archive_pull_parser.set_defaults(function=cmd_pull_archive)

    archive_sync_parser = archive_sub.add_parser(
        "sync",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
        ],
    )
    archive_sync_parser.set_defaults(function=cmd_sync_archive)

    archive_push_parser = archive_sub.add_parser(
        "push",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
        ],
    )
    archive_push_parser.add_argument(
        "--dst",
        required=True,
        help="Destination host. <eskit_host>:<path> can be used to target remote host. e.g. Host1:/home/user/data.",
    )
    archive_push_parser.set_defaults(function=cmd_push_archive)

    archive_show_parser = archive_sub.add_parser(
        "show", parents=[common_parser, viewer_command_parser, archive_common_parser]
    )
    archive_show_parser.set_defaults(function=cmd_show_archive)

    return p


def main():

    args = build_parser().parse_args()

    global job_manager
    job_manager = ESKitJobManager(CACHE_ROOT)

    from eskit.jobs.job_manager import init

    init(CACHE_ROOT)

    args.function(args)
    return
