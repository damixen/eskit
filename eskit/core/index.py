import uuid
import logging
from datetime import datetime, timezone

from eskit.utils.config import load_config, get_host_config, get_reindex_mapping
from eskit.utils.view import build_field_list, apply_view
from eskit.utils.input import confirm_delete
from eskit.core.host import (
    get_current_host_name,
    check_host_name,
    print_host,
    check_push_protected,
)
from eskit.cache.store import read_cache, write_job
from eskit.clients.es_client import connect_es
from eskit.jobs.job import ESKitJob
from eskit.result import Result, ResultCode
from eskit.resource_type import ResourceType

logger = logging.getLogger(__name__)

HTTP_METHOD_DELETE = "DELETE"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_POST = "POST"
HTTP_METHOD_GET = "GET"


def get(config_path, host_name, index, views, fields, flat):
    """
    Public API
    """
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    print_host(host_name)

    if not find_index(host_name, index):
        # logger.error(
        #     "Index:%s not found in cache or does not exist. "
        #     "Please update cache and try again.",
        #     index,
        # )
        return Result.fail(
            ResultCode.NOT_FOUND,
            "Resource not found.",
            {"resource": ResourceType.INDEX, "name": index},
        )

    url = f"/{index}"
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        index_data = res[index]
        target_fields = build_field_list(config, views, fields)
        out = index_data
        if len(target_fields) > 0:
            out = apply_view(index_data, target_fields, flat)

        return Result.ok(out)

    except Exception as e:
        logger.exception(e)

    finally:
        ssh.close()

    return Result.fail(
        ResultCode.INTERNAL_ERROR,
        "Failed to get index data.",
        {"resource": ResourceType.INDEX, "name": index},
    )


def create(config_path, host_name, index, mapping, dry_run, push):
    """
    Public API
    """
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    if find_index(host_name, index):
        # logger.error(
        #     "Index:%s already exists in the cache. Please pull the latest or delete the index.",
        #     index,
        # )
        return Result.fail(
            ResultCode.ALREADY_EXISTS,
            "Resource already exists.",
            {"resource": ResourceType.INDEX, "name": index},
        )

    body = {}
    if mapping:
        m = get_reindex_mapping(config, mapping)
        if m:
            body["mappings"] = m

    url = f"/{index}"
    if dry_run:
        # print_dry_run()
        # print(HTTP_METHOD_PUT, url)
        # print(json.dumps(body, indent=2))
        return Result.ok(
            {
                "executed": False,
                "command": {"method": HTTP_METHOD_PUT, "url": f"/{index}"},
            }
        )

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_PUT, url, body)
        logger.debug("Response:%s", res)
        logger.info("Index:%s created. Updating Cache.", index)
        from eskit.core.metadata import pull_metadata

        pull_metadata(config_path, host_name)
    except Exception as e:
        logger.exception(e)
        return Result.fail(
            ResultCode.INTERNAL_ERROR,
            "Failed to create index.",
            {"resource": ResourceType.INDEX, "name": index},
        )
    finally:
        ssh.close()

    return Result.ok()


def delete(config_path, host_name, index, dry_run, push, force):
    """
    Public API
    """
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    if not find_index(host_name, index):
        # logger.error("Index:%s not found in cache. Please pull the latest.", index)
        return Result.fail(
            ResultCode.NOT_FOUND,
            "Repository not found.",
            {"resource": ResourceType.REPOSITORY, "name": index},
        )

    if not dry_run and not force:
        if not confirm_delete("index", index):
            return Result.fail(
                ResultCode.CANCELED,
                "Canceled.",
                {"resource": ResourceType.REPOSITORY, "name": index},
            )

    url = f"/{index}"
    if dry_run:
        # print_dry_run()
        # print(HTTP_METHOD_DELETE, url)
        return Result.ok(
            {
                "executed": False,
                "command": {"method": "DELETE", "url": f"/{index}"},
            }
        )
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_DELETE, url)
        logger.debug("Response:%s", res)
        logger.info("Index:%s deleted. Updating Cache.", index)
        from eskit.core.metadata import pull_metadata

        pull_metadata(config_path, host_name)
    except Exception as e:
        logger.exception(e)
        return Result.fail(
            ResultCode.INTERNAL_ERROR,
            "Failed to delete index.",
            {"resource": ResourceType.INDEX, "name": index},
        )
    finally:
        ssh.close()

    return Result.ok()


def status(config_path, host_name, index, views, fields, flat):
    """
    Public API
    """
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)

    target_fields = build_field_list(config, views, fields)

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        out = []
        data = es.request("GET", f"/_cat/recovery/{index}?format=json")
        for r in data:
            if len(target_fields) > 0:
                out.append(apply_view(r, target_fields, flat))
            else:
                out.append(r)
        out.sort(key=lambda x: x["index"])
    finally:
        ssh.close()

    return Result.ok(out)


def reindex(config_path, host_name, src, dst, mapping, dry_run, push):
    """
    Public API
    """
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    body = {}
    m = None
    if mapping:
        m = get_reindex_mapping(config, mapping)
        if m:
            body["mappings"] = m
        else:
            # logger.error("Mapping:%s does not exist in the config.", mapping)
            return Result.fail(
                ResultCode.NOT_FOUND,
                "Mapping config not found.",
                {"resource": ResourceType.CONFIG, "name": mapping},
            )

    dst_exists = find_index(host_name, dst)
    if m and dst_exists:
        # logger.error(
        #    "Mapping specified, but index already exists in cache. Please pull latest or delete the index."
        # )
        return Result.fail(
            ResultCode.ALREADY_EXISTS,
            "Resource already exists. Cannot change mapping.",
            {"resource": ResourceType.INDEX, "name": dst},
        )

    if not dst_exists:
        logger.info("Creating a new index:%s.", dst)
        create(config_path, host_name, dst, mapping, dry_run, push)

    job = ESKitJob(
        id=str(uuid.uuid4()),
        name=dst,
        type="reindex",
        host=host_name,
        status="running",
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        payload={"src": src, "dst": dst},
    )

    body = {}
    body["source"] = {"index": src}
    body["dest"] = {"index": dst}

    # default: don't wait
    url = "/_reindex?wait_for_completion=false"
    if dry_run:
        # print_dry_run()
        # print(HTTP_METHOD_POST, url)
        # print(json.dumps(body, indent=2))
        return Result.ok(
            {
                "executed": False,
                "command": {
                    "method": HTTP_METHOD_POST,
                    "url": "/_reindex?wait_for_completion=false",
                },
            }
        )

    write_job(host_name, job)

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    result_code = ResultCode.SUCCESS
    result_msg = ""
    try:
        res = es.request(HTTP_METHOD_POST, url, body)
        # print(json.dumps(res, indent=2))
        # print("check status with task-get command with the id")

        job.status = "running"
        job.result = {"task_id": res.get("task")}
        job.updated_at = datetime.now(timezone.utc).isoformat()

        write_job(host_name, job)

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        write_job(host_name, job)
        result_code = ResultCode.INTERNAL_ERROR
    finally:
        ssh.close()

    return Result(
        code=result_code,
        value=job.to_dict(),
        message=result_msg,
    )


# Internal
def find_index(host, index):
    index_cache = read_cache(host, "indices")
    if not index_cache:
        return False

    for i in index_cache:
        if index == i["index"]:
            return True

    return False
