"""
Telegram ⇆ OpenAI multi-bot runner
Compatible with python-telegram-bot ≥ 20.0
------------------------------------------------
• Spins up one Application per (token, assistant_id) pair.
• Uses BotHandlers for command / message handling.
• No Updater — run_polling() is the async entry-point in v20+.
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
    ContextTypes,
    filters,
)

from .config import telegram_token_bots, assistant_id_bots
from .handlers import BotHandlers


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Bot:
    """Single Telegram-OpenAI assistant bot instance."""

    def __init__(self, token: str, assistant_id: str) -> None:
        self.assistant_id = assistant_id
        self.application: Application = ApplicationBuilder().token(token).build()
        self.handlers = BotHandlers(assistant_id=assistant_id)
        self._setup_handlers()

    # ────── Internal helpers ──────────────────────────────────────────
    def _setup_handlers(self) -> None:
        """Plug slash commands & text dispatcher callbacks."""
        self.application.add_handler(CommandHandler("start", self.handlers.start))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.process_message)
        )

    # ────── Lifecycle API ─────────────────────────────────────────────
    async def run(self) -> None:
        """
        Initialise ▸ start ▸ **block** polling until shutdown.
        run_polling() wraps initialise/start/idle/shutdown internally.
        """
        # Set default bot commands (optional)
        await self.application.initialize()
        await self.application.bot.set_my_commands(
            [("start", "Start the bot"), ("help", "Show help")]
        )
        await self.application.shutdown()  # clean init run ended

        # Now run full polling loop (does its own init/start/idle/shutdown)
        await self.application.run_polling()

    async def stop(self) -> None:
        """Gracefully stop & shutdown (not usually needed, but exposed)."""
        await self.application.stop()
        await self.application.shutdown()


# ──────────────────────────────────────────────────────────────────────
# Multi-bot runner
# ──────────────────────────────────────────────────────────────────────
async def start_bots() -> None:
    """
    Spin up every (token, assistant_id) pair concurrently.
    run_polling() blocks per bot, so we wrap each in a task.
    """
    bots: List[Bot] = [
        Bot(token, assistant_id)
        for token, assistant_id in zip(telegram_token_bots, assistant_id_bots)
    ]

    if not bots:
        logger.error("No bots configured — check TELEGRAM_TOKEN_BOT / ASSISTANT_ID_BOT.")
        return

    logger.info("Launching %d bot(s)…", len(bots))
    await asyncio.gather(*(bot.run() for bot in bots))


def main() -> None:
    """Entry-point for console-script `chatbot`."""
    try:
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        # Ensures clean exit on Ctrl-C in local runs
        logger.info("Shutdown requested by user. Exiting…")


if __name__ == "__main__":
    main()
