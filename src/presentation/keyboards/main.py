from aiogram.utils.keyboard import InlineKeyboardBuilder

from presentation.keyboards.callbacks import MenuCallback


def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="📥 Скачать", callback_data=MenuCallback(action="download"))
    builder.button(text="🕘 История", callback_data=MenuCallback(action="history"))
    builder.button(text="👤 Профиль", callback_data=MenuCallback(action="profile"))
    builder.button(text="⚙️ Настройки", callback_data=MenuCallback(action="settings"))
    builder.button(text="💎 Помощь", callback_data=MenuCallback(action="help"))
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def back_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data=MenuCallback(action="home"))
    return builder.as_markup()
