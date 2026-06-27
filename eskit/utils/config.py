import json

from eskit.error import ConfigError


def get_view_configs(config, views):
    views_config = config.get("views", {})
    out = []
    for name in views:
        if name not in views_config:
            raise ConfigError(f"view not found: {name}")
        out.extend(views_config[name])
    return out


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_host_config(config, host_name):
    for h in config.get("hosts", []):
        if h["name"] == host_name:
            return h
    raise SystemExit(f"Host not found: {host_name}")


def is_push_protected(config, host_name):
    host_config = get_host_config(config, host_name)
    return "push-protected" in host_config and host_config["push-protected"]
