from eskit.command.passes import (
    run_passes,
    RemoveUnnecessaryFields,
    DeduplicateCommonArgs,
    SelectContexts,
    ContextOverviewPass,
)
from eskit.ai.tool import build_tool_definitions
from typing import Any


class ContextToolBuilder:
    def __init__(
        self,
        command_ir: dict[str, Any],
        contexts: set[str] | None = None,
    ) -> None:
        self.command_ir = command_ir
        self.contexts = contexts or set()
        self._context = None

    def build(self):
        optimized_command_ir = self._optimize(self.command_ir)
        
        tools = self._build_tools(optimized_command_ir, self.available_contexts, self.contexts)
            
        self._context = optimized_command_ir, tools, self.contexts
        return self._context

    def get_context(self):
        if self._context is None:
            return self.build()

        return self._context

    def add_context(self, context):
        self.contexts.add(context)
        self._context = None

    def _optimize(self, command_ir):
        passes = [
            SelectContexts(self.contexts),
            ContextOverviewPass(self.command_ir),
            RemoveUnnecessaryFields(),
            DeduplicateCommonArgs(),
        ]

        return run_passes(command_ir, passes)

    def _build_tools(self, command_ir, available_contexts, active_contexts):
        return build_tool_definitions(command_ir, available_contexts, active_contexts)

    @property
    def available_contexts(self) -> set[str]:
        return {
            "init",
            "pull",
            "cat",
            "host",
            "index",
            "snapshot",
            "repository",
            "archive",
            "reindex",
            "ilm",
            "status",
            "task",
            "job",
        }
