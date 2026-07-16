#!/usr/bin/env python3
import argparse
import json
import logging
import shutil
from pathlib import Path
from venv import logger
from dataclasses import dataclass
from eskit.core.host import get_current_host_name
from eskit.version import __version__
from eskit.log import configure_logging
from eskit.exit_code import ExitCode
from eskit.result import ResultCode, Result
from eskit.resource_type import ResourceType
from eskit.render.projection import build_field_list
from eskit.render.renderer import render
from eskit.utils.paths import CACHE_ROOT, ensure_root, root_dir, DEMO_DIR
from eskit.version import __cache_version__
from eskit.utils.config import load_config
from eskit.config.types import Config
from eskit.error import ESKitError, ConfigNotFoundError, CurrentHostNotFoundError

DEFAULT_CONFIG = ".eskit/config.json"
CACHE_ROOT = Path(".eskit")
CURRENT_HOST = ".current_host"

logger = logging.getLogger("eskit")


@dataclass
class RenderOptions:
    output_format: str
    fields: str | None
    views: list[dict] | None
    flat: bool


@dataclass
class CommandContext:
    config: Config
    host: str | None
    render: RenderOptions


def print_dry_run():
    print("\n*Dry Run*\n")


def print_preview():
    print("\n*Preview*\n")


def print_host(host):
    print(f"\n=== ESKit HOST: {host} ===\n")


def get_current_host():
    with open(CACHE_ROOT / CURRENT_HOST, "r", encoding="utf-8") as f:
        for line in f:
            return line


def check_host_name(host):
    if host is None:
        # TODO: add HostNotFoundError error class
        raise SystemExit(
            "Host not found. Please specify the host or set the host by the host set command."
        )
    return


def load_command_context(args) -> CommandContext:

    config_path = getattr(args, "config", None)
    try:
        config = load_config(config_path)
    except FileNotFoundError as e:
        raise ConfigNotFoundError(args.config) from e

    host = args.host
    if not host:
        try:
            host = get_current_host()
        except FileNotFoundError as e:
            raise CurrentHostNotFoundError(str(CACHE_ROOT / CURRENT_HOST)) from e

    output_format = "table"
    if getattr(args, "json", False):
        output_format = "json"

    fields = getattr(args, "fields", None)

    views = getattr(args, "view", None)

    flat = getattr(args, "flat", False)

    context = CommandContext(
        config=config,
        host=host,
        render=RenderOptions(
            output_format=output_format, fields=fields, views=views, flat=flat
        ),
    )

    return context


def cmd_show_host(args):
    from eskit.core.host import get_host

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get_host(context.host, context.config)
    if result.success:
        fields = build_field_list(
            view_config=context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
        return ExitCode.SUCCESS

    if result.code == ResultCode.NOT_FOUND:

        resouce = "host"
        name = context.host
        target = result.get_resource_target()

        if target:
            resouce = target.resource
            name = target.name

        logger.error(
            "Resource:%s Name:%s not found.",
            resouce,
            name,
        )

    elif result.code == ResultCode.INVALID_ARGUMENT:
        argument = result.get_argument()
        if argument:
            logger.error(
                "Invalid argument name:%s valiue:%s", argument.name, argument.value
            )
        else:
            logger.error("Invalid argument.")

    else:
        logger.error("Failed to get host:%s", result.message)
    return ExitCode.FAILURE


def cmd_set_host(args):
    from eskit.core.host import set_current_host_name

    host = args.host
    result = set_current_host_name(host)

    if result.success:
        if args.json:
            print(json.dumps(result.value, indent=2))
        else:
            if result.value:
                host = result.value["host"]
            print(f"Current host set to: {host}")
        return ExitCode.SUCCESS

    logger.error("Failed to set host:%s", result.message)
    return ExitCode.FAILURE


def cmd_get_host(args):
    host_name = get_current_host_name()

    if host_name:
        if args.json:
            print(json.dumps({"name": host_name}, indent=2))
        else:
            print(f"Current host: {host_name}")
        return ExitCode.SUCCESS

    logger.error("No current host set.")
    return ExitCode.FAILURE


def cmd_list_job(args):
    from eskit.core.job import get_list

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get_list(context.host, args.local)

    if result.success:
        fields = build_field_list(
            view_config=context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
        # print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    logger.error("Failed to list jobs.")
    return ExitCode.FAILURE


def cmd_read_job(args):

    from eskit.core.job import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get(context.host, args.job_search_id)

    if result.success:
        fields = build_field_list(
            view_config=context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
        return ExitCode.SUCCESS

    if result.code == ResultCode.NOT_FOUND:
        name = args.job_search_id

        logger.error("Job: %s not found.", name)
    else:
        logger.error("Failed to list jobs.")

    return ExitCode.FAILURE


def cmd_status(args):

    from eskit.core.status import get_status

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get_status(context.host, context.config)
    if result.success:
        fields = build_field_list(
            view_config=context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )

    return ExitCode.FAILURE


def cmd_pull(args):
    from eskit.core.metadata import pull_metadata

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = pull_metadata(context.config, context.host, args.kind)

    if result.success:
        print("Pulled metadata successfully for the current host.")
        return ExitCode.SUCCESS

    logger.error("Failed to pull metadata for the current host.")
    return ExitCode.FAILURE


def cmd_cat2(args):
    from eskit.core.metadata import get_metadata

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get_metadata(context.config, context.host, args.kind)

    if result.success:
        fields = build_field_list(
            view_config=context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
        # print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    resource = ResourceType.CACHE
    name = context.host

    logger.error(
        "Failed to get resource:%s for host:%s.",
        resource,
        name,
    )

    return ExitCode.FAILURE


def cmd_repo_show2(args):

    name = args.name

    from eskit.core.repo import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get(context.host, name)

    if result.success:
        fields = build_field_list(
            view_config=context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
        return ExitCode.SUCCESS

    logger.error("Repository:%s not found.", name)
    return ExitCode.FAILURE


def cmd_delete_repo(args):

    name = args.name
    dry_run = args.dry_run
    push = args.push
    force = args.force

    from eskit.core.repo import delete

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = delete(context.config, context.host, name, dry_run, push, force)

    if result.success:
        if not dry_run or (result.value and result.value["executed"]):
            print("Ropository deleted successfully.")
        else:
            print_dry_run()
            print_host(context.host)
            print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.CANCELED:
        print("Canceled.")
        return ExitCode.CANCELED

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Repository:%s not found.", name)
    else:
        logger.error("Failed to delete repository:%s.", name)
    return ExitCode.FAILURE


def cmd_create_repo(args):

    name = args.name
    dry_run = args.dry_run
    push = args.push
    repo_type = args.type
    location = args.location

    from eskit.core.repo import create

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = create(
        context.config, context.host, name, repo_type, location, dry_run, push
    )
    if result.success:
        if not dry_run or (result.value and result.value["executed"]):
            print("Ropository created successfully.")
        else:
            print_dry_run()
            print_host(context.host)
            print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.ALREADY_EXISTS:
        logger.error("Repository:%s already exists.", name)
    else:
        logger.error("Failed to create repository:%s", name)
    return ExitCode.FAILURE


def cmd_reindex_mapping(args):
    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE
    print(json.dumps(context.config["reindex_configs"], indent=2))


def cmd_create_snapshot(args):

    from eskit.core.snap import create

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE
    name = args.name
    result = create(
        context.config,
        context.host,
        name,
        args.index,
        args.include_global_state,
        args.ignore_unavailable,
        args.dry_run,
        args.push,
    )
    host_name = args.host
    dry_run = args.dry_run
    if result.success:
        if not dry_run or (result.value and result.value["executed"]):
            print("Snapshot creation started successfully.")
            print(
                "Please check status of the snapshot by updating the cache with eskit pull."
            )
        else:
            print_dry_run()
            if host_name is None:
                host_name = get_current_host_name()
            print_host(host_name)
            print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.INVALID_ARGUMENT:
        argument = result.get_argument()
        if argument:
            logger.error(
                "Invalid argument name:%s value:%s", argument.name, argument.value
            )
            logger.error(
                "Please make sure the snapshot name include repository name. <repository>/<name>."
            )
        else:
            logger.error("Invalid argument.")
    elif result.code == ResultCode.ALREADY_EXISTS:
        logger.error("Snapshot:%s already exists.", name)

    return ExitCode.FAILURE


def cmd_delete_snapshot(args):

    from eskit.core.snap import delete

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE
    name = args.name
    result = delete(
        context.config, context.host, name, args.dry_run, args.push, args.force
    )
    host_name = args.host
    dry_run = args.dry_run
    if result.success:
        if not dry_run or (result.value and result.value["executed"]):
            print("Snapshot deleted.")
        else:
            print_dry_run()
            if host_name is None:
                host_name = get_current_host_name()
            print_host(host_name)
            print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.CANCELED:
        print("Canceled.")
        return ExitCode.CANCELED

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Snapshot:%s not found.", name)
    else:
        logger.error("Failed to delete snapshot.")

    logger.error(
        "Please make sure the snapshot name include repository name. <repository>/<name>."
    )
    return ExitCode.FAILURE


def cmd_restore_snapshot(args):

    from eskit.core.snap import restore

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE
    host_name = args.host
    dry_run = args.dry_run
    name = args.name
    result = restore(
        context.config, context.host, name, args.index, args.dry_run, args.push
    )

    if result.success:
        if not dry_run or (result.value and result.value["executed"]):
            print("Restore started.")
            print(
                "Please check the status of restore index by updating the cache with eskit pull."
            )
        else:
            print_dry_run()
            print_host(host_name)
            print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    logger.error("Failed to restore snapshot:%s", name)
    return ExitCode.FAILURE


def cmd_restore_status(args):

    from eskit.core.index import status

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE
    index = args.index
    result = status(context.config, context.host, index)

    if result.success:
        fields = build_field_list(
            view_config=context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            value=result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
    else:
        logger.error("Failed to get restore status for index:%s", index)


def cmd_delete_index(args):

    from eskit.core.index import delete

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    host_name = args.host
    dry_run = args.dry_run
    index = args.index

    result = delete(
        context.config, context.host, args.index, args.dry_run, args.push, args.force
    )

    if result.success:
        if not dry_run or (result.value and result.value["executed"]):
            print(f"Index:{index} deleted.")
        else:
            print_dry_run()
            print_host(host_name)
            print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.CANCELED:
        print("Canceled.")
        return ExitCode.CANCELED

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Index:%s not found.", index)
    else:
        logger.error("Failed to delete index:%s", index)

    return ExitCode.FAILURE


def cmd_create_index(args):

    from eskit.core.index import create

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    host_name = args.host
    dry_run = args.dry_run
    index = args.index

    result = create(
        context.config, context.host, args.index, args.mapping, args.dry_run, args.push
    )

    if result.success:
        if not dry_run or (result.value and result.value["executed"]):
            print("Index created successfully.")
        else:
            print_dry_run()
            print_host(host_name)
            print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.ALREADY_EXISTS:
        logger.error("Index:%s already exists.", index)

    return ExitCode.FAILURE


def cmd_show_index(args):

    index = args.index

    from eskit.core.index import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get(context.config, context.host, index)

    if result.success:
        fields = build_field_list(
            context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
        return ExitCode.SUCCESS

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Index:%s not found.", index)

    logger.error("Failed to get index:%s.", index)
    return ExitCode.FAILURE


def cmd_reindex(args):

    from eskit.core.index import reindex

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    src_index = args.src
    dst_index = args.dst
    result = reindex(
        context.config,
        context.host,
        src_index,
        dst_index,
        args.mapping,
        args.dry_run,
        args.push,
    )

    if result.success:
        logger.info("Reindex started successfully.")
        print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.ALREADY_EXISTS:
        logger.error("Index:%s already exists.", dst_index)
        if args.mapping:
            logger.error("Mapping cannot be changed on existing index.")
    else:
        logger.error("Failed to create job.")
        if result.value:
            print(json.dumps(result.value, indent=2))

    return ExitCode.FAILURE


def cmd_get_task(args):
    from eskit.core.task import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    task_id = args.task_id
    result = get(context.config, context.host, task_id)
    if result.success:
        print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS
    else:
        logger.error("Task:%s not found.", task_id)
        return ExitCode.FAILURE


def _init(is_demo):

    if CACHE_ROOT.exists():
        return Result.fail(
            ResultCode.ALREADY_EXISTS,
            "The cache folder already exists.",
            context={"resource": ResourceType.CACHE, "name": ".eskit"},
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


def cmd_init(args):

    result = _init(args.demo)
    if result.success:
        print("ESKit initialized.")
        if args.demo:
            print("Demo folder copied.")
        return ExitCode.SUCCESS

    if result.code == ResultCode.ALREADY_EXISTS:
        logger.error(".eskit folder already exists.")
        if args.demo:
            logger.error("If you want to reset demo, please remove the folder first.")
    else:
        logger.error("Failed to initialize ESKit.")
    return ExitCode.FAILURE


def cmd_list_archive(args):

    from eskit.core.archive import get_list

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get_list(context.host)

    if result.success:
        fields = build_field_list(
            context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        print(context.render.output_format)
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
        return ExitCode.SUCCESS

    logger.error("Failed to get archive list.")
    return ExitCode.FAILURE


def cmd_pull_archive(args):
    from eskit.core.archive import pull

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    host_name = args.host
    dry_run = args.dry_run
    preview = args.preview
    name = args.name
    contents = args.contents

    result = pull(
        context.config,
        context.host,
        name,
        contents,
        dry_run,
        False,
        False,
        preview,
    )

    if result.success:

        if not (dry_run or preview) or (result.value and result.value.get("executed")):
            pass
        else:
            if host_name is None:
                host_name = get_current_host_name()
            if dry_run:
                print_dry_run()
                print_host(host_name)
            if preview:
                print_preview()
                print_host(host_name)

        print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Archive:%s not found.", name)
    else:
        logger.error("Failed to pull archive:%s", result.message)

    return ExitCode.FAILURE


def cmd_sync_archive(args):
    from eskit.core.archive import pull

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    host_name = context.host
    dry_run = args.dry_run
    preview = args.preview
    name = args.name
    contents = args.contents

    result = pull(
        context.config,
        host_name,
        name,
        contents,
        dry_run,
        False,
        True,
        preview,
    )

    if result.success:
        if not (dry_run or preview) or (result.value and result.value.get("executed")):
            pass
        else:
            if dry_run:
                print_dry_run()
                print_host(host_name)
            if preview:
                print_preview()
                print_host(host_name)

        print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Archive:%s not found.", name)
    else:
        logger.error("Failed to sync archive:%s", result.message)

    return ExitCode.FAILURE


def cmd_push_archive(args):
    from eskit.core.archive import push

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = push(
        context.config,
        context.host,
        args.name,
        args.dst,
        args.contents,
        args.dry_run,
        args.preview,
    )
    host_name = args.host
    dry_run = args.dry_run
    preview = args.preview
    name = args.name
    if result.success:

        if not (dry_run or preview) or (result.value and result.value.get("executed")):
            pass
        else:
            if host_name is None:
                host_name = get_current_host_name()
            if dry_run:
                print_dry_run()
                print_host(host_name)
            if preview:
                print_preview()
                print_host(host_name)

        print(json.dumps(result.value, indent=2))
        return ExitCode.SUCCESS

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Archive:%s not found.", name)
    else:
        logger.error("Failed to push archive:%s", result.message)

    return ExitCode.FAILURE


def cmd_show_archive(args):
    from eskit.core.archive import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return ExitCode.FAILURE

    result = get(context.host, args.name)

    if result.success:
        fields = build_field_list(
            context.config["views"],
            views=context.render.views,
            fields=context.render.fields,
        )
        render(
            result.value,
            output_format=context.render.output_format,
            fields=fields,
            flatten=context.render.flat,
        )
        return ExitCode.SUCCESS

    logger.error("Failed to get archive:%s", result.message)
    return ExitCode.FAILURE


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

    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    output_parser.add_argument(
        "-d", "--debug", action="store_true", help="Enable debug logging"
    )
    output_parser.add_argument(
        "-j", "--json", action="store_true", help="Output in JSON format"
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
    init = sub.add_parser("init", help="Initializes ESKit.", parents=[output_parser])
    init.set_defaults(function=cmd_init)
    init.add_argument(
        "--demo", action="store_true", help="Initialize with demo data set"
    )

    # Host commands
    host_parser = sub.add_parser("host", help="Host related commands.")
    host_parser_sub = host_parser.add_subparsers(required=True)

    host_show_parser = host_parser_sub.add_parser(
        "show",
        parents=[common_parser, output_parser, viewer_command_parser],
        help="Show available hosts in the config",
    )
    host_show_parser.set_defaults(function=cmd_show_host)

    host_set_parser = host_parser_sub.add_parser(
        "set", parents=[output_parser], help="Set as current host"
    )
    host_set_parser.add_argument("host")
    host_set_parser.set_defaults(function=cmd_set_host)

    host_get_parser = host_parser_sub.add_parser(
        "get", parents=[output_parser], help="Get current host"
    )
    host_get_parser.set_defaults(function=cmd_get_host)
    #

    # Pull
    pull = sub.add_parser(
        "pull",
        parents=[common_parser, output_parser],
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
        parents=[common_parser, viewer_command_parser, output_parser],
        help="Show cached information.",
    )
    cat.add_argument("kind", choices=["repo", "snap", "index"])
    cat.set_defaults(function=cmd_cat2)

    # Repo sub command
    common_repo_parser = argparse.ArgumentParser(add_help=False)
    common_repo_parser.add_argument(
        "name", help="Name of repo or snapshot. <repo> or <repo>/<snapshot>"
    )

    repo = sub.add_parser(
        "repo", parents=[common_parser, output_parser], help="Repository commands."
    )

    repo_sub = repo.add_subparsers(required=True)

    repo_show_parser = repo_sub.add_parser(
        "show",
        parents=[
            common_parser,
            common_repo_parser,
            viewer_command_parser,
            output_parser,
        ],
    )
    repo_show_parser.set_defaults(function=cmd_repo_show2)

    repo_create = repo_sub.add_parser(
        "create",
        parents=[common_parser, common_repo_parser, mutating_parser, output_parser],
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
    snap = sub.add_parser(
        "snap", parents=[common_parser, output_parser], help="Snapshot commands"
    )
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
            output_parser,
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
            output_parser,
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
            output_parser,
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
            output_parser,
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
            output_parser,
        ],
    )
    index_create.set_defaults(function=cmd_create_index)

    index_show = index_sub.add_parser(
        "show",
        parents=[
            common_parser,
            common_index_parser,
            viewer_command_parser,
            output_parser,
        ],
    )
    index_show.set_defaults(function=cmd_show_index)

    index_status = index_sub.add_parser(
        "status",
        parents=[
            common_parser,
            common_index_parser,
            viewer_command_parser,
            output_parser,
        ],
    )
    index_status.set_defaults(function=cmd_restore_status)

    # Reindex Commands
    reindex = sub.add_parser(
        "reindex",
        parents=[common_parser, index_mapper_parser, mutating_parser, output_parser],
        help="Reindex command.",
    )
    reindex.add_argument(
        "src",
        help="Source index. it can be multiple by comma separated or * wild card can be used",
    )
    reindex.add_argument("dst", help="destination index")
    reindex.set_defaults(function=cmd_reindex)

    reindex_mapping = sub.add_parser(
        "mapping",
        help="Shows mappings in the config",
        parents=[common_parser, output_parser],
    )
    reindex_mapping.set_defaults(function=cmd_reindex_mapping)

    task = sub.add_parser("task", help="Elasticsearch Task Commands")
    task_sub = task.add_subparsers(required=True)

    task_get = task_sub.add_parser(
        "get",
        help="Get task status on elasticsearch",
        parents=[common_parser, output_parser],
    )
    task_get.add_argument("task_id", help="elasticsearch task id")
    task_get.set_defaults(function=cmd_get_task)

    job = sub.add_parser("job")

    job_sub = job.add_subparsers(required=True)
    job_list = job_sub.add_parser(
        "list", parents=[common_parser, viewer_command_parser, output_parser]
    )
    job_list.add_argument(
        "--local",
        default=False,
        action="store_true",
        help="Show local jobs in .eskit/jobs generated by archive commands.",
    )
    job_list.set_defaults(function=cmd_list_job)

    job_show = job_sub.add_parser(
        "show", parents=[common_parser, viewer_command_parser, output_parser]
    )
    job_show.add_argument(
        "job_search_id", help="Job search id / job output file name in the jobs cache"
    )
    job_show.set_defaults(function=cmd_read_job)

    status = sub.add_parser(
        "status",
        parents=[common_parser, output_parser, viewer_command_parser],
        help="Show current ESKit status.",
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
        "archive", parents=[common_parser, output_parser], help="Archive commands."
    )

    archive_sub = archive.add_subparsers(required=True)

    archive_list_parser = archive_sub.add_parser(
        "list",
        parents=[common_parser, viewer_command_parser, output_parser],
    )
    archive_list_parser.set_defaults(function=cmd_list_archive)

    archive_pull_parser = archive_sub.add_parser(
        "pull",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
            output_parser,
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
            output_parser,
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
            output_parser,
        ],
    )
    archive_push_parser.add_argument(
        "--dst",
        required=True,
        help="Destination host. <eskit_host>:<path> can be used to target remote host. e.g. Host1:/home/user/data.",
    )
    archive_push_parser.set_defaults(function=cmd_push_archive)

    archive_show_parser = archive_sub.add_parser(
        "show",
        parents=[
            common_parser,
            viewer_command_parser,
            archive_common_parser,
            output_parser,
        ],
    )
    archive_show_parser.set_defaults(function=cmd_show_archive)

    return p


def main():

    args = build_parser().parse_args()

    from eskit.jobs.job_manager import init

    init(CACHE_ROOT)

    configure_logging(args.verbose, args.debug)

    return args.function(args)
