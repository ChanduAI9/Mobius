import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.application.agents.orchestrator import Orchestrator
from app.application.conversation.conversation_service import ConversationService
from app.application.memory.memory_service import MemoryService
from app.application.research.research_service import ResearchService
from app.application.tools.tool_orchestrator import ToolOrchestrator
from app.application.knowledge.rag_service import RAGService
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.security.jwt import decode_token

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_conversation(websocket: WebSocket, conversation_id: uuid.UUID):
    await websocket.accept()
    token = websocket.query_params.get("token")
    if not token:
        await websocket.send_json({"type": "error", "message": "Authentication required"})
        await websocket.close()
        return

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.send_json({"type": "error", "message": "Invalid token"})
        await websocket.close()
        return

    user_id = uuid.UUID(payload["sub"])

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") != "message":
                continue

            content = message.get("content", "").strip()
            if not content:
                continue

            agent = message.get("agent")
            space_ids_raw = message.get("space_ids", [])
            space_ids = [uuid.UUID(s) for s in space_ids_raw] if space_ids_raw else None

            async with async_session_factory() as session:
                memory_service = MemoryService(session)
                rag = RAGService(session, memory_service)
                research = ResearchService(session, memory_service)
                orchestrator = Orchestrator(rag, memory_service, research)
                tool_orch = ToolOrchestrator(session)
                conv_service = ConversationService(session, memory_service, orchestrator, tool_orch)

                try:
                    agent_used = orchestrator.get_agent_for_message(content, agent)
                    if tool_orch.needs_tool_orchestration(content):
                        agent_used = "tool_orchestrator"
                    await websocket.send_json({"type": "agent", "agent": agent_used})

                    async for token_chunk in conv_service.stream_message(
                        conversation_id, user_id, content, agent=agent, space_ids=space_ids
                    ):
                        await websocket.send_json({"type": "token", "content": token_chunk})
                    await session.commit()
                    await websocket.send_json({"type": "done", "agent": agent_used})
                except ValueError as e:
                    await websocket.send_json({"type": "error", "message": str(e)})
    except WebSocketDisconnect:
        pass
