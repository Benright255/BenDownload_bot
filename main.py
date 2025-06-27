from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
import subprocess, os

import logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7669956648:AAHlE5QVstECzeR4n3DgWK5RAX5ytH7QYDQ"

user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📘 Facebook", callback_data='facebook')],
        [InlineKeyboardButton("📸 Instagram", callback_data='instagram')],
        [InlineKeyboardButton("📺 YouTube", callback_data='youtube')],
        [InlineKeyboardButton("🐦 Twitter", callback_data='twitter')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎯 *Choose video you need to download*", reply_markup=reply_markup, parse_mode='Markdown')

async def handle_platform_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    platform = query.data
    user_state[user_id] = {'platform': platform}
    await query.edit_message_text(f"📥 Send the {platform.capitalize()} video link")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    link = update.message.text

    if user_id not in user_state:
        await update.message.reply_text("⚠️ Please choose a platform first by using /start.")
        return

    user_state[user_id]['link'] = link
    await update.message.reply_text("⏳ Please wait while we prepare your download...")

    keyboard = [
        [InlineKeyboardButton("⬇️ Download Video", callback_data='video')],
        [InlineKeyboardButton("🎧 Download Audio", callback_data='audio')]
    ]
    await update.message.reply_text("Select format:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_format_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_state or 'link' not in user_state[user_id]:
        await query.edit_message_text("⚠️ No link found. Please send the video link first.")
        return

    if query.data == 'video':
        keyboard = [
            [InlineKeyboardButton("🔹 360p", callback_data='v_360')],
            [InlineKeyboardButton("🔸 720p", callback_data='v_720')],
            [InlineKeyboardButton("🔶 1080p", callback_data='v_1080')]
        ]
        await query.edit_message_text("Choose video quality:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'audio':
        keyboard = [
            [InlineKeyboardButton("🎵 64kbps", callback_data='a_64')],
            [InlineKeyboardButton("🎶 128kbps", callback_data='a_128')],
            [InlineKeyboardButton("🎧 320kbps", callback_data='a_320')]
        ]
        await query.edit_message_text("Choose audio quality:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    selection = query.data
    link = user_state[user_id]['link']

    if selection.startswith("v_"):
        quality = selection.replace("v_", "")
        filename = f"video_{user_id}.mp4"
        await query.edit_message_text(f"📥 Downloading video ({quality})...")

        try:
            subprocess.run(["yt-dlp", "-f", f"best[height={quality}]", "-o", filename, link], check=True)
            await query.message.reply_video(video=open(filename, "rb"))
            os.remove(filename)
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {e}")

    elif selection.startswith("a_"):
        bitrate = selection.replace("a_", "")
        filename = f"audio_{user_id}.mp3"
        await query.edit_message_text(f"🎧 Downloading audio ({bitrate}kbps)...")

        try:
            subprocess.run([
                "yt-dlp", "-x", "--audio-format", "mp3",
                "--audio-quality", bitrate, "-o", filename, link
            ], check=True)
            await query.message.reply_audio(audio=open(filename, "rb"))
            os.remove(filename)
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {e}")

    user_state.pop(user_id, None)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_platform_choice, pattern='^(facebook|instagram|youtube|twitter)$'))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_handler(CallbackQueryHandler(handle_format_choice, pattern='^(video|audio)$'))
    app.add_handler(CallbackQueryHandler(handle_download, pattern='^(v_|a_).*'))
    print("🤖 Bot is running...")
    app.run_polling()
