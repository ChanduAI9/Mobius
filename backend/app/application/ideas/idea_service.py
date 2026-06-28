import json
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import IdeaStatus
from app.infrastructure.ai.provider_registry import llm_registry
from app.infrastructure.database.models import IdeaModel, TaskModel

IDEA_TRIGGER_PATTERNS = [
    r"\bi have an idea\b",
    r"\bi've got an idea\b",
    r"\bnew idea\b",
    r"\bstartup idea\b",
    r"\bwhat if we\b.+\b(build|create|make|start)\b",
]

IDEA_ANALYSIS_PROMPT = """Analyze this idea thoroughly. Return ONLY valid JSON with these fields:
{
  "summary": "2-3 sentence summary",
  "business_value": "Assessment of business value (low/medium/high) with explanation",
  "implementation_effort": "Estimate (low/medium/high) with key work items",
  "weaknesses": "Key weaknesses and risks",
  "improvements": "Suggested improvements",
  "analysis": {
    "feasibility": 0.0-1.0,
    "complexity": "low|medium|high",
    "cost": "low|medium|high",
    "time": "estimate in weeks/months",
    "market_potential": "low|medium|high",
    "competition": "brief assessment",
    "technical_risk": "low|medium|high",
    "security_impact": "low|medium|high",
    "scalability": "low|medium|high",
    "recommendation": "proceed|refine|reconsider",
    "confidence": 0.0-1.0
  },
  "tasks": [
    {"title": "task description", "priority": "low|medium|high"}
  ],
  "follow_up_questions": ["question1", "question2"]
}"""


class IdeaService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def detect_idea_trigger(self, text: str) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in IDEA_TRIGGER_PATTERNS)

    def extract_idea_content(self, text: str) -> str:
        for pattern in [
            r"(?:i have an idea(?:\s+for)?|i've got an idea(?:\s+for)?|new idea:?)\s*(.+)",
            r"(?:what if we)\s+(.+)",
        ]:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return text.strip()

    async def capture(
        self,
        user_id: uuid.UUID,
        raw_input: str,
        project_id: uuid.UUID | None = None,
        conversation_id: uuid.UUID | None = None,
    ) -> dict:
        analysis = await self._analyze_idea(raw_input)

        idea = IdeaModel(
            user_id=user_id,
            project_id=project_id,
            raw_input=raw_input,
            summary=analysis.get("summary"),
            business_value=analysis.get("business_value"),
            implementation_effort=analysis.get("implementation_effort"),
            weaknesses=analysis.get("weaknesses"),
            improvements=analysis.get("improvements"),
            analysis=analysis.get("analysis", {}),
            status=IdeaStatus.NEW.value,
        )
        self._session.add(idea)
        await self._session.flush()

        tasks = []
        for task_data in analysis.get("tasks", [])[:5]:
            task = TaskModel(
                user_id=user_id,
                project_id=project_id,
                idea_id=idea.id,
                title=task_data.get("title", "Untitled task"),
                priority=task_data.get("priority", "medium"),
            )
            self._session.add(task)
            tasks.append(task)
        await self._session.flush()

        return {
            **self._idea_dict(idea),
            "tasks": [self._task_dict(t) for t in tasks],
            "follow_up_questions": analysis.get("follow_up_questions", []),
            "related_ideas": await self._find_related(user_id, raw_input, idea.id),
        }

    async def list_ideas(self, user_id: uuid.UUID, limit: int = 20, offset: int = 0) -> tuple[list[dict], int]:
        from sqlalchemy import func

        query = (
            select(IdeaModel)
            .where(IdeaModel.user_id == user_id)
            .order_by(IdeaModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(query)
        ideas = result.scalars().all()
        total = (
            await self._session.execute(select(func.count()).select_from(IdeaModel).where(IdeaModel.user_id == user_id))
        ).scalar() or 0
        return [self._idea_dict(i) for i in ideas], total

    async def get_idea(self, idea_id: uuid.UUID, user_id: uuid.UUID) -> dict | None:
        result = await self._session.execute(
            select(IdeaModel).where(IdeaModel.id == idea_id, IdeaModel.user_id == user_id)
        )
        idea = result.scalar_one_or_none()
        if not idea:
            return None
        tasks_result = await self._session.execute(select(TaskModel).where(TaskModel.idea_id == idea_id))
        tasks = tasks_result.scalars().all()
        return {**self._idea_dict(idea), "tasks": [self._task_dict(t) for t in tasks]}

    async def update_idea(self, idea_id: uuid.UUID, user_id: uuid.UUID, **updates) -> dict | None:
        result = await self._session.execute(
            select(IdeaModel).where(IdeaModel.id == idea_id, IdeaModel.user_id == user_id)
        )
        idea = result.scalar_one_or_none()
        if not idea:
            return None
        for key, value in updates.items():
            if value is not None and hasattr(idea, key):
                setattr(idea, key, value)
        idea.updated_at = datetime.now(UTC)
        await self._session.flush()
        return self._idea_dict(idea)

    async def _analyze_idea(self, raw_input: str) -> dict:
        provider = llm_registry.get_with_fallback()
        try:
            response = await provider.complete(
                [{"role": "user", "content": f"Idea: {raw_input}"}],
                system=IDEA_ANALYSIS_PROMPT,
                temperature=0.5,
            )
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return self._fallback_analysis(raw_input)

    def _fallback_analysis(self, raw_input: str) -> dict:
        return {
            "summary": raw_input[:200],
            "business_value": "Requires further analysis",
            "implementation_effort": "medium",
            "weaknesses": "Analysis pending—configure an LLM provider for full analysis",
            "improvements": "Define target market and MVP scope",
            "analysis": {
                "feasibility": 0.5,
                "complexity": "medium",
                "recommendation": "refine",
                "confidence": 0.3,
            },
            "tasks": [{"title": "Validate problem with potential users", "priority": "high"}],
            "follow_up_questions": [
                "Who is the target customer?",
                "What problem does this solve?",
                "What's your unfair advantage?",
            ],
        }

    async def _find_related(self, user_id: uuid.UUID, raw_input: str, exclude_id: uuid.UUID) -> list[dict]:
        result = await self._session.execute(
            select(IdeaModel)
            .where(IdeaModel.user_id == user_id, IdeaModel.id != exclude_id)
            .order_by(IdeaModel.created_at.desc())
            .limit(3)
        )
        return [{"id": str(i.id), "summary": i.summary or i.raw_input[:100]} for i in result.scalars().all()]

    @staticmethod
    def _idea_dict(idea: IdeaModel) -> dict:
        return {
            "id": str(idea.id),
            "user_id": str(idea.user_id),
            "project_id": str(idea.project_id) if idea.project_id else None,
            "raw_input": idea.raw_input,
            "summary": idea.summary,
            "business_value": idea.business_value,
            "implementation_effort": idea.implementation_effort,
            "weaknesses": idea.weaknesses,
            "improvements": idea.improvements,
            "analysis": idea.analysis or {},
            "status": idea.status,
            "created_at": idea.created_at.isoformat(),
            "updated_at": idea.updated_at.isoformat(),
        }

    @staticmethod
    def _task_dict(task: TaskModel) -> dict:
        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
        }
