# def build_field_list(view_config, views, fields) -> list[str] | list[list[str]]:
#     """
#     Builds a unique list of fields from views and explicit field selections.
#     """
#     result = []

#     for view in views or []:
#         result.extend(view_config.get(view, []))

#     if fields:
#         result.extend(fields.split(","))

#     result = [
#     list(x) if isinstance(x, tuple) else x 
#     for x in dict.fromkeys(tuple(item) if isinstance(item, list) else item for item in result)
# ]

#     return result


# # def normalize_projection(fields):
# #     result = []

# #     seen = set()

# #     for field in fields:
# #         normalized = normalize_field(field)

# #         path = normalized.path

# #         if path in seen:
# #             continue

# #         seen.add(path)
# #         result.append(normalized)

# #     return result

# def normalize_projection(fields: list[str] | list[list[str]]):
#     result = []

#     seen = set()

#     for field in fields:
#         normalized_path = normalize_path(field)
#         if normalized_path in seen:
#             continue

#         seen.add(normalized_path)
#         result.append(normalized_path)

#     return result


# def normalize_path(path: str | list[str] | tuple[str, ...]) -> tuple[str, ...]:

#     result = None
#     if isinstance(path, str):
#         result = tuple(path.split("."))
#     else:
#         result = tuple(path)

#     result = tuple(item.replace("$", ".") for item in result)

#     return result


# def get_path(data, path: tuple[str, ...]):
#     current = data

#     for part in path:
#         if not isinstance(current, dict):
#             return None

#         if part not in current:
#             return None

#         current = current[part]

#     return current


# def set_path(data, path: tuple[str, ...], value):

#     current = data

#     for part in path[:-1]:
#         part = part.replace("$", ".")

#         if part not in current:
#             current[part] = {}

#         current = current[part]

#     current[path[-1]] = value

