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
from eskit.result import ResultCode, Result, result_to_ai_response
from eskit.resource_type import ResourceType
from eskit.utils.paths import CACHE_ROOT, ensure_root, root_dir, DEMO_DIR
from eskit.version import __cache_format_version__
from eskit.utils.config import load_config
from eskit.config.types import Config
from eskit.error import ESKitError, ConfigNotFoundError, CurrentHostNotFoundError
from eskit.cache.store import check_cache_version
from eskit.command.builder import describe_parser
from eskit.utils.input import confirm_delete

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
    command: str
    dry_run: bool


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


def load_command_context(args, skip_get_current_host=False) -> CommandContext:

    config: Config = {
        "hosts": [],
        "views": {},
        "reindex-configs": [],
    }
    config_path = getattr(args, "config", None)
    if config_path:
        try:
            config = load_config(config_path)
        except FileNotFoundError as e:
            raise ConfigNotFoundError(args.config) from e

    host = getattr(args, "host", "")
    if not skip_get_current_host:
        if not host:
            try:
                host = get_current_host()
            except FileNotFoundError as e:
                raise CurrentHostNotFoundError(str(CACHE_ROOT / CURRENT_HOST)) from e

    output_format = "table"
    projection_supported = False
    if getattr(args, "json", False):
        output_format = "json"
        projection_supported = True

    fields = getattr(args, "fields", None)
    views = getattr(args, "view", None)
    flat = getattr(args, "flat", False)

    if not projection_supported and (fields or views or flat):
        fields = None
        views = None
        flat = False
        logger.warning(
            "Warning: --fields and --view are only supported with --json and have been ignored."
        )

    dry_run = getattr(args, "dry_run", False)

    context = CommandContext(
        config=config,
        host=host,
        render=RenderOptions(
            output_format=output_format, fields=fields, views=views, flat=flat
        ),
        command=args.function.__name__,
        dry_run=dry_run,
    )

    return context


def cmd_show_host(args):
    from eskit.core.host import get_host

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = get_host(context.host, context.config)
    result.command_context = context

    if result.code == ResultCode.SUCCESS:
        return result

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

    return result


def cmd_set_host(args):
    from eskit.core.host import set_current_host_name

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    host = args.host
    result = set_current_host_name(host)
    result.command_context = context

    if result.success:
        return result

    logger.error("Failed to set host:%s", result.message)
    return result


def cmd_get_host(args):

    try:
        context = load_command_context(args, skip_get_current_host=True)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = get_current_host_name()
    result.command_context = context

    if result.success:
        return result

    logger.error("No current host set.")
    return result


def cmd_list_jobs(args):
    from eskit.core.job import get_list

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = get_list(context.host, args.local)
    result.command_context = context

    if result.success:
        # print(json.dumps(result.value, indent=2))
        return result

    logger.error("Failed to list jobs.")
    return result


def cmd_read_job(args):

    from eskit.core.job import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = get(context.host, args.job_search_id)
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        name = args.job_search_id

        logger.error("Job: %s not found.", name)
    else:
        logger.error("Failed to list jobs.")

    return result


def cmd_status(args):

    from eskit.core.status import get_status

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = get_status(context.host, context.config)
    result.command_context = context

    return result


def cmd_pull(args):
    from eskit.core.metadata import pull_metadata

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = pull_metadata(context.config, context.host, args.kind)
    result.command_context = context

    if result.success:
        return result

    logger.error("Failed to pull metadata for the current host.")
    return result


def cmd_cat2(args):
    from eskit.core.metadata import get_metadata

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    if not check_cache_version(context.host):
        logger.warning(
            "Cache format version doesn't match. Please pull the cache again."
        )

    result = get_metadata(context.host, args.kind)
    result.command_context = context

    mapping = {
        "repo": "cat_repository",
        "snap": "cat_snapshot",
        "index": "cat_index",
        "ilm": "cat_ilm",
    }
    cmd = mapping[args.kind]
    result.command_context.command = cmd

    if result.success:
        return result

    resource = ResourceType.CACHE
    name = context.host

    logger.error(
        "Failed to get resource:%s for host:%s.",
        resource,
        name,
    )

    return result


def cmd_repo_show2(args):

    name = args.name

    from eskit.core.repo import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = get(context.host, name)
    result.command_context = context

    if result.success:
        cmd = "show_repository"

        result_context = result.context
        if result_context and result_context["resource_type"] == ResourceType.SNAPSHOT:
            cmd = "show_snapshot"

        result.command_context.command = cmd
        return result

    logger.error("Repository:%s not found.", name)
    return result


def cmd_snap_show(args):

    name = args.name
    repo, sep, snap = name.partition("/")

    if not (repo and snap):
        logger.error("Snapshot name needs to be in format of <repository>/<snapshot>.")
        return Result.fail(
            ResultCode.INVALID_ARGUMENT,
            "Snapshot name needs to be in format of <repository>/<snapshot>.",
        )

    return cmd_repo_show2(args)


def cmd_delete_repo(args):

    name = args.name
    dry_run = args.dry_run
    force = args.force

    from eskit.core.repo import delete

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    confirmed = False
    if not args.force and not args.dry_run:
        confirmed = confirm_delete("repository", name)

    result = delete(context.config, context.host, name, dry_run, force, confirmed)
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Repository:%s not found.", name)
    else:
        logger.error("Failed to delete repository:%s.", name)
    return result


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
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = create(context.config, context.host, name, repo_type, location, dry_run)
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.ALREADY_EXISTS:
        logger.error("Repository:%s already exists.", name)
    else:
        logger.error("Failed to create repository:%s", name)
    return result


def cmd_reindex_mapping(args):
    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = Result.ok(context.config["reindex-configs"])
    result.command_context = context

    return result


def cmd_create_snapshot(args):

    from eskit.core.snap import create

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    name = args.name
    result = create(
        context.config,
        context.host,
        name,
        args.index,
        args.include_global_state,
        args.ignore_unavailable,
        args.dry_run,
        args.wait,
    )
    result.command_context = context

    if result.success:
        return result

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

    return result


def cmd_delete_snapshot(args):

    from eskit.core.snap import delete

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    name = args.name

    confirmed = False
    if not args.force and not args.dry_run:
        confirmed = confirm_delete("snapshot", name)

    result = delete(
        context.config, context.host, name, args.dry_run, args.force, confirmed
    )
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Snapshot:%s not found.", name)
    else:
        logger.error("Failed to delete snapshot.")

    logger.error(
        "Please make sure the snapshot name include repository name. <repository>/<name>."
    )
    return result


def cmd_restore_snapshot(args):

    from eskit.core.snap import restore

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    name = args.name

    result = restore(
        context.config,
        context.host,
        name,
        args.index,
        args.dry_run,
        args.ilm,
        args.remove_ilm,
        args.wait,
    )
    result.command_context = context

    if result.success:
        return result

    logger.error("Failed to restore snapshot:%s", name)
    return result


def cmd_restore_status(args):

    from eskit.core.index import status

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    index = args.index
    result = status(context.config, context.host, index)
    result.command_context = context

    if result.success:
        return result
    else:
        logger.error("Failed to get restore status for index:%s", index)

    return result


def cmd_delete_index(args):

    from eskit.core.index import delete

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    index = args.index

    confirmed = False
    if not args.force and not args.dry_run:
        confirmed = confirm_delete("index", args.index)

    result = delete(
        context.config, context.host, args.index, args.dry_run, args.force, confirmed
    )
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Index:%s not found.", index)
    else:
        logger.error("Failed to delete index:%s", index)

    return result


def cmd_create_index(args):

    from eskit.core.index import create

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    index = args.index

    result = create(
        context.config, context.host, args.index, args.mapping, args.dry_run
    )
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.ALREADY_EXISTS:
        logger.error("Index:%s already exists.", index)

    return result


def cmd_show_index(args):

    index = args.index

    from eskit.core.index import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = get(context.config, context.host, index)
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Index:%s not found.", index)

    logger.error("Failed to get index:%s.", index)
    return result


def cmd_reindex(args):

    from eskit.core.index import reindex

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    src_index = args.src
    dst_index = args.dst
    result = reindex(
        context.config,
        context.host,
        src_index,
        dst_index,
        args.mapping,
        args.dry_run,
    )
    result.command_context = context

    if result.success:
        logger.info("Reindex started successfully.")
        return result

    if result.code == ResultCode.ALREADY_EXISTS:
        logger.error("Index:%s already exists.", dst_index)
        if args.mapping:
            logger.error("Mapping cannot be changed on existing index.")
    else:
        logger.error("Failed to create job.")
        if result.value:
            print(json.dumps(result.value, indent=2))

    return result


def cmd_get_task(args):
    from eskit.core.task import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    task_id = args.task_id
    result = get(context.config, context.host, task_id)
    result.command_context = context

    if result.success:
        return result
    else:
        logger.error("Task:%s not found.", task_id)
        return result


def _init(args, is_demo):

    try:
        context = load_command_context(args, skip_get_current_host=True)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

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
            f"{DEMO_DIR}/{__cache_format_version__}", root_dir(), dirs_exist_ok=True
        )
        # print(f"demo/{__cache_format_version__} copied to .eskit folder.")

    result = Result.ok(
        value={"resource": ResourceType.CACHE, "name": config_path, "demo": is_demo},
        command_context=context,
    )

    return result


def cmd_init(args):

    result = _init(args, args.demo)
    if result.success:
        return result

    if result.code == ResultCode.ALREADY_EXISTS:
        logger.error(".eskit folder already exists.")
        if args.demo:
            logger.error("If you want to reset demo, please remove the folder first.")
    else:
        logger.error("Failed to initialize ESKit.")
    return result


def cmd_list_archives(args):

    from eskit.core.archive import get_list

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = get_list(context.host)
    result.command_context = context

    if result.success:
        return result

    logger.error("Failed to get archive list.")
    return result


def cmd_pull_archive(args):
    from eskit.core.archive import pull

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

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
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Archive:%s not found.", name)
    else:
        logger.error("Failed to pull archive:%s", result.message)

    return result


def cmd_sync_archive(args):
    from eskit.core.archive import pull

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

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
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Archive:%s not found.", name)
    else:
        logger.error("Failed to sync archive:%s", result.message)

    return result


def cmd_push_archive(args):
    from eskit.core.archive import push

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    result = push(
        context.config,
        context.host,
        args.name,
        args.dst,
        args.contents,
        args.dry_run,
        args.preview,
    )
    result.command_context = context

    name = args.name
    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Archive:%s not found.", name)
    else:
        logger.error("Failed to push archive:%s", result.message)

    return result


def cmd_show_archive(args):
    from eskit.core.archive import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    archive_name = args.name
    result = get(context.host, archive_name)
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        logger.error("Archive %s not found.", archive_name)
    else:
        logger.error("Failed to get archive:%s", result.message)
    return result


def cmd_show_ilm(args):
    from eskit.core.ilm import get

    try:
        context = load_command_context(args)
    except ESKitError as e:
        logger.error("%s", e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to load context.")

    ilm_name = args.name
    result = get(context.host, ilm_name)
    result.command_context = context

    if result.success:
        return result

    if result.code == ResultCode.NOT_FOUND:
        result_ctx = result.context
        if result_ctx:
            resource_type = result_ctx["resource_type"]
            if resource_type == ResourceType.CACHE:
                logger.error("ILM cache not found. Please pull.")
        logger.error("ILM %s not found.", ilm_name)
    else:
        logger.error("Failed to get archive:%s", result.message)

    return result


def execute_command(tool_call, tools):

    parser = build_parser()
    command_ir = describe_parser(parser)

    if tool_call:

        from eskit.ai.tool import to_argparse

        args = to_argparse(tool_call, command_ir["commands"], tools)
        # print("args:", args)

        parsed_args = parser.parse_args(args)

        return result_to_ai_response(parsed_args.function(parsed_args))

    return result_to_ai_response(
        Result.fail(code=ResultCode.INTERNAL_ERROR, message="failed to execute tool.")
    )


def cmd_ai(args):

    parser = build_parser()

    command_ir = describe_parser(parser)

    from eskit.command.passes import (
        run_passes,
        RemoveUnnecessaryFields,
        DeduplicateCommonArgs,
    )

    passes = [
        RemoveUnnecessaryFields(),
        DeduplicateCommonArgs(),
    ]

    optimized_command_ir = run_passes(command_ir, passes)

    from eskit.ai.tool import build_tool_definitions, tools_to_json

    tools = build_tool_definitions(optimized_command_ir)

    if args.output_command_json:
        with open("tools.json", "w", encoding="UTF-8") as f:
            f.write(tools_to_json(tools))

    if args.output_command_json:
        with open(args.output_command_json, "w", encoding="UTF-8") as f:
            json.dump(command_ir, f)

    from eskit.ai.helper import run_agent

    result = run_agent(
        question=args.question,
        command_description=optimized_command_ir,
        model=args.model,
        tools=tools,
        executor=execute_command,
    )

    print(result)

    return ExitCode.SUCCESS


def cmd_describe(args):

    parser = build_parser()

    command_json = describe_parser(parser)

    with open("command_ir_raw.json", "w", encoding="UTF-8") as f:
        json.dump(command_json, f)

    from eskit.command.passes import (
        run_passes,
        RemoveUnnecessaryFields,
        DeduplicateCommonArgs,
    )

    passes = [
        RemoveUnnecessaryFields(),
        DeduplicateCommonArgs(),
    ]

    command_json = run_passes(command_json, passes)

    with open("command_ir.json", "w", encoding="UTF-8") as f:
        json.dump(command_json, f)

    return Result.ok("JSON files created.")

    # from eskit.ai.tool import build_tool_definitions, tools_to_json

    # tools = build_tool_definitions(command_json)

    # with open("tools.json", "w", encoding="UTF-8") as f:
    #     f.write(tools_to_json(tools))


def cmd_root(args):
    if args.version:
        print(__version__)
    else:
        print("Please use -h/--help for more information.")


def serialize_default(value):
    if callable(value):
        return value.__name__
    return value


def set_metadata(parser, **metadata):
    parser._eskit_metadata = metadata
    return parser


def build_parser():
    p = argparse.ArgumentParser(
        prog="eskit",
        description="a light-weight Elasticsearch toolkit for managing repo, snapshots, and index.",
    )

    p.add_argument("--version", action="store_true", help="Show help")
    p.set_defaults(function=cmd_root)

    # common parsers
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_CONFIG,
        help="Set config file. Optional as default value is .eskit/config.json",
        type=str,
    )
    common_parser.add_argument(
        "--host",
        help="Specify which host to operate. Optional if found in .current_host file.",
        type=str,
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

    # Destructive Operation common
    destructive_command_parser = argparse.ArgumentParser(add_help=False)
    destructive_command_parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Administrative override for safety checks. Use only when the user explicitly requests --force. Do not use it as a substitute for user confirmation."
        ),
    )

    # common viewer
    viewer_command_parser = argparse.ArgumentParser(add_help=False)
    viewer_command_parser.add_argument(
        "--view",
        action="append",
        default=[],
        type=str,
        help="Name of view defined in the config.",
    )
    viewer_command_parser.add_argument(
        "--fields",
        type=str,
        help="Fields to retrieve the data in a dictionary. e.g.  settings.index.provided_name as settings['index']['provided_name']",
    )
    viewer_command_parser.add_argument("--flat", action="store_true")

    sub = p.add_subparsers(dest="command")

    # Init command
    init = sub.add_parser(
        "init",
        help="Initializes ESKit.",
        parents=[output_parser],
        description="Initializes ESKit",
    )
    init.set_defaults(function=cmd_init)
    init.add_argument(
        "--demo", action="store_true", help="Initialize with demo data set."
    )

    # Host commands
    host_parser = sub.add_parser(
        "host", help="Host related commands.", description="Host data related commands."
    )
    host_parser_sub = host_parser.add_subparsers(required=True)

    host_show_parser = host_parser_sub.add_parser(
        "show",
        parents=[common_parser, output_parser, viewer_command_parser],
        help="Show available hosts in the config",
        description="Show available hosts in the config",
    )
    host_show_parser.set_defaults(function=cmd_show_host)

    set_metadata(
        host_show_parser,
        risk="read",
    )

    host_set_parser = host_parser_sub.add_parser(
        "set",
        parents=[output_parser],
        help="Set the given host as current host",
        description="Set the given host as current host",
    )
    host_set_parser.add_argument("host", help="Host name", type=str)
    host_set_parser.set_defaults(function=cmd_set_host)
    set_metadata(cmd_set_host, risk="write")

    host_get_parser = host_parser_sub.add_parser(
        "get",
        parents=[output_parser],
        help="Get the current host",
        description="Get the current host",
    )
    host_get_parser.set_defaults(function=cmd_get_host)
    set_metadata(host_get_parser, risk="read")

    #

    # Pull
    pull = sub.add_parser(
        "pull",
        parents=[common_parser, output_parser],
        help="Pulls resource data from the current host into cache.",
        description="Pulls resource data from the current host into cache.",
    )
    pull.add_argument(
        "kind",
        choices=["es", "archive"],
        nargs="*",
        help="Optional kind of cache to pull. es - Elasticsearch Cache, archive - Archive Cache. If omitted, all types are pulled.",
        type=str,
    )
    pull.set_defaults(function=cmd_pull)
    set_metadata(pull, risk="write")

    # Cat
    cat = sub.add_parser(
        "cat",
        parents=[common_parser, viewer_command_parser, output_parser],
        help="Show cached information.",
        description="Show cached information.",
    )
    cat.add_argument("kind", choices=["repo", "snap", "index", "ilm"], type=str)
    cat.set_defaults(function=cmd_cat2)

    set_metadata(
        cat,
        risk="read",
    )

    # Repo sub command
    common_repo_parser = argparse.ArgumentParser(add_help=False)
    common_repo_parser.add_argument(
        "name", help="Name of repo or snapshot. <repo> or <repo>/<snapshot>", type=str
    )

    repo = sub.add_parser(
        "repo",
        help="Repository commands.",
        description="Repository commands.",
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
        help="Show repository detials.",
        description="Show repository details.",
    )
    repo_show_parser.set_defaults(function=cmd_repo_show2)

    set_metadata(
        repo_show_parser,
        risk="read",
    )

    repo_create = repo_sub.add_parser(
        "create",
        parents=[common_parser, common_repo_parser, mutating_parser, output_parser],
        help="Create repository.",
        description="Create repository.",
    )
    repo_create.add_argument(
        "--type", default="fs", help="Type of repository. e.g. fs", type=str
    )
    repo_create.add_argument(
        "--location",
        required=True,
        help="Location of the repository to be created. A path to a folder.",
        type=str,
    )
    repo_create.set_defaults(function=cmd_create_repo)

    set_metadata(
        repo_create,
        risk="write",
    )

    repo_delete = repo_sub.add_parser(
        "delete",
        parents=[
            common_parser,
            common_repo_parser,
            mutating_parser,
            destructive_command_parser,
        ],
        help="Delete repository.",
        description="Delete repository.",
    )
    repo_delete.set_defaults(function=cmd_delete_repo)

    set_metadata(
        repo_delete,
        risk="destructive",
        confirmation=("The user must explicitly confirm the action before execution."),
    )

    # Snapshot Sub Commands
    snap = sub.add_parser(
        "snap",
        help="Snapshot commands",
        description="Snapshot commands",
    )
    snap_sub = snap.add_subparsers(required=True)

    # common snap parser
    common_snap_parser = argparse.ArgumentParser(add_help=False)
    common_snap_parser.add_argument(
        "name", help="Name to snapshot. must be <repo>/<snapshot>", type=str
    )

    # common snapshot index parser
    common_snap_index_parser = argparse.ArgumentParser(add_help=False)
    common_snap_index_parser.add_argument(
        "--index",
        help="Index to add to the snapshot. * is allowed as a wildcard. Multiple indices allowed by comma separated.",
        type=str,
    )
    common_snap_index_parser.add_argument(
        "--include_global_state", default=False, action="store_true"
    )
    common_snap_index_parser.add_argument(
        "--ignore_unavailable", action="store_true", default=True
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
        help="Create a snapshot.",
        description="Create a snapshot.",
    )
    snap_create.add_argument(
        "--wait",
        help="Wait for snapshot creation to be completed.",
        default=False,
        action="store_true",
    )
    snap_create.set_defaults(function=cmd_create_snapshot)

    set_metadata(
        snap_create,
        risk="write",
    )

    snap_delete = snap_sub.add_parser(
        "delete",
        parents=[
            common_parser,
            common_snap_parser,
            mutating_parser,
            destructive_command_parser,
            output_parser,
        ],
        help="Delete a snapshot.",
        description="Delete a snapshot.",
    )
    snap_delete.set_defaults(function=cmd_delete_snapshot)

    set_metadata(
        snap_delete,
        risk="destructive",
        confirmation=("The user must explicitly confirm the action before execution."),
    )

    snap_restore = snap_sub.add_parser(
        "restore",
        parents=[
            common_parser,
            common_snap_parser,
            common_snap_index_parser,
            mutating_parser,
            output_parser,
        ],
        help="Restore a snapshot.",
        description="Restore a snapshot.",
    )
    snap_restore.add_argument(
        "--wait",
        help="Wait until restoratio is done.",
        default=False,
        action="store_true",
    )
    snap_restore.add_argument("--ilm", help="Override ILM policy.")
    snap_restore.add_argument(
        "--remove-ilm",
        help="Remove the original ILM when restoring.",
        default=False,
        action="store_true",
    )
    snap_restore.set_defaults(function=cmd_restore_snapshot)

    set_metadata(snap_restore, risk="write")

    snap_show_parser = snap_sub.add_parser(
        "show",
        parents=[
            common_parser,
            common_snap_parser,
            viewer_command_parser,
            output_parser,
        ],
        help="Show snapshot details.",
        description="Show a snapshot details.",
    )
    snap_show_parser.set_defaults(function=cmd_snap_show)

    set_metadata(
        snap_show_parser,
        risk="read",
    )

    # Index commands
    common_index_parser = argparse.ArgumentParser(add_help=False)
    common_index_parser.add_argument("index", help="Name of an index.", type=str)

    index_mapper_parser = argparse.ArgumentParser(add_help=False)
    index_mapper_parser.add_argument(
        "-m", "--mapping", help="Name of mapping in the config.", type=str
    )

    index_parser = sub.add_parser(
        "index", help="Index commands.", description="Index commands."
    )
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
        help="Delete an index.",
        description="Delete an index.",
    )
    index_delete.set_defaults(function=cmd_delete_index)

    set_metadata(
        index_delete,
        risk="destructive",
        confirmation=("The user must explicitly confirm the action before execution."),
    )

    index_create = index_sub.add_parser(
        "create",
        parents=[
            common_parser,
            common_index_parser,
            index_mapper_parser,
            mutating_parser,
            output_parser,
        ],
        help="Create an index.",
        description="Create an index.",
    )
    index_create.set_defaults(function=cmd_create_index)

    set_metadata(
        index_create,
        risk="write",
    )

    index_show = index_sub.add_parser(
        "show",
        parents=[
            common_parser,
            common_index_parser,
            viewer_command_parser,
            output_parser,
        ],
        help="Show an index.",
        description="Show an index.",
    )
    index_show.set_defaults(function=cmd_show_index)

    set_metadata(
        index_show,
        risk="read",
    )

    index_status = index_sub.add_parser(
        "status",
        parents=[
            common_parser,
            common_index_parser,
            viewer_command_parser,
            output_parser,
        ],
        help="Show a recovery status of an index.",
        description="Show a recovery status of an index.",
    )
    index_status.set_defaults(function=cmd_restore_status)

    set_metadata(
        index_status,
        risk="read",
    )

    # Reindex Commands
    reindex = sub.add_parser(
        "reindex",
        parents=[common_parser, index_mapper_parser, mutating_parser, output_parser],
        help="Reindex command.",
        description="Reindex command.",
    )
    reindex.add_argument(
        "src",
        help="Source index. it can be multiple by comma separated or * wild card can be used",
        type=str,
    )
    reindex.add_argument("dst", help="destination index", type=str)
    reindex.set_defaults(function=cmd_reindex)

    set_metadata(
        reindex,
        risk="write",
    )

    reindex_mapping = sub.add_parser(
        "mapping",
        help="Shows mappings in the config",
        parents=[common_parser, output_parser],
        description="Shows mappings in the config.",
    )
    reindex_mapping.set_defaults(function=cmd_reindex_mapping)

    set_metadata(
        reindex_mapping,
        risk="read",
    )

    task = sub.add_parser(
        "task",
        help="Elasticsearch Task Commands",
        description="Elasticsearch Task Commands.",
    )
    task_sub = task.add_subparsers(required=True)

    task_get = task_sub.add_parser(
        "get",
        help="Get task status on elasticsearch",
        parents=[common_parser, output_parser],
        description="Get task status on elasticsearch.",
    )
    task_get.add_argument("task_id", help="elasticsearch task id", type=str)
    task_get.set_defaults(function=cmd_get_task)
    set_metadata(task_get, risk="read")

    job = sub.add_parser(
        "job", help="Job related commands.", description="Job related commands."
    )

    job_sub = job.add_subparsers(required=True)
    job_list = job_sub.add_parser(
        "list",
        parents=[common_parser, viewer_command_parser, output_parser],
        help="List jobs.",
        description="List jobs.",
    )
    job_list.add_argument(
        "--local",
        default=False,
        action="store_true",
        help="Show local jobs in .eskit/jobs generated by archive commands.",
    )
    job_list.set_defaults(function=cmd_list_jobs)

    set_metadata(
        job_list,
        risk="read",
    )

    job_show = job_sub.add_parser(
        "show",
        parents=[common_parser, viewer_command_parser, output_parser],
        help="Show job details.",
        description="Show job details.",
    )
    job_show.add_argument(
        "job_search_id",
        help="Job search id / job output file name in the jobs cache",
        type=str,
    )
    job_show.set_defaults(function=cmd_read_job)

    status = sub.add_parser(
        "status",
        parents=[common_parser, output_parser, viewer_command_parser],
        help="Show current ESKit status.",
        description="Show current ESKit status.",
    )
    status.set_defaults(function=cmd_status)

    archive_common_parser = argparse.ArgumentParser(add_help=False)
    archive_common_parser.add_argument("name", help="Name of the archive", type=str)

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
        "archive",
        help="Archive commands.",
        description="Archive commands.",
    )

    archive_sub = archive.add_subparsers(required=True)

    archive_list_parser = archive_sub.add_parser(
        "list",
        parents=[common_parser, viewer_command_parser, output_parser],
        description="List archives.",
        help="List archives.",
    )
    archive_list_parser.set_defaults(function=cmd_list_archives)

    set_metadata(
        archive_list_parser,
        risk="read",
    )

    archive_pull_parser = archive_sub.add_parser(
        "pull",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
            output_parser,
        ],
        help="Pull an data from the source to local destination defined in the config. This is incremental.",
        description="Pull an data from the source to local destination defined in the config. This is incremental.",
    )
    archive_pull_parser.set_defaults(function=cmd_pull_archive)

    set_metadata(
        archive_pull_parser,
        risk="write",
    )

    archive_sync_parser = archive_sub.add_parser(
        "sync",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
            output_parser,
        ],
        help="Sync with a source host with mirroring.",
        description="Sync with a source host with mirroring.",
    )
    archive_sync_parser.set_defaults(function=cmd_sync_archive, risk="destructive")
    set_metadata(archive_sync_parser, risk="destructive")

    archive_push_parser = archive_sub.add_parser(
        "push",
        parents=[
            common_parser,
            mutating_parser,
            archive_common_parser,
            archive_common_operation_parser,
            output_parser,
        ],
        help="Push a local archive with a destination host with mirroring.",
        description="Sync with a destination host with mirroring.",
    )
    archive_push_parser.add_argument(
        "--dst",
        required=True,
        help="Destination host. <eskit_host>:<path> can be used to target remote host. e.g. Host1:/home/user/data.",
    )
    archive_push_parser.set_defaults(function=cmd_push_archive)

    set_metadata(
        archive_push_parser,
        risk="write",
    )

    archive_show_parser = archive_sub.add_parser(
        "show",
        parents=[
            common_parser,
            viewer_command_parser,
            archive_common_parser,
            output_parser,
        ],
        help="Show an archive.",
        description="Show an archive.",
    )
    archive_show_parser.set_defaults(function=cmd_show_archive)

    set_metadata(
        archive_show_parser,
        risk="read",
    )

    # ILM Command

    ilm_common_parser = argparse.ArgumentParser(add_help=False)
    ilm_common_parser.add_argument("name", help="Name of the ilm.", type=str)

    ilm = sub.add_parser(
        "ilm",
        help="Index lifecycle management commands.",
        description="Index lifecycle management commands.",
    )
    ilm_sub = ilm.add_subparsers(required=True)

    ilm_show_parser = ilm_sub.add_parser(
        "show",
        parents=[
            common_parser,
            viewer_command_parser,
            ilm_common_parser,
            output_parser,
        ],
        help="Show lifecycle management commands.",
        description="Show lifecycle management commands.",
    )
    ilm_show_parser.set_defaults(function=cmd_show_ilm)

    set_metadata(
        ilm_show_parser,
        risk="read",
    )

    ai_parser = sub.add_parser(
        "ai",
        help="AI commands.",
        parents=[output_parser],
        description="AI commands.",
    )
    ai_parser.add_argument("question", help="Question to ask to AI.")
    ai_parser.add_argument(
        "--model",
        help="Choose the LLM model to work with.",
        default="claude-haiku-4-5-20251001",
        choices=[
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-6",
            "claude-sonnet-5",
            "qwen3:4b",
            "qwen3:8b",
            "gemma3:4b",
            "mistral:7b",
            "qwen3:14b",
        ],
    )
    ai_parser.add_argument(
        "--output-command-json", help="A path to output command json."
    )
    ai_parser.set_defaults(function=cmd_ai)

    describe = sub.add_parser(
        "describe",
        parents=[common_parser, output_parser],
        help="Build command IR",
        description="Build command IR",
    )

    describe.add_argument("--out", help="a path to output file.")
    describe.set_defaults(function=cmd_describe)

    return p


def main():

    args = build_parser().parse_args()

    from eskit.jobs.job_manager import init

    init(CACHE_ROOT)

    configure_logging(args.verbose, args.debug)

    result = args.function(args)

    ai_mode = hasattr(args, "ai") or (args.command == "ai")

    from eskit.render.renderer import render_result
    from eskit.ai.helper import run_agent

    if ai_mode:
        # print("result:", result)
        pass
    else:
        render_result(args, result)
        if result.code == ResultCode.CANCELED:
            return ExitCode.CANCELED

        if result.code != ResultCode.SUCCESS:
            return ExitCode.FAILURE

    return ExitCode.SUCCESS


if __name__ == "__main__":
    main()
