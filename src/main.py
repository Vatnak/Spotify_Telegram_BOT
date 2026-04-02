from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from command import start, stop_bot
from response import handle_response
from dotenv import load_dotenv
from auth import generate_auth_url, logout
from spotify import get_now_playing, pause, play

import os
load_dotenv()

TOKEN = os.getenv("Telegram_API")
BOT_USERNAME = "@SpodifyTrack_bot"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(start())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("here are all the list of command")

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(stop_bot())
    context.application.stop_running()
    

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    url = generate_auth_url(telegram_id)  
    await update.message.reply_text(f"Login to Spotify:\n\n{url}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    print(f"User ({update.message.chat.id}) in {message_type}: {text}")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, "").strip()
            response = handle_response(new_text)
        else:
            return
    else:
        response = handle_response(text)

    await update.message.reply_text(response)

async def now_playing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    await update.message.reply_text(get_now_playing(telegram_id))

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    logout(telegram_id)
    await update.message.reply_text("✅ Disconnected from Spotify.")

async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    await update.message.reply_text(pause(telegram_id))


async def play_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.from_user.id)

    if not context.args:
        await update.message.reply_text("Usage: /play <song name>\nExample: /play Blinding Lights")
        return

    track_name = " ".join(context.args)  # joins multi-word names like "APT Rose"
    await update.message.reply_text(play(telegram_id, track_name))


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("nowplaying", now_playing))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("Pause", pause_command))
    app.add_handler(CommandHandler("play", play_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))



    print("Bot is running...")
    app.run_polling()
            




