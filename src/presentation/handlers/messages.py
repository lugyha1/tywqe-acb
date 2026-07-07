from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from application.use_cases.create_download import CreateDownloadUseCase
from application.use_cases.register_user import RegisterUserUseCase
from domain.entities.user import User
from presentation.keyboards.main import back_menu, main_menu
from presentation.states.download import DownloadStates

router = Router(name="messages")

WELCOME = """━━━━━━━━━━━━━━━━━━━━
🎬 <b>Media Downloader Pro</b>

✨ Ваш премиальный центр загрузки медиа.

📥 Отправьте ссылку или выберите действие ниже.

<b>Поддерживаемые сервисы</b>
• ▶️ YouTube
• 🎵 TikTok
• 📸 Instagram
• 𝕏 X / Twitter
• 📌 Pinterest
━━━━━━━━━━━━━━━━━━━━"""


@router.message(CommandStart())
async def start(message: Message, register_user: RegisterUserUseCase) -> None:
    tg_user = message.from_user
    if tg_user is not None:
        await register_user.execute(
            User(tg_user.id, tg_user.username, tg_user.first_name, tg_user.language_code or "ru")
        )
    await message.answer(WELCOME, reply_markup=main_menu())


@router.message(DownloadStates.waiting_for_link)
async def receive_link(
    message: Message, state: FSMContext, create_download: CreateDownloadUseCase
) -> None:
    progress = await message.answer(
        "╭──────────────╮\n⏳ <b>Проверяем ссылку</b>\n╰──────────────╯\n\n▰▰▱▱▱ 40%"
    )
    download = await create_download.execute(message.from_user.id, message.text or "")
    await state.clear()
    await progress.edit_text(
        "╭──────────────╮\n✨ <b>Задача создана</b>\n╰──────────────╯\n\n"
        f"🆔 <b>Номер:</b> {download.id}\n🎥 <b>Статус:</b> в очереди\n\n━━━━━━━━━━━━━━━━━━━━",
        reply_markup=back_menu(),
    )
