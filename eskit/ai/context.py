from eskit.command.passes import (
    run_passes,
    RemoveUnnecessaryFields,
    DeduplicateCommonArgs,
)
from eskit.ai.tool import build_tool_definitions


class ContextToolBuilder:
    def __init__(self, command_ir):
        self.command_ir = command_ir

    def build(self):
        optimized_command_ir = self._optimize(self.command_ir)
        tools = self._build_tools(optimized_command_ir)

        return optimized_command_ir, tools

    def _optimize(self, command_ir):
        passes = [
            RemoveUnnecessaryFields(),
            DeduplicateCommonArgs(),
        ]

        return run_passes(command_ir, passes)

    def _build_tools(self, command_ir):
        return build_tool_definitions(command_ir)
