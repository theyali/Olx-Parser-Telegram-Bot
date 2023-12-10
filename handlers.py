from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import bot, dp
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from scraper import fetch_and_parse, get_total_pages


class Form(StatesGroup):
    category = State()
    keyword = State()
    currency = State()  # New state for currency selection
    price_range = State()

    


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    transport_btn = InlineKeyboardButton('Транспорт', callback_data='transport')
    electronics_btn = InlineKeyboardButton('Электроника', callback_data='elektronika')
    reset_btn = InlineKeyboardButton('Снять задачу', callback_data='reset')
    keyboard.add(transport_btn, electronics_btn, reset_btn)
    await bot.send_message(message.chat.id, "Choose an option:", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'start')
async def process_callback_start(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вы выбрали Start')

@dp.callback_query_handler(lambda c: c.data == 'reset')
async def process_callback_reset(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, 'Вы выбрали Снять задачу')



@dp.callback_query_handler(lambda c: c.data in ['transport', 'elektronika'])
async def process_callback_transport(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await state.update_data(category=callback_query.data)  # Save the category to the state
    await bot.send_message(callback_query.from_user.id, 'Введите ключевое слово:')
    await Form.keyword.set()

@dp.message_handler(state=Form.keyword)
async def process_keyword(message: types.Message, state: FSMContext):
    keyword = message.text
    await state.update_data(keyword=keyword)
    # Ask for currency selection
    currency_keyboard = InlineKeyboardMarkup()
    sum_btn = InlineKeyboardButton('Сум', callback_data='UZS')
    usd_btn = InlineKeyboardButton('У.Е.', callback_data='UYE')
    currency_keyboard.add(sum_btn, usd_btn)
    await bot.send_message(message.chat.id, 'Выберите валюту:', reply_markup=currency_keyboard)
    await Form.currency.set()

    
@dp.callback_query_handler(lambda c: c.data in ['UZS', 'UYE'], state=Form.currency)
async def process_currency(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    currency = callback_query.data
    await state.update_data(currency=currency)
    await bot.send_message(callback_query.from_user.id, 'Введите диапазон цен в формате "мин-макс":')
    await Form.price_range.set()

@dp.message_handler(state=Form.price_range)
async def process_price_range(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, f"Начало парсинга...")
    price_range = message.text.split('-')
    min_price = price_range[0]
    max_price = price_range[1]
    data = await state.get_data()
    keyword = data['keyword']
    category = data['category']
    currency = data['currency']
    base_url = f"https://www.olx.uz/{category}/q-{keyword}/?currency={currency}&search%5Bfilter_float_price:from%5D={min_price}&search%5Bfilter_float_price:to%5D={max_price}"
    total_pages = await get_total_pages(base_url)
    if total_pages == 'Мы нашли  0 объявлений':
            await bot.send_message(message.chat.id, "🅾Мы нашли  0 объявлений🅾️")
            keyboard = InlineKeyboardMarkup()
            transport_btn = InlineKeyboardButton('Транспорт', callback_data='transport')
            electronics_btn = InlineKeyboardButton('Электроника', callback_data='elektronika')
            reset_btn = InlineKeyboardButton('Снять задачу', callback_data='reset')
            keyboard.add(transport_btn, electronics_btn, reset_btn)
            await bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=keyboard)
            await state.finish()
    else:
        for page_number in range(1, total_pages + 1):
            url = f"{base_url}&page={page_number}"
            parsed_data = await fetch_and_parse(url)
            for product in parsed_data:
                title = product['title']
                description = product['description']
                price = product['price']
                my_message = f"1️⃣Название: {title}\n2️⃣Описание: {description}\n3️⃣Цена: {price}\n4️⃣Cсылка: {product['url']}\n"
                await bot.send_message(message.chat.id, my_message)
        await bot.send_message(message.chat.id, "✅Парсинг завершен.✅")
        keyboard = InlineKeyboardMarkup()
        transport_btn = InlineKeyboardButton('Транспорт', callback_data='transport')
        electronics_btn = InlineKeyboardButton('Электроника', callback_data='elektronika')
        reset_btn = InlineKeyboardButton('Снять задачу', callback_data='reset')
        keyboard.add(transport_btn, electronics_btn, reset_btn)
        await bot.send_message(message.chat.id, "Выберите опцию:", reply_markup=keyboard)
        await state.finish()
