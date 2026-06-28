from collections.abc import AsyncIterator

import httpx
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from app.config import settings


class OpenAIProvider:
    name = "openai"

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self._model = settings.openai_model

    def _ensure_client(self) -> AsyncOpenAI:
        if not self._client:
            raise RuntimeError("OpenAI API key not configured")
        return self._client

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        client = self._ensure_client()
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        api_messages.extend(messages)
        response = await client.chat.completions.create(
            model=self._model,
            messages=api_messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def stream(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        client = self._ensure_client()
        api_messages = []
        if system:
            api_messages.append({"role": "system", "content": system})
        api_messages.extend(messages)
        stream = await client.chat.completions.create(
            model=self._model,
            messages=api_messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta


class AnthropicProvider:
    name = "anthropic"

    def __init__(self) -> None:
        self._client = (
            AsyncAnthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        )
        self._model = settings.anthropic_model

    def _ensure_client(self) -> AsyncAnthropic:
        if not self._client:
            raise RuntimeError("Anthropic API key not configured")
        return self._client

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        client = self._ensure_client()
        response = await client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system or "",
            messages=[{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"],
            temperature=temperature,
        )
        return response.content[0].text

    async def stream(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        client = self._ensure_client()
        async with client.messages.stream(
            model=self._model,
            max_tokens=4096,
            system=system or "",
            messages=[{"role": m["role"], "content": m["content"]} for m in messages if m["role"] != "system"],
            temperature=temperature,
        ) as stream:
            async for text in stream.text_stream:
                yield text


class OllamaProvider:
    name = "ollama"

    def __init__(self) -> None:
        self._base_url = settings.ollama_base_url.rstrip("/")
        self._model = settings.ollama_model

    async def complete(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> str:
        payload = {"model": self._model, "messages": messages, "stream": False, "options": {"temperature": temperature}}
        if system:
            payload["messages"] = [{"role": "system", "content": system}, *messages]
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
            return response.json()["message"]["content"]

    async def stream(
        self,
        messages: list[dict[str, str]],
        *,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        payload = {"model": self._model, "messages": messages, "stream": True, "options": {"temperature": temperature}}
        if system:
            payload["messages"] = [{"role": "system", "content": system}, *messages]
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    import json

                    data = json.loads(line)
                    if content := data.get("message", {}).get("content"):
                        yield content


class LLMProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, OpenAIProvider | AnthropicProvider | OllamaProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "ollama": OllamaProvider(),
        }
        self._fallback_order = ["openai", "anthropic", "ollama"]

    def get(self, name: str | None = None):
        provider_name = name or settings.default_llm_provider
        return self._providers[provider_name]

    def get_with_fallback(self, preferred: str | None = None):
        order = [preferred] if preferred else []
        order.extend([p for p in self._fallback_order if p not in order])
        for name in order:
            provider = self._providers[name]
            if name == "openai" and settings.openai_api_key:
                return provider
            if name == "anthropic" and settings.anthropic_api_key:
                return provider
            if name == "ollama":
                return provider
        raise RuntimeError("No LLM provider configured. Set OPENAI_API_KEY, ANTHROPIC_API_KEY, or use Ollama.")


llm_registry = LLMProviderRegistry()
