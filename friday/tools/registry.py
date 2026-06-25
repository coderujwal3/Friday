from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    examples: list[str]
    handler: Callable[..., str]
    dangerous: bool = False


@dataclass
class ToolRegistry:
    tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        self.tools[tool.name] = tool

    def execute(self, name: str, query: str) -> str:
        if name not in self.tools:
            return f"I do not know how to run '{name}'."
        return self.tools[name].handler(query)

    def examples(self) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for tool in self.tools.values():
            rows.extend((tool.name, example) for example in tool.examples)
        return rows
