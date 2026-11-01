import asyncio
import os
import sqlite3

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

dp = Dispatcher()

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@dp.message(Command("weather"))
async def weather(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Напиши: /weather Москва")
        return
    city = parts[1]
    async with aiohttp.ClientSession() as session:
        async with session.get(GEO_URL, params={"name": city, "count": 1, "language": "ru"}) as resp:
            geo = await resp.json()
        results = geo.get("results")
        if not results:
            await message.answer(f"Не нашёл город «{city}»")
            return
        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        found = results[0]["name"]
        async with session.get(
            WEATHER_URL,
            params={"latitude": lat, "longitude": lon, "current": "temperature_2m,wind_speed_10m"},
        ) as resp:
            data = await resp.json()
    current = data["current"]
    await message.answer(
        f"{found}: {current['temperature_2m']} °C, ветер {current['wind_speed_10m']} км/ч"
    )
DB = "bot.db"


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    conn.commit()
    conn.close()


def save_user(user_id, name):
    conn = sqlite3.connect(DB)
    conn.execute(
        "INSERT INTO users (id, name) VALUES (?, ?) "
        "ON CONFLICT(id) DO UPDATE SET name = excluded.name",
        (user_id, name),
    )
    conn.commit()
    conn.close()

class Form(StatesGroup):
    name = State()

@dp.message(Command("myname"))
async def my_name(message: Message):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT name FROM users WHERE id = ?", (message.from_user.id,)).fetchone()
    conn.close()
    if row:
        await message.answer(f"Тебя зовут: {row[0]}")
    else:
        await message.answer("Я тебя ещё не знаю. Напиши /name")

@dp.message(Command("name"))
async def ask_name(message: Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Как тебя зовут?")


@dp.message(Form.name)
async def save_name(message: Message, state: FSMContext):
    save_user(message.from_user.id, message.text)
    await state.update_data(name=message.text)
    await state.clear()
    await message.answer(f"Запомнил: {message.text}")
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(f"Привет, {message.from_user.first_name}! Я твой первый бот.")

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("Я умею: /start, /help и повторяю твои сообщения.") 
@dp.message(Command("menu"))
async def menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Привет", callback_data="hello")],
        [InlineKeyboardButton(text="Пока", callback_data="bye")],
    ])
    await message.answer("Выбери кнопку:", reply_markup=kb)


@dp.callback_query(F.data == "hello")
async def on_hello(callback: CallbackQuery):
    await callback.answer("Привет!")
    await callback.message.answer("Ты нажал «Привет»")


@dp.callback_query(F.data == "bye")
async def on_bye(callback: CallbackQuery):
    await callback.answer("Пока!")
    await callback.message.answer("Ты нажал «Пока»")

@dp.message()
async def echo(message: Message):
    await message.answer(f"Ты написал: {message.text}")

async def main():
    init_db()
    bot = Bot(token=TOKEN)
    await bot.set_my_commands([
        BotCommand(command="myname", description="Моё имя"),
        BotCommand(command="weather", description="Погода"),
        BotCommand(command="name", description="Знакомство"),
        BotCommand(command="menu", description="Кнопки"),
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Что я умею"),
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
