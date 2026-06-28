import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.agents.orchestrator import Orchestrator
from app.application.knowledge.rag_service import RAGService
from app.application.memory.memory_service import MemoryService
from app.application.tools.tool_orchestrator import ToolOrchestrator
from app.domain.entities import MessageRole
from app.infrastructure.database.models import ConversationModel, MessageModel


class ConversationService:
    def __init__(
        self,
        session: AsyncSession,
        memory_service: MemoryService,
        orchestrator: Orchestrator | None = None,
        tool_orchestrator: ToolOrchestrator | None = None,
    ) -> None:
        self._session = session
        self._memory = memory_service
        self._orchestrator = orchestrator
        self._tool_orchestrator = tool_orchestrator

    async def create(self, user_id: uuid.UUID, title: str = "New conversation", project_id: uuid.UUID | None = None):
        conv = ConversationModel(user_id=user_id, title=title, project_id=project_id)
        self._session.add(conv)
        await self._session.flush()
        return conv

    async def list_conversations(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0, project_id: uuid.UUID | None = None
    ):
        query = select(ConversationModel).where(ConversationModel.user_id == user_id)
        count_q = select(func.count()).select_from(ConversationModel).where(ConversationModel.user_id == user_id)
        if project_id:
            query = query.where(ConversationModel.project_id == project_id)
            count_q = count_q.where(ConversationModel.project_id == project_id)
        query = query.order_by(ConversationModel.updated_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(query)
        conversations = result.scalars().all()
        total = (await self._session.execute(count_q)).scalar() or 0

        items = []
        for conv in conversations:
            msg_count = (
                await self._session.execute(
                    select(func.count()).select_from(MessageModel).where(MessageModel.conversation_id == conv.id)
                )
            ).scalar() or 0
            items.append({**self._conv_dict(conv), "message_count": msg_count})
        return items, total

    async def get_conversation(self, conversation_id: uuid.UUID, user_id: uuid.UUID):
        result = await self._session.execute(
            select(ConversationModel).where(ConversationModel.id == conversation_id, ConversationModel.user_id == user_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            return None
        messages_result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at)
        )
        messages = messages_result.scalars().all()
        return {**self._conv_dict(conv), "messages": [self._msg_dict(m) for m in messages]}

    async def send_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        attachments: list | None = None,
        agent: str | None = None,
        space_ids: list[uuid.UUID] | None = None,
    ) -> tuple[dict, dict, str]:
        conv = await self._get_conv(conversation_id, user_id)
        user_msg = MessageModel(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
            attachments=attachments or [],
        )
        self._session.add(user_msg)
        await self._session.flush()

        if conv.title == "New conversation":
            conv.title = content[:80] + ("..." if len(content) > 80 else "")
            conv.updated_at = datetime.now(UTC)

        history = await self._get_message_history(conversation_id)
        agent_used = agent or "conversation"

        if self._orchestrator:
            response = await self._orchestrator.process(
                user_id, history, agent_override=agent, space_ids=space_ids,
                tool_orchestrator=self._tool_orchestrator,
            )
            response_text = response.content
            agent_used = response.agent
        else:
            from app.application.conversation.prompts import MOBIUS_SYSTEM_PROMPT
            from app.infrastructure.ai.provider_registry import llm_registry

            memories = await self._memory.retrieve_relevant(user_id, content, limit=5)
            memory_block = "\n".join(f"- [{m.category}] {m.content}" for m in memories)
            system = MOBIUS_SYSTEM_PROMPT
            if memory_block:
                system += f"\n\nRelevant memories:\n{memory_block}"
            provider = llm_registry.get_with_fallback()
            response_text = await provider.complete(history, system=system)

        assistant_msg = MessageModel(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=response_text,
            metadata_={"agent": agent_used},
        )
        self._session.add(assistant_msg)
        conv.updated_at = datetime.now(UTC)
        await self._session.flush()

        await self._memory.extract_from_conversation(user_id, content, response_text, conversation_id)

        return self._msg_dict(user_msg), self._msg_dict(assistant_msg), agent_used

    async def stream_message(
        self,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        content: str,
        agent: str | None = None,
        space_ids: list[uuid.UUID] | None = None,
    ) -> AsyncIterator[str]:
        conv = await self._get_conv(conversation_id, user_id)
        user_msg = MessageModel(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
        )
        self._session.add(user_msg)
        await self._session.flush()

        if conv.title == "New conversation":
            conv.title = content[:80] + ("..." if len(content) > 80 else "")

        history = await self._get_message_history(conversation_id)
        full_response: list[str] = []
        agent_used = agent or "conversation"

        if self._orchestrator:
            agent_used = self._orchestrator.get_agent_for_message(content, agent)
            async for token in self._orchestrator.stream(
                user_id, history, agent_override=agent, space_ids=space_ids,
                tool_orchestrator=self._tool_orchestrator,
            ):
                full_response.append(token)
                yield token
        else:
            from app.application.conversation.prompts import MOBIUS_SYSTEM_PROMPT
            from app.infrastructure.ai.provider_registry import llm_registry

            memories = await self._memory.retrieve_relevant(user_id, content, limit=5)
            memory_block = "\n".join(f"- [{m.category}] {m.content}" for m in memories)
            system = MOBIUS_SYSTEM_PROMPT
            if memory_block:
                system += f"\n\nRelevant memories:\n{memory_block}"
            provider = llm_registry.get_with_fallback()
            async for token in provider.stream(history, system=system):
                full_response.append(token)
                yield token

        assistant_msg = MessageModel(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content="".join(full_response),
            metadata_={"agent": agent_used},
        )
        self._session.add(assistant_msg)
        conv.updated_at = datetime.now(UTC)
        await self._session.flush()

        await self._memory.extract_from_conversation(user_id, content, "".join(full_response), conversation_id)

    async def _get_conv(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> ConversationModel:
        result = await self._session.execute(
            select(ConversationModel).where(ConversationModel.id == conversation_id, ConversationModel.user_id == user_id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise ValueError("Conversation not found")
        return conv

    async def _get_message_history(self, conversation_id: uuid.UUID) -> list[dict[str, str]]:
        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.created_at)
        )
        messages = result.scalars().all()
        return [{"role": m.role, "content": m.content} for m in messages]

    @staticmethod
    def _conv_dict(conv: ConversationModel) -> dict:
        return {
            "id": str(conv.id),
            "title": conv.title,
            "status": conv.status,
            "project_id": str(conv.project_id) if conv.project_id else None,
            "metadata": conv.metadata_ or {},
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        }

    @staticmethod
    def _msg_dict(msg: MessageModel) -> dict:
        return {
            "id": str(msg.id),
            "conversation_id": str(msg.conversation_id),
            "role": msg.role,
            "content": msg.content,
            "attachments": msg.attachments or [],
            "metadata": msg.metadata_ or {},
            "created_at": msg.created_at.isoformat(),
        }
