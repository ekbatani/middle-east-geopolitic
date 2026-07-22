"""Notification delivery adapters (e.g. Telegram, email)."""

from mei.infrastructure.messaging.telegram import TelegramClient

__all__ = ["TelegramClient"]
