import asyncio
import logging
import os
from datetime import datetime
from html import escape

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo
from dotenv import load_dotenv

from .db import Storage
from .scoring import CONFIG, TESTS, InvalidPayload, TestResult, score_payload

load_dotenv()
BOT_TOKEN = os.environ["BOT_TOKEN"]
WEBAPP_URL = os.environ["WEBAPP_URL"]
DB_PATH = os.getenv("DB_PATH", "psycheck.db")

LEVEL_EMOJI = ["🟢", "🟢", "🟡", "🟠", "🔴"]

dp = Dispatcher()
storage = Storage(DB_PATH)


def main_keyboard() -> ReplyKeyboardMarkup:
    # sendData из Mini App работает только при открытии через кнопку обычной клавиатуры
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🧠 Пройти чекап", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )


@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Привет! Я помогу провести короткий <b>психологический чекап</b>: настроение, тревога, "
        "стресс и общее самочувствие.\n\n"
        "Это научно обоснованные скрининговые опросники (PHQ-9, GAD-7, WHO-5, PSS-10). "
        "Они не ставят диагноз, но помогают понять, стоит ли обратить внимание на своё состояние.\n\n"
        "Нажмите кнопку ниже, чтобы начать.\n\n"
        "/history — мои результаты\n/delete — удалить мои данные",
        reply_markup=main_keyboard(),
    )


@dp.message(F.web_app_data)
async def on_webapp_data(message: Message) -> None:
    raw = message.web_app_data.data
    try:
        results = score_payload(raw)
    except InvalidPayload:
        logging.warning("invalid payload from %s", message.from_user.id)
        await message.answer("Не получилось обработать ответы. Попробуйте пройти чекап ещё раз.")
        return

    storage.save(message.from_user.id, raw, results)

    if any(r.crisis for r in results):
        c = CONFIG["crisis"]
        contacts = "\n".join(f"• {escape(x['label'])}: <b>{escape(x['phone'])}</b>" for x in c["contacts"])
        await message.answer(f"❗️ <b>{escape(c['title'])}</b>\n\n{escape(c['text'])}\n\n{contacts}")

    await message.answer(format_report(results), reply_markup=main_keyboard())


def format_report(results: list[TestResult]) -> str:
    lines = ["<b>Ваш психологический чекап</b>\n"]
    for r in results:
        if r.subscales:
            lines.append(format_subscales(r))
            continue
        lines.append(
            f"{LEVEL_EMOJI[r.level]} <b>{escape(r.title)}</b> ({r.name}): {r.total}{r.unit}/{r.max}{r.unit}\n"
            f"<i>{escape(r.label)}</i>. {escape(r.advice)}\n"
        )
    worst = max((r.level for r in results if r.in_summary), default=0)
    if worst >= 3 or any(r.crisis for r in results):
        lines.append("Некоторые показатели говорят о выраженных трудностях. Рекомендуем обратиться к специалисту.")
    elif worst == 2:
        lines.append("Есть показатели, на которые стоит обратить внимание — хорошо бы обсудить их с психологом.")
    else:
        lines.append("В целом всё в пределах нормы. Повторяйте чекап раз в месяц, чтобы видеть динамику.")
    lines.append("\n<i>Результаты скрининга не являются медицинским диагнозом.</i>")
    return "\n".join(lines)


def format_subscales(r: TestResult) -> str:
    notable = [x for x in r.subscales if x.level >= 2]
    head = f"🧩 <b>{escape(r.title)}</b> ({escape(r.name)})"
    if not notable:
        return head + "\nЯрко выраженных ловушек не обнаружено (все шкалы ниже 30 из 60).\n"
    rows = "\n".join(
        f"{LEVEL_EMOJI[x.level]} <b>{escape(x.title)}</b> — {x.total}/60, {escape(x.label.lower())}. "
        f"<i>{escape(x.description)}</i>"
        for x in notable
    )
    return f"{head}\n{rows}\n"


def history_item(r: dict) -> str:
    test = TESTS[r["id"]]
    if "subscales" in r:
        names = {s["id"]: s["title"] for s in test["scoring"]["subscales"]}
        top_id = max(r["subscales"], key=r["subscales"].get)
        return f"🧩 {escape(test['title'])}: {escape(names.get(top_id, top_id))} {r['subscales'][top_id]}"
    return f"{LEVEL_EMOJI[r['level']]} {escape(test['title'])} {r['total']}"


@dp.message(Command("history"))
async def history(message: Message) -> None:
    rows = storage.history(message.from_user.id)
    if not rows:
        await message.answer("У вас пока нет сохранённых результатов.", reply_markup=main_keyboard())
        return
    parts = ["<b>Последние чекапы</b>\n"]
    for row in rows:
        date = datetime.fromisoformat(row["created_at"]).strftime("%d.%m.%Y")
        items = ", ".join(history_item(r) for r in row["results"] if r["id"] in TESTS)
        parts.append(f"<b>{date}</b>: {items}")
    await message.answer("\n".join(parts))


@dp.message(Command("delete"))
async def delete(message: Message) -> None:
    n = storage.delete_user(message.from_user.id)
    await message.answer(f"Удалено записей: {n}. Ваши данные стёрты.")


async def serve_webapp(port: int) -> None:
    """Раздаёт папку webapp/ по HTTP, чтобы не нужен был отдельный хостинг.
    Наружу её выставляет HTTPS-туннель (например, cloudflared)."""
    from pathlib import Path

    from aiohttp import web

    root = Path(__file__).resolve().parent.parent / "webapp"
    app = web.Application()
    app.router.add_get("/", lambda _: web.FileResponse(root / "index.html"))
    app.router.add_static("/", root)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "127.0.0.1", port).start()
    logging.info("Mini App: http://127.0.0.1:%s/", port)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if port := os.getenv("WEBAPP_PORT"):
        await serve_webapp(int(port))
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать"),
        BotCommand(command="history", description="Мои результаты"),
        BotCommand(command="delete", description="Удалить мои данные"),
    ])
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
