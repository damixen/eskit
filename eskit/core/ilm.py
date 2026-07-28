import logging
from eskit.core.host import (
    check_host_name,
)
from eskit.result import Result, ResultCode, DataSource
from eskit.cache.store import read_cache
from eskit.resource_type import ResourceType

logger = logging.getLogger(__name__)

HTTP_METHOD_DELETE = "DELETE"
HTTP_METHOD_PUT = "PUT"
HTTP_METHOD_POST = "POST"
HTTP_METHOD_GET = "GET"


def get(host_name, policy_name):
    """
    Public API
    """

    check_host_name(host_name)

    ilms = read_cache(host_name, "ilms")

    if ilms is None:
        return Result.fail(
            ResultCode.NOT_FOUND,
            "ILM cache not found. Please pull.",
            context={"resource_type": ResourceType.CACHE},
        )

    ilm_data = None
    for ilm in ilms:
        if ilm["name"] == policy_name:
            ilm_data = ilm
            break

    if not ilm_data:
        return Result.fail(
            ResultCode.NOT_FOUND,
            "ILM policy not found. Please pull.",
            context={"resource_type": ResourceType.ILM},
        )

    return Result.ok(ilm_data, context={"sources": [DataSource.CACHE]})
