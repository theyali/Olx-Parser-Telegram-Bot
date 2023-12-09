from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, dp

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    transport_btn = InlineKeyboardButton('Транспорт', callback_data='transport')
    electronics_btn = InlineKeyboardButton('Электроника', callback_data='electronics')
    reset_btn = InlineKeyboardButton('Снять задачу', callback_data='reset')
    keyboard.add(transport_btn, electronics_btn, reset_btn)
    await bot.send_message(message.chat.id, "Choose an option:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'start')
async def process_callback_start(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вы выбрали Start')

@dp.callback_query_handler(lambda c: c.data == 'transport')
async def process_callback_transport(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вы выбрали Транспорт')

@dp.callback_query_handler(lambda c: c.data == 'electronics')
async def process_callback_electronics(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вы выбрали Электроника')

@dp.callback_query_handler(lambda c: c.data == 'reset')
async def process_callback_reset(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вы выбрали Снять задачу')