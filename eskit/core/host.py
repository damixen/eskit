from eskit.utils.config import load_config, get_host_config
from eskit.utils.paths import CURRENT_HOST_FILE


def print_dry_run():
    print("\n*Dry Run*\n")


def print_preview():
    print("\n*Preview*\n")


def print_host(host):
    print(f"\n=== ESKit HOST: {host} ===\n")


def get_current_host_name():
    if not (CURRENT_HOST_FILE).exists():
        return

    with open(CURRENT_HOST_FILE, "r", encoding="utf-8") as f:
        for line in f:
            return line


def set_current_host_name(host):
    with open(CURRENT_HOST_FILE, "w", encoding="utf-8") as f:
        f.write(host)
    print(f"Host is set to:{host}")


def check_host_name(host):
    if host is None:
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
        print_host(host)
        raise SystemExit(
            f"Host:{host} is push protected. Please use --push to make a change or --dry-run to check command."
        )
    return


def get_hosts(host_name, config_path):

    config = load_config(config_path)
    host = host_name

    hosts = config.get("hosts", [])
    if host:
        out = []
        for h in hosts:
            if h["name"] == host:
                out.append(h)
                break
        hosts = out

    if len(hosts) == 0:
        print(f"Host:{host_name} not found.")
        return None

    return hosts
