import uuid
import logging
from datetime import datetime, timezone

from eskit.utils.config import get_host_config, get_reindex_mapping
from eskit.utils.input import confirm_delete
from eskit.core.host import (
    check_host_name,
    check_push_protected,
)
from eskit.cache.store import read_cache, write_job
from eskit.clients.es_client import connect_es
from eskit.jobs.job import ESKitJob
from eskit.result import Result, ResultCode, ResourceTarget, DataSource
from eskit.resource_type import ResourceType
from eskit.config.types import Config
from eskit.resource.index import INDEX_SCHEMA
from eskit.core.metadata import parse_duration

logger = logging.getLogger(__name__)

HTTP_METHOD_DELETE = "DELETE"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_POST = "POST"
HTTP_METHOD_GET = "GET"


def get(config: Config, host_name, index):
    """
    Public API
    """

    check_host_name(host_name)

    if not find_index(host_name, index):
        # logger.error(
        #     "Index:%s not found in cache or does not exist. "
        #     "Please update cache and try again.",
        #     index,
        # )
        return Result.fail(ResultCode.NOT_FOUND, "Resource not found.")

    url = f"/{index}"
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        index_data = res[index]

        cat_param = ",".join(INDEX_SCHEMA.names())
        indices = es.request(
            "GET", f"/_cat/indices?h={cat_param}&format=json&index={index}"
        )
        if indices and len(indices) > 0:
            index_data |= indices[0]

        ilm = es.request(
            "GET", f"/{index}/_ilm/explain"
        )
        policy = None
        retention = None
        if ilm:
            policy = ilm["indices"][index].get("policy", None)

        if policy:
            policy_data = es.request(
                "GET", f"/_ilm/policy/{policy}"
            )
            delete_data = policy_data[policy]["policy"]["phases"].get("delete", None)
            retention = delete_data["min_age"]
            if retention:
                ilm["indices"][index]["retention"] = retention
                retention_ms = parse_duration(retention)
                ilm["indices"][index]["remaining_ms"] = retention_ms - ilm["indices"][index]["age_in_millis"]
            index_data["ilm"] = ilm["indices"][index]

        return Result.ok(index_data, context={"sources":[DataSource.ELASTICSEARCH]})

    except Exception as e:
        logger.exception(e)

    finally:
        ssh.close()

    return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to get index data.")


def create(config: Config, host_name, index, mapping, dry_run, push):
    """
    Public API
    """

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)

    if find_index(host_name, index):
        # logger.error(
        #     "Index:%s already exists in the cache. Please pull the latest or delete the index.",
        #     index,
        # )
        return Result.fail(ResultCode.ALREADY_EXISTS, "Resource already exists.")

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

        pull_metadata(config, host_name)
    except Exception as e:
        logger.exception(e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to create index.")
    finally:
        ssh.close()

    return Result.ok()


def delete(config: Config, host_name, index, dry_run, push, force):
    """
    Public API
    """

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)

    if not find_index(host_name, index):
        # logger.error("Index:%s not found in cache. Please pull the latest.", index)
        return Result.fail(ResultCode.NOT_FOUND, "Index not found.")

    if not dry_run and not force:
        if not confirm_delete("index", index):
            return Result.fail(ResultCode.CANCELED, "Canceled.")

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

        pull_metadata(config, host_name)
    except Exception as e:
        logger.exception(e)
        return Result.fail(ResultCode.INTERNAL_ERROR, "Failed to delete index.")
    finally:
        ssh.close()

    return Result.ok()


def status(config: Config, host_name, index):
    """
    Public API
    """

    check_host_name(host_name)

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        out = []
        data = es.request("GET", f"/_cat/recovery/{index}?format=json")
        for r in data:
            out.append(r)
        out.sort(key=lambda x: x["index"])
    finally:
        ssh.close()

    return Result.ok(out, context={"sources":[DataSource.ELASTICSEARCH]})


def reindex(config: Config, host_name, src, dst, mapping, dry_run, push):
    """
    Public API
    """

    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)

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
                context=ResourceTarget(resource=ResourceType.CONFIG, name=mapping),
            )

    dst_exists = find_index(host_name, dst)
    if m and dst_exists:
        # logger.error(
        #    "Mapping specified, but index already exists in cache. Please pull latest or delete the index."
        # )
        return Result.fail(
            ResultCode.ALREADY_EXISTS,
            "Resource already exists. Cannot change mapping.",
            context=ResourceTarget(resource=ResourceType.INDEX, name=dst),
        )

    if not dst_exists:
        logger.info("Creating a new index:%s.", dst)
        create(config, host_name, dst, mapping, dry_run, push)

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
