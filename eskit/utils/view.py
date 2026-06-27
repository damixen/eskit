def build_field_list(config, views, fields):
    result = []

    for view in views:
        result.extend(config["views"].get(view, []))

    if fields:
        result.extend(fields.split(","))

    return list(dict.fromkeys(result))


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


def build_projection(data, field_paths):
    out = {}

    for path in field_paths:
        value = get_path(data, path)

        if value is not None:
            out[path] = value

    return out
