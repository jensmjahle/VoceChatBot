import logging

from openai import AsyncOpenAI

from app.bots.ai_chat.conversation import ConversationHistory
from app.core.config import AIChatConfig
from app.core.models import WebhookPayload
from app.core.registry import BotHandler
from app.core.vocechat_client import VoceChatClient

logger = logging.getLogger(__name__)


class AIChatBot(BotHandler):
    def __init__(
        self,
        api_key: str,
        client: VoceChatClient,
        config: AIChatConfig,
        ollama_base_url: str,
    ) -> None:
        self.api_key = api_key
        self._client = client
        self._config = config
        self._history = ConversationHistory(max_pairs=config.history_length)
        self._ai = AsyncOpenAI(
            base_url=f"{ollama_base_url.rstrip('/')}/v1",
            api_key="ollama",
        )

    async def startup(self) -> None:
        logger.info("AIChatBot started with model '%s'", self._config.model)

    async def handle_webhook(self, payload: WebhookPayload) -> None:
        content = payload.detail.content.strip()

        if not content:
            return

        if content.lower() in ("!clear", "!reset"):
            key = _conv_key(payload)
            await self._history.clear(key)
            await self._reply(payload, "Conversation history cleared.")
            return

        key = _conv_key(payload)
        await self._history.append(key, "user", content)
        history = await self._history.get(key)

        try:
            response = await self._ai.chat.completions.create(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": self._config.system_prompt},
                    *history,
                ],
                temperature=self._config.temperature,
                max_tokens=self._config.max_tokens,
            )
            reply = response.choices[0].message.content or ""
        except Exception as exc:
            logger.error("Ollama API error: %s", exc)
            reply = "Sorry, I could not reach the AI model right now."

        await self._history.append(key, "assistant", reply)
        await self._reply(payload, reply)

    async def _reply(self, payload: WebhookPayload, text: str) -> None:
        if payload.target.gid is not None:
            await self._client.send_to_group(payload.target.gid, text, "text/plain")
        elif payload.target.uid is not None:
            await self._client.send_to_user(payload.from_uid, text, "text/plain")


def _conv_key(payload: WebhookPayload) -> str:
    if payload.target.gid is not None:
        return f"g{payload.target.gid}_{payload.from_uid}"
    return f"u{payload.from_uid}"
