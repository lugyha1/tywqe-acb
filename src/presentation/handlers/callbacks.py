from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from application.use_cases.list_history import ListHistoryUseCase
from presentation.keyboards.callbacks import MenuCallback
from presentation.keyboards.main import back_menu, main_menu
from presentation.states.download import DownloadStates

router = Router(name="callbacks")


@router.callback_query(MenuCallback.filter(F.action == "home"))
async def home(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🏠 <b>Главное меню</b>\n\n"
            "Выберите следующий шаг.\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "download"))
async def ask_link(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(DownloadStates.waiting_for_link)
    await callback.message.edit_text(
        (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📥 <b>Вставьте ссылку</b>\n\n"
            "Поддерживаются YouTube, TikTok, Instagram, X и Pinterest.\n\n"
            "🔐 Ссылка будет проверена безопасно.\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        reply_markup=back_menu(),
    )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action == "history"))
async def history(callback: CallbackQuery, list_history: ListHistoryUseCase) -> None:
    items = await list_history.execute(callback.from_user.id)
    body = (
        "\n".join(f"• #{item.id} — {item.status.value} — {item.title or 'Media'}" for item in items)
        or "История пока пуста."
    )
    await callback.message.edit_text(
        f"━━━━━━━━━━━━━━━━━━━━\n🕘 <b>История</b>\n\n{body}\n━━━━━━━━━━━━━━━━━━━━",
        reply_markup=back_menu(),
    )
    await callback.answer()


@router.callback_query(MenuCallback.filter(F.action.in_({"profile", "settings", "help"})))
async def static_screen(callback: CallbackQuery, callback_data: MenuCallback) -> None:
    titles = {"profile": "👤 Профиль", "settings": "⚙️ Настройки", "help": "💎 Помощь"}
    await callback.message.edit_text(
        (
            f"━━━━━━━━━━━━━━━━━━━━\n{titles[callback_data.action]}\n\n"
            "Скоро здесь появится больше возможностей.\n"
            "━━━━━━━━━━━━━━━━━━━━"
        ),
        reply_markup=back_menu(),
    )
    await callback.answer()
