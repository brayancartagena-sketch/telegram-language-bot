"""Punto de entrada del bot de Telegram."""
import asyncio
import logging
import os
import tempfile

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import agent
import config
import storage

logging.basicConfig(level=logging.INFO)
for logger_name in ("httpx", "httpcore", "httpx2", "httpcore2"):
    logging.getLogger(logger_name).setLevel(logging.WARNING)

WELCOME = (
    "¡Hola! Soy tu tutor de idiomas 🇬🇧🇫🇷\n\n"
    "Escríbeme, envíame una nota de voz o una imagen y te ayudo a mejorar. "
    "Con una imagen puedes responder con una palabra o una oración, por texto o por voz.\n"
    "/lang en|fr  → idioma a practicar\n"
    "/level A1|A2|B1|B2|C1  → tu nivel\n"
    "/practice  → ejercicio de pronunciación\n"
    "/cancel  → termina el ejercicio actual\n"
    "/progress  → tu progreso"
)


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME)


async def set_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    code = (ctx.args[0].lower() if ctx.args else "")
    if code not in config.LANGS:
        await update.message.reply_text("Usa /lang en o /lang fr")
        return
    storage.set_profile(update.effective_user.id, lang=code)
    await update.message.reply_text(f"Idioma: {config.LANGS[code]} ✅")


async def set_level(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    level = (ctx.args[0].upper() if ctx.args else "")
    if level not in config.LEVELS:
        await update.message.reply_text("Usa /level A1, A2, B1, B2 o C1")
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
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, on_image))
    app.add_handler(MessageHandler(filters.VOICE, on_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    asyncio.set_event_loop(asyncio.new_event_loop())
    app.run_polling()


if __name__ == "__main__":
    main()
