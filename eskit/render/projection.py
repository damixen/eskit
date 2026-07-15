def build_field_list(view_config, views, fields):
    """
    Builds a unique list of fields from views and explicit field selections.
    """
    result = []

    for view in views or []:
        result.extend(view_config.get(view, []))

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


def project(value, fields, flatten=False):
    """
    Project a dict or list of dicts to the selected fields.
    """

    if isinstance(value, list):
        return [
            project(item, fields, flatten)
            for item in value
        ]

    out = {}

    for field in fields:
        field_value = get_path(value, field)

        if flatten:
            out[field] = field_value
        elif field_value is not None:
            set_path(out, field, field_value)

    return out