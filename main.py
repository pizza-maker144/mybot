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
    WebAppInfo,
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

dp = Dispatcher()

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
APP_URL = "https://pizza-maker144.github.io/funnyclicker/app.html"


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
    conn.execute(
        "CREATE TABLE IF NOT EXISTS notes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, text TEXT NOT NULL)"
    )
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


def add_note(user_id, text):
    conn = sqlite3.connect(DB)
    cur = conn.execute("INSERT INTO notes (user_id, text) VALUES (?, ?)", (user_id, text))
    note_id = cur.lastrowid
    conn.commit()
    conn.close()
    return note_id


def get_notes(user_id):
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT id, text FROM notes WHERE user_id = ? ORDER BY id", (user_id,)
    ).fetchall()
    conn.close()
    return rows


def delete_note(user_id, note_id):
    conn = sqlite3.connect(DB)
    cur = conn.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    deleted = cur.rowcount
    conn.commit()
    conn.close()
    return deleted > 0


def note_button_text(text):
    return text if len(text) <= 40 else text[:37] + "..."


def notes_keyboard(rows):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=note_button_text(text), callback_data=f"del:{note_id}")]
            for note_id, text in rows
        ]
    )


class Form(StatesGroup):
    name = State()
    note = State()

@dp.message(Command("myname"))
async def my_name(message: Message):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT name FROM users WHERE id = ?", (message.from_user.id,)).fetchone()
    conn.close()
    if row:
        await message.answer(f"Тебя зовут: {row[0]}")
    else:
        await message.answer("Я тебя ещё не знаю. Напиши /name")


@dp.message(Command("note"))
async def note(message: Message, state: FSMContext):
    parts = message.text.split(maxsplit=1)
    if len(parts) >= 2 and parts[1].strip():
        note_id = add_note(message.from_user.id, parts[1].strip())
        await message.answer(f"Сохранено #{note_id}")
        return
    await state.set_state(Form.note)
    await message.answer("Напиши текст заметки:")


@dp.message(Command("notes"))
async def notes(message: Message):
    rows = get_notes(message.from_user.id)
    if not rows:
        await message.answer("Заметок пока нет. Добавь: /note текст")
        return
    lines = [f"{note_id}. {text}" for note_id, text in rows]
    await message.answer("\n".join(lines))


@dp.message(Command("del"))
async def del_note(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) >= 2 and parts[1].strip().isdigit():
        if delete_note(message.from_user.id, int(parts[1])):
            await message.answer("Удалено")
        else:
            await message.answer("Такой заметки нет")
        return
    rows = get_notes(message.from_user.id)
    if not rows:
        await message.answer("Заметок нет")
        return
    await message.answer("Выбери заметку для удаления:", reply_markup=notes_keyboard(rows))


@dp.callback_query(F.data.startswith("del:"))
async def on_del(callback: CallbackQuery):
    note_id = int(callback.data.split(":", 1)[1])
    if delete_note(callback.from_user.id, note_id):
        await callback.answer("Удалено")
    else:
        await callback.answer("Уже удалено")
    rows = get_notes(callback.from_user.id)
    if rows:
        await callback.message.edit_text(
            "Выбери заметку для удаления:", reply_markup=notes_keyboard(rows)
        )
    else:
        await callback.message.edit_text("Все заметки удалены")


@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено")


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
    await message.answer(
        "Я умею: /start, /help, /menu, /name, /myname, /weather, /note, /notes, /del"
    )
@dp.message(Command("menu"))
async def menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Привет", callback_data="hello")],
        [InlineKeyboardButton(text="Пока", callback_data="bye")],
    ])
    await message.answer("Выбери кнопку:", reply_markup=kb)


@dp.message(Command("app"))
async def app(message: Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть приложение", web_app=WebAppInfo(url=APP_URL))]
        ]
    )
    await message.answer("Мини-приложение:", reply_markup=kb)


@dp.callback_query(F.data == "hello")
async def on_hello(callback: CallbackQuery):
    await callback.answer("Привет!")
    await callback.message.answer("Ты нажал «Привет»")


@dp.callback_query(F.data == "bye")
async def on_bye(callback: CallbackQuery):
    await callback.answer("Пока!")
    await callback.message.answer("Ты нажал «Пока»")

@dp.message(Form.note)
async def save_note(message: Message, state: FSMContext):
    note_id = add_note(message.from_user.id, message.text.strip())
    await state.clear()
    await message.answer(f"Сохранено #{note_id}")


@dp.message()
async def echo(message: Message):
    await message.answer(f"Ты написал: {message.text}")

async def main():
    init_db()
    bot = Bot(token=TOKEN)
    await bot.set_my_commands([
        BotCommand(command="note", description="Добавить заметку"),
        BotCommand(command="notes", description="Мои заметки"),
        BotCommand(command="del", description="Удалить заметку"),
        BotCommand(command="cancel", description="Отменить действие"),
        BotCommand(command="myname", description="Моё имя"),
        BotCommand(command="weather", description="Погода"),
        BotCommand(command="name", description="Знакомство"),
        BotCommand(command="menu", description="Кнопки"),
        BotCommand(command="app", description="Мини-приложение"),
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="help", description="Что я умею"),
    ])
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
