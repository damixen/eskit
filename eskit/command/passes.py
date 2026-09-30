from typing import Any
from copy import deepcopy

class CommandPass:
    def apply(self, command: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError


class RemoveUnnecessaryFields(CommandPass):
    FIELDS_TO_REMOVE = {
        "nargs",
    }

    EMPTY_FIELDS_TO_REMOVE = {
        "commands",
    }

    def apply(self, command: dict[str, Any]) -> dict[str, Any]:
        return self._clean(command)

    def _clean(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: self._clean(item)
                for key, item in value.items()
                if not self._remove(key, item)
            }

        if isinstance(value, list):
            return [self._clean(item) for item in value]

        return value

    def _remove(self, key: str, value: Any) -> bool:
        if key in self.FIELDS_TO_REMOVE:
            return True

        if value is None:
            return True

        if key in self.EMPTY_FIELDS_TO_REMOVE and not value:
            return True

        return False


class DeduplicateCommonArgs(CommandPass):
    COMMON_ARGUMENTS = {
        "verbose",
        "debug",
        "json",
        "view",
        "config",
        "host",
        "fields",
        "flat",
        "dry_run",
    }

    def apply(self, command: dict[str, Any]) -> dict[str, Any]:
        result = deepcopy(command)

        common_arguments: dict[str, Any] = {}

        result["arguments"], extracted = self._extract_common(
            result.get("arguments", [])
        )
        common_arguments.update(extracted)

        self._process_commands(
            result.get("commands", {}),
            common_arguments,
        )

        if common_arguments:
            result["common_arguments"] = common_arguments

        return result

    def _process_commands(
        self,
        commands: dict[str, Any],
        common_arguments: dict[str, Any],
    ) -> None:
        for command in commands.values():
            arguments = command.get("arguments", [])

            remaining, extracted = self._extract_common(arguments)
            if remaining:
                command["arguments"] = remaining

            for name, definition in extracted.items():
                common_arguments.setdefault(name, definition)

            if extracted:
                command["common_arguments"] = list(extracted)

            self._process_commands(
                command.get("commands", {}),
                common_arguments,
            )

    def _extract_common(
        self,
        arguments: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        remaining = []
        extracted = {}

        for argument in arguments:
            name = argument.get("name")

            if name in self.COMMON_ARGUMENTS:
                extracted[name] = argument
            else:
                remaining.append(argument)

        return remaining, extracted


class SelectContexts(CommandPass):
    def __init__(self, contexts: set[str]):
        self.contexts = contexts

    def apply(self, command):
        result = deepcopy(command)

        if not self.contexts:
            result["commands"] = {}
            return result

        result["commands"] = {
            name: value
            for name, value in result.get("commands", {}).items()
            if value.get("metadata", {}).get("context") in self.contexts
        }
        
        for value in result["commands"].values():
            metadata = value.setdefault("metadata", {})
            metadata["context_level"] = "loaded"

        return result


class ContextOverviewPass(CommandPass):
    def __init__(self, command_ir: dict[str, Any]):
        self.command_ir = command_ir

    def apply(self, command: dict[str, Any]) -> dict[str, Any]:
        result = deepcopy(command)

        visible_commands = result.setdefault("commands", {})
        source_commands = self.command_ir.get("commands", {})

        for name, source in source_commands.items():
            if name in visible_commands:
                continue

            visible_commands[name] = self._overview(source)

        return result

    def _overview(self, command: dict[str, Any]) -> dict[str, Any]:
        overview = {
            "program": command.get("program"),
            "description": command.get("description"),
        }

        metadata = command.get("metadata", {}).copy()
        metadata["context_level"] = "overview"

        overview["metadata"] = metadata

        commands = command.get("commands")
        if commands:
            overview["commands"] = {name: {} for name in commands}

        return overview


def run_passes(
    command: dict[str, Any],
    passes: list[CommandPass],
) -> dict[str, Any]:
    result = command

    for command_pass in passes:
        result = command_pass.apply(result)

    return result
