import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.schemas import SynthesizeRequest
from app.application.voice.voice_service import VoiceService
from app.config import settings
from app.dependencies import get_current_user_id, get_voice_service

router = APIRouter(prefix="/voice", tags=["voice"])

ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/wav", "audio/mpeg", "audio/mp3", "audio/ogg", "audio/x-wav"}


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: VoiceService = Depends(get_voice_service),
):
    if file.content_type and file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported audio type: {file.content_type}")

    data = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.max_upload_size_mb}MB")

    try:
        result = await service.transcribe(data, file.filename or "audio.webm")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return result


@router.post("/synthesize")
async def synthesize(
    body: SynthesizeRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    service: VoiceService = Depends(get_voice_service),
):
    try:
        audio = await service.synthesize(body.text, voice=body.voice)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return Response(content=audio, media_type="audio/mpeg")
