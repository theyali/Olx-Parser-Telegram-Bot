from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, dp
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from scraper import fetch_and_parse, get_total_pages
import os

OWNER_ID = os.getenv('OWNER_ID')

class Form(StatesGroup):
    category = State()
    keyword = State()
    currency = State()
    price_range = State()


should_continue_parsing = True

def should_continue():
    return should_continue_parsing

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message, user_id=None):
    if user_id is None:
        user_id = message.from_user.id

    if str(user_id) != str(OWNER_ID):
        await bot.send_message(user_id, '❌Вы не владелец бота, доступ запрещен.❌')
        return
    keyboard = InlineKeyboardMarkup()
    transport_btn = InlineKeyboardButton('Транспорт🚘', callback_data='transport')
    electronics_btn = InlineKeyboardButton('Электроника💻', callback_data='elektronika')
    reset_btn = InlineKeyboardButton('Снять задачу🗑', callback_data='reset')
    keyboard.add(transport_btn, electronics_btn, reset_btn)
    await bot.send_message(message.chat.id, "Выберите категорию🛠:", reply_markup=keyboard)


@dp.message_handler(commands=['stop'], state='*')
async def process_stop(message: types.Message, state: FSMContext):
    if str(message.from_user.id) != str(OWNER_ID):
        await bot.send_message(message.chat.id, '❌Вы не владелец бота, доступ запрещен.❌')
        return
    global should_continue_parsing
    should_continue_parsing = False
    await state.finish()
    await bot.send_message(message.chat.id, 'Парсинг остановлен❌')

@dp.callback_query_handler(lambda c: c.data == 'reset', state='*')
async def process_reset(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.finish() 
    await bot.send_message(callback_query.from_user.id, 'Задача снята 👍')
    await send_welcome(callback_query.message, user_id=callback_query.from_user.id)



@dp.callback_query_handler(lambda c: c.data in ['transport', 'elektronika'])
async def process_callback_transport(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.update_data(category=callback_query.data)
    await bot.send_message(callback_query.from_user.id, 'Введите ключевое слово🔎:')
    await Form.keyword.set()

@dp.message_handler(state=Form.keyword)
async def process_keyword(message: types.Message, state: FSMContext):
    keyword = message.text
    await state.update_data(keyword=keyword)
    currency_keyboard = InlineKeyboardMarkup()
    sum_btn = InlineKeyboardButton('Сум', callback_data='UZS')
    usd_btn = InlineKeyboardButton('У.Е.', callback_data='UYE')
    currency_keyboard.add(sum_btn, usd_btn)
    await bot.send_message(message.chat.id, 'Выберите валюту💷:', reply_markup=currency_keyboard)
    await Form.currency.set()

    
@dp.callback_query_handler(lambda c: c.data in ['UZS', 'UYE'], state=Form.currency)
async def process_currency(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    currency = callback_query.data
    await state.update_data(currency=currency)
    await bot.send_message(callback_query.from_user.id, 'Введите диапазон цен в формате "мин-макс"📈:')
    await Form.price_range.set()


async def send_product_data(url: str, chat_id):
    global should_continue_parsing

    async for product_data in fetch_and_parse(url, should_continue):
        if not should_continue_parsing:
            break
        title = product_data['title']
        description = product_data['description']
        price = product_data['price']
        message = f"1️⃣Название: {title}\n2️⃣Описание: {description}\n3️⃣Цена: {price}\n4️⃣Ссылка: {product_data['url']}\n"
        await bot.send_message(chat_id, message)

@dp.message_handler(state=Form.price_range)
async def process_price_range(message: types.Message, state: FSMContext):
    global should_continue_parsing
    should_continue_parsing = True
    price_range = message.text.split('-')

    if len(price_range) != 2 or not price_range[0].isdigit() or not price_range[1].isdigit():
        await bot.send_message(message.chat.id, '⛔️Неверный формат⛔️. Пожалуйста, введите диапазон цен в формате "мин-макс".')
        return
    await bot.send_message(message.chat.id, f"Начало парсинга📥")
    min_price = price_range[0]
    max_price = price_range[1]
    data = await state.get_data()
    keyword = data['keyword']
    category = data['category']
    currency = data['currency']
    base_url = f"https://www.olx.uz/{category}/q-{keyword}/?currency={currency}&search%5Bfilter_float_price:from%5D={min_price}&search%5Bfilter_float_price:to%5D={max_price}"
    while True:
        total_pages = await get_total_pages(base_url, should_continue)
        if not should_continue_parsing or total_pages == 'Мы нашли  0 объявлений':
            break
        for page_number in range(1, total_pages + 1):
            if not should_continue_parsing:
                break
            url = f"{base_url}&page={page_number}"
            await send_product_data(url, message.chat.id)
    if total_pages == 'Мы нашли  0 объявлений':
        await bot.send_message(message.chat.id, "🅾Мы нашли  0 объявлений🅾️")
    keyboard = InlineKeyboardMarkup()
    transport_btn = InlineKeyboardButton('Транспорт🚘', callback_data='transport')
    electronics_btn = InlineKeyboardButton('Электроника💻', callback_data='elektronika')
    reset_btn = InlineKeyboardButton('Снять задачу🗑', callback_data='reset')
    keyboard.add(transport_btn, electronics_btn, reset_btn)
    await bot.send_message(message.chat.id, "Выберите категорию🛠:", reply_markup=keyboard)

    await state.finish()
