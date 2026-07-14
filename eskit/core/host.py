import logging
from eskit.utils.config import get_host_config
from eskit.utils.paths import CURRENT_HOST_FILE
from eskit.result import Result, ResultCode, ResourceTarget, Argument
from eskit.resource_type import ResourceType
from eskit.config.types import Config

logger = logging.getLogger(__name__)


def get_current_host_name():
    if not (CURRENT_HOST_FILE).exists():
        return

    with open(CURRENT_HOST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            return line


def check_host_name(host):
    if host is None:
        # TODO: add HostNotFoundError error class
        raise SystemExit(
            "Host not found. Please specify the host or set the host by the host set command."
        )
    return


def check_push_protected(config, host, dry_run, push):
    host_config = get_host_config(config, host)
    if (
        "push-protected" in host_config
        and host_config["push-protected"]
        and not dry_run
        and not push
    ):
        # TODO: add PushProtectionError error class
        raise SystemExit(
            f"Host:{host} is push protected. Please use --push to make a change or --dry-run to check command."
        )
    return


def get_host(host_name, config: Config):
    """
    Public API Retuns the host config by name.
    """

    host = host_name

    if not host:
        return Result.fail(
            ResultCode.INVALID_ARGUMENT,
            "Empty host name.",
            context=Argument(name="host", value=None),
        )

    if not config:
        return Result.fail(
            ResultCode.INVALID_ARGUMENT,
            "Config is None.",
            context=Argument(name="config", value=None),
        )

    hosts = config.get("hosts", [])
    if host:
        for h in hosts:
            if h["name"] == host:
                return Result.ok(h)
    return Result.fail(ResultCode.NOT_FOUND, "Resource not found.")


def set_current_host_name(host):
    """
    Public API Sets a host name in the current host file.
    """
    try:
        with open(CURRENT_HOST_FILE, "w", encoding="utf-8") as f:
            f.write(host)
    except Exception:
        logger.exception("Failed to write current host configuration.")
        return Result.fail(
            ResultCode.INTERNAL_ERROR,
            "Failed to write current host configuration.",
            context=ResourceTarget(
                resource=ResourceType.CONFIG, name=str(CURRENT_HOST_FILE)
            ),
        )
    return Result.ok({"host": host})
