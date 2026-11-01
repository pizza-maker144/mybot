# Проект: mybot

Telegram-бот на aiogram 3 (Python 3.13), учебный проект.

## Возможности
- `/start` — приветствие
- `/help` — список умений
- `/menu` — инлайн-кнопки (callback `hello` / `bye`)
- `/name` — знакомство через FSM, имя сохраняется в SQLite
- `/myname` — показать сохранённое имя
- `/weather <город>` — погода через Open-Meteo (без ключа)
- любое другое сообщение — эхо

## Запуск
Из папки проекта (PowerShell):
```powershell
.\venv\Scripts\python.exe main.py
```

## Зависимости
```
venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Проверка перед коммитом
```powershell
.\venv\Scripts\python.exe -m py_compile main.py
.\venv\Scripts\python.exe -m ruff check .
.\venv\Scripts\python.exe -m pytest -q
```

## Правила
- Секреты только в `.env` (`TOKEN=...`), в коде токен не хранить.
- `.env`, `venv/`, `bot.db`, `__pycache__/` не коммитить (см. `.gitignore`).
- На этом ПК `api.telegram.org` доступен только при включённом Cloudflare WARP.
- Git: ветка `main`, remote `origin` (SSH). Коммит — после завершённой и проверенной задачи.
- Код без комментариев, стиль существующих функций сохранять.
