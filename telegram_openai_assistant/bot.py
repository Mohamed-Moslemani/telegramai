"""
telegram_openai_assistant.bot
─────────────────────────────
Spins up one PTB-v20 Application per (token, assistant_id) pair and
delegates all command / message logic to BotHandlers.

Requirements
------------
• python-telegram-bot >= 20.0 (tested 20.8 / 21.0a6)
• asyncio-compatible runtime (Python ≥ 3.9)
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
    """Single Telegram-OpenAI assistant instance."""

    def __init__(self, telegram_token: str, assistant_id: str) -> None:
        self.assistant_id = assistant_id
        self.telegram_token = telegram_token

        # Build PTB Application
        self.application: Application = (
            ApplicationBuilder().token(self.telegram_token).build()
        )

        # Wire handlers (delegate to BotHandlers class)
        self.handlers = BotHandlers(self.assistant_id, self.telegram_token)
        self._setup_handlers()

    # ------------------------------------------------------------------
    def _setup_handlers(self) -> None:
        """Attach slash-command and text handlers."""
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.process_message)
        )

    # ------------------------------------------------------------------
    async def run(self) -> None:
        """
        Initialise ➜ set commands ➜ run_polling (blocks until shutdown).
        """
        await self.application.initialize()

        await self.application.bot.set_my_commands(
            [
                ("start", "Start the bot"),
                ("help", "Show help"),
            ]
        )

        # run_polling() handles start/idle/shutdown internally
        await self.application.run_polling()

    async def stop(self) -> None:
        """Expose a graceful shutdown (rarely needed manually)."""
        await self.application.stop()
        await self.application.shutdown()


# ─────────────────────── Multi-bot launcher ─────────────────
async def start_bots() -> None:
    """
    Create & run every (token, assistant_id) pair concurrently.
    Each Bot.run() blocks; asyncio.gather keeps them alive together.
    """
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

    # Run all bots concurrently (each run() never returns unless shutdown)
    await asyncio.gather(*(bot.run() for bot in bots))


def main() -> None:
    """Entry-point for console-script `chatbot`."""
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received — shutting down.")


if __name__ == "__main__":
    main()
