"""Punto de entrada del bot de Telegram."""
import asyncio
import logging
import os
import tempfile

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import agent
import config
import storage

logging.basicConfig(level=logging.INFO)
for logger_name in ("httpx", "httpcore", "httpx2", "httpcore2"):
    logging.getLogger(logger_name).setLevel(logging.WARNING)

WELCOME = (
    "¡Hola! Soy tu tutor de idiomas 🇬🇧🇫🇷\n\n"
    "Puedes conversar conmigo con tus propias palabras, sin seguir un guion. "
    "También puedes enviarme una nota de voz o una imagen para describirla.\n\n"
    "Elige una opción para empezar o simplemente escríbeme."
)

TOPIC_LABELS = {
    "daily": "☀️ Mi día",
    "food": "🍜 Comida",
    "travel": "✈️ Viajes",
    "hobbies": "🎨 Pasatiempos",
}


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇬🇧 Inglés", callback_data="lang:en"),
                InlineKeyboardButton("🇫🇷 Francés", callback_data="lang:fr"),
            ],
            [InlineKeyboardButton("💬 Conversar por tema", callback_data="menu:topics")],
            [
                InlineKeyboardButton("🎙️ Pronunciación", callback_data="action:practice"),
                InlineKeyboardButton("📊 Progreso", callback_data="action:progress"),
            ],
            [InlineKeyboardButton("🎚️ Elegir nivel", callback_data="menu:levels")],
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🇬🇧 Inglés", callback_data="lang:en"),
                InlineKeyboardButton("🇫🇷 Francés", callback_data="lang:fr"),
            ],
            [InlineKeyboardButton("↩️ Menú", callback_data="menu:home")],
        ]
    )


def level_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(level, callback_data=f"level:{level}")
                for level in config.LEVELS[:2]
            ],
            [
                InlineKeyboardButton(level, callback_data=f"level:{level}")
                for level in config.LEVELS[2:4]
            ],
            [InlineKeyboardButton(config.LEVELS[4], callback_data=f"level:{config.LEVELS[4]}")],
            [InlineKeyboardButton("↩️ Menú", callback_data="menu:home")],
        ]
    )


def topic_keyboard() -> InlineKeyboardMarkup:
    topics = list(TOPIC_LABELS.items())
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(label, callback_data=f"topic:{topic}")
                for topic, label in topics[index : index + 2]
            ]
            for index in range(0, len(topics), 2)
        ]
        + [[InlineKeyboardButton("↩️ Menú", callback_data="menu:home")]]
    )


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        WELCOME, reply_markup=main_menu_keyboard()
    )


async def set_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    code = (ctx.args[0].lower() if ctx.args else "")
    if code not in config.LANGS:
        await update.effective_message.reply_text(
            "Elige el idioma que quieres practicar:", reply_markup=language_keyboard()
        )
        return
    storage.set_profile(update.effective_user.id, lang=code)
    agent.reset_conversation(update.effective_user.id)
    await update.message.reply_text(f"Idioma: {config.LANGS[code]} ✅")


async def set_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    level = (ctx.args[0].upper() if ctx.args else "")
    if level not in config.LEVELS:
        await update.effective_message.reply_text(
            "Elige el nivel que mejor te represente; puedes cambiarlo cuando quieras:",
            reply_markup=level_keyboard(),
        )
        return
    storage.set_profile(update.effective_user.id, level=level)
    await update.message.reply_text(f"Nivel: {level} ✅")


async def practice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(agent.start_practice(update.effective_user.id))


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    agent.cancel_practice(update.effective_user.id)
    await update.effective_message.reply_text(
        "✅ Ejercicio terminado. Puedes iniciar otro con /practice o enviarme una imagen."
    )


async def progress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(agent.progress(update.effective_user.id))


async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()

    user = update.effective_user
    if not user or not query.message:
        return

    data = query.data or ""
    if data.startswith("lang:"):
        code = data.partition(":")[2]
        if code not in config.LANGS:
            await query.edit_message_text(
                "No reconocí ese idioma. Usa /start para volver al menú."
            )
            return
        storage.set_profile(user.id, lang=code)
        agent.reset_conversation(user.id)
        await query.edit_message_text(
            f"¡Listo! Practicaremos {config.LANGS[code]}. Escríbeme cuando quieras.",
            reply_markup=main_menu_keyboard(),
        )
    elif data == "menu:levels":
        await query.edit_message_text(
            "¿Qué nivel prefieres practicar?", reply_markup=level_keyboard()
        )
    elif data.startswith("level:"):
        level = data.partition(":")[2]
        if level not in config.LEVELS:
            await query.edit_message_text(
                "No reconocí ese nivel. Usa /start para volver al menú."
            )
            return
        storage.set_profile(user.id, level=level)
        await query.edit_message_text(
            f"Nivel actualizado a {level}. Puedes cambiarlo cuando quieras.",
            reply_markup=main_menu_keyboard(),
        )
    elif data == "menu:topics":
        await query.edit_message_text(
            "Elige un tema o escríbeme libremente sobre lo que te apetezca:",
            reply_markup=topic_keyboard(),
        )
    elif data.startswith("topic:"):
        topic = data.partition(":")[2]
        if topic not in TOPIC_LABELS:
            await query.edit_message_text(
                "No reconocí ese tema. Usa /start para volver al menú."
            )
            return
        opener = await asyncio.to_thread(agent.start_topic, user.id, topic)
        await query.edit_message_text(opener)
    elif data == "action:practice":
        await query.edit_message_text(agent.start_practice(user.id))
    elif data == "action:progress":
        await query.edit_message_text(agent.progress(user.id))
    elif data == "menu:home":
        await query.edit_message_text(WELCOME, reply_markup=main_menu_keyboard())
    else:
        await query.edit_message_text(
            "No reconocí esa opción. Usa /start para volver al menú."
        )


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    try:
        reply = await asyncio.to_thread(
            agent.handle_text, update.effective_user.id, update.message.text
        )
    except Exception:
        logging.exception("Error en texto")
        reply = "Tuve un problema procesando tu mensaje. Inténtalo de nuevo en un momento."
    await update.message.reply_text(reply)


async def on_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("typing")
    tg_file = await update.message.voice.get_file()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "voice.ogg")
        await tg_file.download_to_drive(path)
        try:
            reply = await asyncio.to_thread(
                agent.handle_voice, update.effective_user.id, path
            )
        except Exception:
            logging.exception("Error en voz")
            reply = "Tuve un problema con el audio. ¿Puedes enviarlo de nuevo?"
    await update.message.reply_text(reply)


async def on_image(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    if not message or not user:
        return

    await message.chat.send_action("typing")
    media = message.photo[-1] if message.photo else message.document
    if not media:
        await message.reply_text("No pude encontrar una imagen en tu mensaje.")
        return

    try:
        reply = await asyncio.to_thread(agent.start_image_practice, user.id)
    except Exception:
        logging.exception("Error iniciando práctica a partir de imagen")
        reply = "No pude iniciar el ejercicio con esa imagen. Inténtalo de nuevo."
    await message.reply_text(reply)


def main():
    if not config.TELEGRAM_TOKEN:
        raise SystemExit("Falta TELEGRAM_TOKEN en el archivo .env")
    if not config.HF_TOKEN:
        raise SystemExit("Falta HF_TOKEN con permiso de inferencia en el archivo .env")
    app = Application.builder().token(config.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lang", set_lang))
    app.add_handler(CommandHandler("level", set_level))
    app.add_handler(CommandHandler("practice", practice))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("progress", progress))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, on_image))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling()


if __name__ == "__main__":
    main()
