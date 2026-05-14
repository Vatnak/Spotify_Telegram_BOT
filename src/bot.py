from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from command import start, stop_bot
from response import handle_response
from dotenv import load_dotenv
from auth import generate_auth_url, logout
from spotify import *
from db import get_db_path, init_db
import os
load_dotenv()

TOKEN = os.getenv("Telegram_API")
BOT_USERNAME = "@SpodifyTrack_bot"
USER_STATES = {}

init_db()

def main_menu_keyboard():
    keyboard = [
        [KeyboardButton("▶️ Play"), KeyboardButton("⏸ Pause"), KeyboardButton("▶️ Resume")],
        [KeyboardButton("🎵 Now Playing"), KeyboardButton("➕ Add to Queue"), KeyboardButton("📱 Select Device")],
        [KeyboardButton("🔑 Login"), KeyboardButton("🚪 Logout"), KeyboardButton("❌ Cancel")],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="Tap a button to control Spotify"
    )


def set_user_state(telegram_id: str, state: str):
    USER_STATES[telegram_id] = state


def get_user_state(telegram_id: str) -> str:
    return USER_STATES.get(telegram_id, "idle")


def clear_user_state(telegram_id: str):
    USER_STATES.pop(telegram_id, None)


async def reply_with_poster(update: Update, result, **kwargs):
    if isinstance(result, dict):
        text = result.get("text", "")
        image_url = result.get("image_url")
    else:
        text = str(result)
        image_url = None

    if image_url:
        await update.message.reply_photo(image_url, caption=text, **kwargs)
    else:
        await update.message.reply_text(text, **kwargs)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    clear_user_state(telegram_id)
    await update.message.reply_text(
        start(),
        reply_markup=main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """🚫 Available Commands:

/login — Connect your Spotify account
/logout — Disconnect from Spotify
/play song name — Search and play a track
/pause — Pause current playback
/resume — Resume paused playback
/nowplaying — Show currently playing track
/add song name — Add track to queue
/device name or id — Select playback device
/stop — Stop the bot
/cancel — Cancel current action
    """
    await update.message.reply_text(
        help_text,
        reply_markup=main_menu_keyboard()
    )

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(stop_bot())
    context.application.stop_running()
    

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    clear_user_state(telegram_id)
    await update.message.reply_text("✅ Action cancelled.", reply_markup=main_menu_keyboard())


async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    url = generate_auth_url(telegram_id)  
    await update.message.reply_text(f"Login to Spotify:\n\n{url}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    message_type: str = update.message.chat.type
    text: str = update.message.text.strip()
    state = get_user_state(telegram_id)

    print(f"User ({update.message.chat.id}) in {message_type}: {text} state={state}")

    if message_type == "group":
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, "").strip()
            response = handle_response(new_text)
            await update.message.reply_text(response)
        return

    if text == "❌ Cancel":
        clear_user_state(telegram_id)
        await update.message.reply_text("✅ Action cancelled.", reply_markup=main_menu_keyboard())
        return

    if state == "awaiting_play":
        clear_user_state(telegram_id)
        await reply_with_poster(update, play(telegram_id, text), reply_markup=main_menu_keyboard())
        return

    if state == "awaiting_add":
        clear_user_state(telegram_id)
        await update.message.reply_text(add_queue(telegram_id, text), reply_markup=main_menu_keyboard())
        return

    if state == "awaiting_device":
        clear_user_state(telegram_id)
        await update.message.reply_text(set_device(telegram_id, text), reply_markup=main_menu_keyboard())
        return

    if state != "idle":
        await update.message.reply_text(
            "Please finish the current action first or send /cancel.",
            reply_markup=main_menu_keyboard()
        )
        return

    if text == "▶️ Play":
        set_user_state(telegram_id, "awaiting_play")
        await update.message.reply_text("Send me the song name to play:", reply_markup=main_menu_keyboard())
        return

    if text == "➕ Add to Queue":
        set_user_state(telegram_id, "awaiting_add")
        await update.message.reply_text("Send me the track name to add to queue:", reply_markup=main_menu_keyboard())
        return

    if text == "📱 Select Device":
        devices_text = get_devices(telegram_id)
        set_user_state(telegram_id, "awaiting_device")
        await update.message.reply_text(
            f"{devices_text}\n\nSend me the device name or ID to select:",
            reply_markup=main_menu_keyboard()
        )
        return

    if text == "⏸ Pause":
        await update.message.reply_text(pause(telegram_id), reply_markup=main_menu_keyboard())
        return

    if text == "▶️ Resume":
        await reply_with_poster(update, resume(telegram_id), reply_markup=main_menu_keyboard())
        return

    if text == "🎵 Now Playing":
        await reply_with_poster(update, get_now_playing(telegram_id), reply_markup=main_menu_keyboard())
        return

    if text == "🔑 Login":
        url = generate_auth_url(telegram_id)
        await update.message.reply_text(f"Login to Spotify:\n\n{url}", reply_markup=main_menu_keyboard())
        return

    if text == "🚪 Logout":
        logout(telegram_id)
        await update.message.reply_text("✅ Disconnected from Spotify.", reply_markup=main_menu_keyboard())
        return

    response = handle_response(text)
    await update.message.reply_text(response, reply_markup=main_menu_keyboard())

async def now_playing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    await reply_with_poster(update, get_now_playing(telegram_id))

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
    await reply_with_poster(update, play(telegram_id, track_name))

async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    await reply_with_poster(update, resume(telegram_id))

async def add_to_queue_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)

    if not context.args:
        await update.message.reply_text("Usage: /add <song name>\nExample: /add Blinding Lessons")
        return

    track_name = " ".join(context.args)
    await update.message.reply_text(add_queue(telegram_id, track_name))


async def device_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.message.chat.id)
    if not context.args:
        devices_text = get_devices(telegram_id)
        set_user_state(telegram_id, "awaiting_device")
        await update.message.reply_text(
            f"{devices_text}\n\nSend me the device name or ID to select:",
            reply_markup=main_menu_keyboard()
        )
        return

    device_query = " ".join(context.args)
    await update.message.reply_text(set_device(telegram_id, device_query))


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Missing Telegram_API in environment. Set your bot token in .env.")
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
    app.add_handler(CommandHandler("device", device_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))



    print("Bot is running...")
    print(f"Spotify logins are stored in: {get_db_path()}")
    app.run_polling()
            




