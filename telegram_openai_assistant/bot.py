"""
telegram_openai_assistant.bot
─────────────────────────────
Async, multi-bot runner for python-telegram-bot ≥ 20.8
"""

from __future__ import annotations

import asyncio
import logging
from typing import List

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import telegram_token_bots, assistant_id_bots
from .handlers import BotHandlers

# ───────────────────────── Logging ──────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ───────────────────────── Bot wrapper ──────────────────────
class Bot:
    """One Telegram ↔ OpenAI assistant instance."""

    def __init__(self, telegram_token: str, assistant_id: str) -> None:
        self.telegram_token = telegram_token
        self.assistant_id = assistant_id

        self.application: Application = (
            ApplicationBuilder().token(self.telegram_token).build()
        )

        self.handlers = BotHandlers(self.assistant_id, self.telegram_token)
        self._setup_handlers()

    # ------------------------------------------------------------------
    def _setup_handlers(self) -> None:
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND,
                           self.handlers.process_message)
        )

    # ------------------------------------------------------------------
    async def run(self) -> None:
        """
        Full async life-cycle:

        initialise ➜ start ➜ updater.start_polling ➜ updater.idle
        Blocks until the bot is stopped (Ctrl-C / SIGTERM on Render).
        """
        await self.application.initialize()
        await self.application.bot.set_my_commands(
            [("start", "Start the bot"), ("help", "Show help")]
        )
        await self.application.start()

        # Begin long-polling and block until shutdown signal
        await self.application.updater.start_polling()
        await self.application.updater.idle()   # waits indefinitely

        # Graceful shutdown
        await self.application.stop()
        await self.application.shutdown()


# ─────────────────────── Multi-bot launcher ─────────────────
async def start_bots() -> None:
    if not telegram_token_bots or not assistant_id_bots:
        logger.error(
            "No tokens or assistant IDs detected. "
            "Check TELEGRAM_TOKEN_BOT / ASSISTANT_ID_BOT env vars."
        )
        return

    bots: List[Bot] = [
        Bot(token, asst_id)
        for token, asst_id in zip(telegram_token_bots, assistant_id_bots)
    ]

    logger.info("Launching %d bot(s)…", len(bots))
    await asyncio.gather(*(bot.run() for bot in bots))


def main() -> None:
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        logger.info("Shutdown requested — exiting.")


if __name__ == "__main__":
    main()
