import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable, Awaitable

from sqlalchemy.ext.asyncio import AsyncSession


class ToolName(StrEnum):
    MEMORY_SEARCH = "memory_search"
    KNOWLEDGE_SEARCH = "knowledge_search"
    WEB_SEARCH = "web_search"
    PROJECT_SUMMARY = "project_summary"
    STORE_FINDING = "store_finding"
    RESEARCH = "research"


@dataclass
class ToolResult:
    tool: str
    success: bool
    output: str
    metadata: dict = field(default_factory=dict)


@dataclass
class PlanStep:
    step: int
    tool: ToolName
    query: str
    reason: str


@dataclass
class OrchestrationResult:
    plan: list[PlanStep]
    tool_results: list[ToolResult]
    final_response: str
    agents_used: list[str] = field(default_factory=list)


ToolHandler = Callable[..., Awaitable[ToolResult]]
