import argparse


def serialize_default(value):
    if callable(value):
        return value.__name__
    return value


def normalize_type(action):
    if action.nargs == 0:
        return "boolean"

    if action.type is None:
        return "str"

    if hasattr(action.type, "__name__"):   
        return action.type.__name__

    return str(action.type)


def get_required(action):
    if not action.option_strings:
        # Positional argument
        return action.nargs not in ("?", "*")

    return action.required


def normalize_nargs(nargs):
    if nargs is None:
        return "one"
    if nargs == "?":
        return "zero_or_one"
    if nargs == "*":
        return "zero_or_more"
    if nargs == "+":
        return "one_or_more"
    if isinstance(nargs, int):
        return nargs

    return str(nargs)


def describe_parser(parser):
    result = {
        "program": parser.prog,
        "description": parser.description,
        "arguments": [],
        "commands": {},
    }

    for action in parser._actions:
        if isinstance(action, argparse._HelpAction):
            continue

        if isinstance(action, argparse._SubParsersAction):
            for name, subparser in action.choices.items():
                result["commands"][name] = describe_parser(subparser)
            continue

        result["arguments"].append(
            {
                "flags": action.option_strings,
                "name": action.dest,
                "type": normalize_type(action),
                "required": get_required(action),
                "default": serialize_default(action.default),
                "choices": (
                    list(action.choices) if action.choices is not None else None
                ),
                "nargs": normalize_nargs(action.nargs),
                "description": action.help,
            }
        )

    metadata = getattr(parser, "_eskit_metadata", None)
    if metadata:
        result["metadata"] = metadata

    return result
