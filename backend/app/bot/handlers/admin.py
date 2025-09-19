"""Admin bot handlers."""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.config import settings
from app.services.product import ProductService
from app.services.order import OrderService

router = Router()

# Filter for admin users only
admin_filter = F.from_user.id == settings.admin_id


@router.message(Command("admin"), admin_filter)
async def cmd_admin(message: types.Message):
    """Handle /admin command - admin panel."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📦 Товары", callback_data="admin_products"),
                InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
                InlineKeyboardButton(text="⚙️ Настройки", callback_data="admin_settings")
            ]
        ]
    )

    admin_text = f"""
<b>👨‍💼 Панель администратора</b>

Добро пожаловать, {message.from_user.first_name}!

Выберите действие:
    """

    await message.answer(admin_text, reply_markup=keyboard)


@router.callback_query(lambda c: c.data == "admin_products", admin_filter)
async def callback_admin_products(callback_query: types.CallbackQuery):
    """Handle admin products callback."""
    product_service = ProductService()
    products_count = await product_service.get_products_count()

    text = f"""
<b>📦 Управление товарами</b>

Всего товаров: {products_count}

Функции:
• Добавление товаров
• Редактирование цен
• Управление остатками
• Категории

<i>Полное управление доступно в веб-панели администратора</i>
    """

    await callback_query.message.edit_text(text)
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "admin_orders", admin_filter)
async def callback_admin_orders(callback_query: types.CallbackQuery):
    """Handle admin orders callback."""
    order_service = OrderService()
    stats = await order_service.get_orders_stats()

    text = f"""
<b>📋 Управление заказами</b>

Всего заказов: {stats.get('total', 0)}
Новые: {stats.get('pending', 0)}
В работе: {stats.get('processing', 0)}
Выполненные: {stats.get('completed', 0)}

<i>Полное управление доступно в веб-панели администратора</i>
    """

    await callback_query.message.edit_text(text)
    await callback_query.answer()


@router.callback_query(lambda c: c.data == "admin_stats", admin_filter)
async def callback_admin_stats(callback_query: types.CallbackQuery):
    """Handle admin statistics callback."""
    text = """
<b>📊 Статистика</b>

• Продажи за сегодня
• Популярные товары
• Средний чек
• Конверсия

<i>Детальная статистика доступна в веб-панели</i>
    """

    await callback_query.message.edit_text(text)
    await callback_query.answer()


@router.message(Command("stats"), admin_filter)
async def cmd_stats(message: types.Message):
    """Handle /stats command - quick stats."""
    product_service = ProductService()
    order_service = OrderService()

    products_count = await product_service.get_products_count()
    orders_stats = await order_service.get_orders_stats()

    stats_text = f"""
<b>📊 Быстрая статистика</b>

<b>Товары:</b> {products_count}
<b>Заказы:</b>
• Всего: {orders_stats.get('total', 0)}
• Новые: {orders_stats.get('pending', 0)}
• Выполненные: {orders_stats.get('completed', 0)}

<i>Обновлено: сейчас</i>
    """

    await message.answer(stats_text)