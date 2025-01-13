from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from app.database.requests import get_channels_by_user

async def channels(user_id):
    all_channels = await get_channels_by_user(user_id, 'creator')
    keyboard = InlineKeyboardBuilder()
    print("All channels", user_id)
    for p in all_channels:
        print(p.id, p.name, p.tg_id)
        keyboard.add(InlineKeyboardButton(text=p.name, callback_data=f"channel_{p.tg_id}"))
    return keyboard.adjust(1).as_markup()


async def menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='Управление каналом', callback_data='administration'))
    keyboard.add(InlineKeyboardButton(text='Найти пост', callback_data='find_post'))
    return keyboard.adjust(2).as_markup()








main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Управление каналом', callback_data='channel_administration')],
    [InlineKeyboardButton(text='Найти пост', callback_data='find_post')]
], resize_keyboard=True,
input_field_placeholder='Выберите пункт меню')