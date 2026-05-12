from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from command import start, stop_bot
from response import handle_response
from dotenv import load_dotenv
from auth import generate_auth_url, logout
from spotify import *

import os
load_dotenv()

TOKEN = os.getenv("Telegram_API")
BOT_USERNAME = "@SpodifyTrack_bot"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(start())


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🚫 *Available Commands:*

/login - Connect your Spotify account
/logout - Disconnect from Spotify
/play <song name> - Search and play a track
/pause - Pause current playback
/resume - Resume paused playback
/nowplaying - Show currently playing track
/add <song name> - Add track to queue
/devices - Show available Spotify devices
/device <name|id> - Select playback device
/stop - Stop the bot
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

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
    telegram_id = str(update.message.chat.id)

    if not context.args:
        await update.message.reply_text("Usage: /play <song name>\nExample: /play Blinding Lights")
        return

    track_name = " ".join(context.args)  
    await update.message.reply_text(play(telegram_id, track_name))

async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    await update.message.reply_text(resume(telegram_id))

async def add_to_queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)

    if not context.args:
        await update.message.reply_text("Usage: /add <song name>\nExample: /add Blinding Lessons")
        return

    track_name = " ".join(context.args)
    await update.message.reply_text(add_queue(telegram_id, track_name))


async def devices_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    await update.message.reply_text(get_devices(telegram_id), parse_mode="Markdown")


async def device_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    if not context.args:
        await update.message.reply_text("Usage: /device <name or id>\nExample: /device My Phone")
        return

    device_query = " ".join(context.args)
    await update.message.reply_text(set_device(telegram_id, device_query), parse_mode="Markdown")


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("login", login_command))
    app.add_handler(CommandHandler("nowplaying", now_playing))
    app.add_handler(CommandHandler("logout", logout_command))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("play", play_command))
    app.add_handler(CommandHandler("resume", resume_command))
    app.add_handler(CommandHandler("add", add_to_queue_command))
    app.add_handler(CommandHandler("devices", devices_command))
    app.add_handler(CommandHandler("device", device_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))



    print("Bot is running...")
    app.run_polling()
            




