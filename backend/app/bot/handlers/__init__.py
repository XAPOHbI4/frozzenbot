"""Bot handlers."""

from aiogram import Dispatcher

from .basic import router as basic_router
from .admin import router as admin_router
from .payments import router as payments_router
from .orders import router as orders_router
# Import feedback handlers to register them
from . import feedback


def setup_handlers(dp: Dispatcher) -> None:
    """Setup all bot handlers."""
    dp.include_router(basic_router)
    dp.include_router(admin_router)
    dp.include_router(payments_router)
    dp.include_router(orders_router)
    # Feedback handlers are registered directly with dp in feedback.py