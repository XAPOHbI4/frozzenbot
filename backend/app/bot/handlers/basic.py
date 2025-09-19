"""Basic bot handlers."""

from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

from app.config import settings
from app.services.user import UserService

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Handle /start command."""
    user = message.from_user

    # Register or update user in database
    # TODO: Database temporarily disabled
    # user_service = UserService()
    # await user_service.create_or_update_user(
    #     telegram_id=user.id,
    #     username=user.username,
    #     first_name=user.first_name,
    #     last_name=user.last_name
    # )

    # Create main keyboard with only "Каталог" button (as per screenshots)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Каталог",
                    web_app=WebAppInfo(url=f"{settings.WEBAPP_URL}")
                )
            ]
        ]
    )

    welcome_text = f"""
<b>Привет, {user.first_name}!</b> 👋

Пожалуйста, нажмите на голубую кнопку ниже, чтобы сделать заказ. Если её не видно свяжитесь с <b>@telegram</b>

🛒 <b>Для заказа используйте кнопку "Каталог"</b>

В каталоге вы найдете:
• Готовые замороженные блюда
• Детальное описание и цены
• Удобное оформление заказа
• Безопасную оплату через Telegram

💡 <b>Минимальный заказ:</b> 1500₽
🚚 <b>Доставка:</b> 10-15 мин
    """

    await message.answer(
        welcome_text,
        reply_markup=keyboard
    )


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    """Handle /help command."""
    help_text = """
<b>🔹 Помощь по боту</b>

<b>Команды:</b>
/start - Главное меню
/catalog - Открыть каталог товаров
/help - Показать эту справку

<b>Как сделать заказ:</b>
1️⃣ Нажмите "Открыть магазин" или /catalog
2️⃣ Выберите товары и добавьте в корзину
3️⃣ Оформите заказ с контактными данными
4️⃣ Мы свяжемся с вами для подтверждения

<b>Оплата:</b>
{payment_info}

<b>Минимальный заказ:</b> {min_order}₽

По всем вопросам пишите администратору.
    """.format(
        payment_info=settings.payment_card_info,
        min_order=settings.min_order_amount
    )

    await message.answer(help_text)


@router.message(Command("catalog"))
async def cmd_catalog(message: types.Message):
    """Handle /catalog command."""

    await message.answer(
        f"🛒 <b>Каталог товаров</b>\n\n🌐 Откройте в браузере:\n<code>{settings.webapp_url}</code>\n\n💡 Скопируйте ссылку выше"
    )


@router.callback_query(lambda c: c.data == "my_orders")
async def callback_my_orders(callback_query: types.CallbackQuery):
    """Handle my orders callback."""
    # TODO: Implement order history
    await callback_query.answer("Функция в разработке", show_alert=True)