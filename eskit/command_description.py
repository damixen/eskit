import argparse
from .cli import build_parser

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

        result["arguments"].append({
            "flags": action.option_strings,
            "name": action.dest,
            "type": normalize_type(action),
            "required": action.required,
            "default": serialize_default(action.default),
            "choices": (
                list(action.choices)
                if action.choices is not None
                else None
            ),
            "nargs": action.nargs,
            "description": action.help,
        })

    metadata = getattr(parser, "_eskit_metadata", None)
    if metadata:
        result["metadata"] = metadata

    return result

def build_command_description():
    parser = build_parser()
    return describe_parser(parser)