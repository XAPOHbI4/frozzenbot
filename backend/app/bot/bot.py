"""Main bot instance and setup."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot instance
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

# Dispatcher
dp = Dispatcher()


async def setup_bot() -> None:
    """Setup bot with handlers and middlewares."""
    from app.bot.handlers import setup_handlers
    from app.bot.middlewares import setup_middlewares

    # Setup middlewares
    setup_middlewares(dp)

    # Setup handlers
    setup_handlers(dp)

    logger.info("Bot setup completed")


async def start_bot() -> None:
    """Start bot polling."""
    await setup_bot()
    await dp.start_polling(bot)


async def stop_bot() -> None:
    """Stop bot and cleanup."""
    await bot.session.close()
    logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        asyncio.run(stop_bot())