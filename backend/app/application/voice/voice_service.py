import io

from app.config import settings


class VoiceService:
    async def transcribe(self, audio_data: bytes, filename: str) -> dict:
        if settings.openai_api_key:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            audio_file = io.BytesIO(audio_data)
            audio_file.name = filename
            response = await client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            return {"text": response.text, "duration_seconds": None}
        raise RuntimeError("Voice transcription requires OPENAI_API_KEY")

    async def synthesize(self, text: str, voice: str = "alloy") -> bytes:
        if settings.openai_api_key:
            from openai import AsyncOpenAI

            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.audio.speech.create(model="tts-1", voice=voice, input=text)
            return response.content
        raise RuntimeError("Voice synthesis requires OPENAI_API_KEY")
