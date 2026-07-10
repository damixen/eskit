import json
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
    print_dry_run,
)
from eskit.cache.store import read_cache, write_job
from eskit.clients.es_client import connect_es
from eskit.jobs.job import ESKitJob
from eskit.exit_code import ExitCode

logger = logging.getLogger(__name__)

HTTP_METHOD_DELETE = "DELETE"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_POST = "POST"
HTTP_METHOD_GET = "GET"


def show(config_path, host_name, index, views, fields, flat):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    print_host(host_name)

    if not find_index(host_name, index):
        logger.error(
            "Index:%s not found in cache or does not exist. "
            "Please update cache and try again.",
            index,
        )
        return ExitCode.FAILURE

    url = f"/{index}"
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_GET, url)
        index_data = res[index]
        target_fields = build_field_list(config, views, fields)

        if len(target_fields) > 0:
            print(json.dumps(apply_view(index_data, target_fields, flat), indent=2))
        else:
            print(json.dumps(index_data, indent=2))

    except Exception as e:
        print(e)
        return ExitCode.FAILURE
    finally:
        ssh.close()

    return ExitCode.SUCCESS


def create(config_path, host_name, index, mapping, dry_run, push):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    if find_index(host_name, index):
        logger.error(
            "Index:%s already exists in the cache. Please pull the latest or delete the index.",
            index,
        )
        return ExitCode.FAILURE

    body = {}
    if mapping:
        m = get_reindex_mapping(config, mapping)
        if m:
            body["mappings"] = m

    url = f"/{index}"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_PUT, url)
        print(json.dumps(body, indent=2))
        return ExitCode.SUCCESS

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_PUT, url, body)
        print(res)
        logger.info("Index:%s created. Updating Cache.", index)
        from eskit.core.metadata import pull

        pull(config_path, host_name)
    except Exception as e:
        print(e)
        return ExitCode.FAILURE
    finally:
        ssh.close()

    return ExitCode.SUCCESS


def delete(config_path, host_name, index, dry_run, push, force):
    config = load_config(config_path)

    if host_name is None:
        host_name = get_current_host_name()
    check_host_name(host_name)
    check_push_protected(config, host_name, dry_run, push)
    print_host(host_name)

    if not find_index(host_name, index):
        logger.error("Index:%s not found in cache. Please pull the latest.", index)
        return ExitCode.FAILURE

    if not dry_run and not force:
        if not confirm_delete("index", index):
            print("Cancelled.")
            return ExitCode.CANCELED

    url = f"/{index}"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_DELETE, url)
        return ExitCode.SUCCESS
    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_DELETE, url)
        print(res)
        logger.info("Index:%s deleted. Updating Cache.", index)
        from eskit.core.metadata import pull

        pull(config_path, host_name)
    except Exception as e:
        print(e)
        return ExitCode.FAILURE
    finally:
        ssh.close()

    return ExitCode.SUCCESS


def status(config_path, host_name, index, views, fields, flat):
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
        print(json.dumps(out, indent=2))
    finally:
        ssh.close()

    return ExitCode.SUCCESS


def reindex(config_path, host_name, src, dst, mapping, dry_run, push):
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
            logger.error("Mapping:%s does not exist in the config.", mapping)
            return ExitCode.FAILURE

    dst_exists = find_index(host_name, dst)
    if m and dst_exists:
        logger.error(
            "Mapping specified, but index already exists in cache. Please pull latest or delete the index."
        )
        return ExitCode.FAILURE

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
    url = f"/_reindex?wait_for_completion=false"
    if dry_run:
        print_dry_run()
        print(HTTP_METHOD_POST, url)
        print(json.dumps(body, indent=2))
        return ExitCode.SUCCESS

    write_job(host_name, job)

    host_config = get_host_config(config, host_name)
    ssh, es = connect_es(host_config)
    try:
        res = es.request(HTTP_METHOD_POST, url, body)
        # print(json.dumps(res, indent=2))
        # print("check status with task-get command with the id")

        job.status = "running"
        job.result = {"task_id": res.get("task")}
        job.updated_at = datetime.now(timezone.utc).isoformat()

        write_job(host_name, job)

        print(
            f"[{host_name}] reindex job started search id/output name: {job.get_output_id()}"
        )

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        write_job(host_name, job)
        print(e)
        return ExitCode.FAILURE
    finally:
        ssh.close()

    return ExitCode.SUCCESS


# Internal
def find_index(host, index):
    index_cache = read_cache(host, "indices")
    if not index_cache:
        return False

    for i in index_cache:
        if index == i["index"]:
            return True

    return False
