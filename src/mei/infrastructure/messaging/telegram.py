import httpx

from mei.shared.logging import get_logger

logger = get_logger(__name__)


class TelegramClient:
    def __init__(self, bot_token: str | None = None, default_chat_id: str | None = None) -> None:
        self._token = bot_token
        self._chat_id = default_chat_id

    async def send_message(self, text: str, chat_id: str | None = None) -> bool:
        target_chat = chat_id or self._chat_id
        if not self._token or not target_chat:
            logger.warning(
                "telegram.dispatch_skipped",
                reason="Telegram credentials not configured. Notification was simulated.",
                token_configured=bool(self._token),
                chat_id_configured=bool(target_chat),
                text=text,
            )
            return True

        url = f"https://api.telegram.org/bot{self._token}/sendMessage"
        payload = {"chat_id": target_chat, "text": text}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10)
                resp.raise_for_status()
            logger.info("telegram.dispatch_success", chat_id=target_chat)
            return True
        except Exception as exc:
            logger.error("telegram.dispatch_failed", chat_id=target_chat, error=str(exc))
            raise


__all__ = ["TelegramClient"]
