import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from utils import save_default_thumbnail, apply_thumbnail

TOKEN = os.getenv("BOT_TOKEN")
THUMB_DIR = "thumbs"
DEFAULT_THUMB_PATH = os.path.join(THUMB_DIR, "default.jpg")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("היי! שלח לי קובץ PDF או EPUB ואצרף לו thumbnail.")

async def set_thumb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("אנא שלח תמונה.")
        return
    file = await update.message.photo[-1].get_file()
    await file.download_to_drive(DEFAULT_THUMB_PATH)
    await update.message.reply_text("התמונה הוגדרה כברירת מחדל ל-thumbnail!")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith((".pdf", ".epub")):
        await update.message.reply_text("רק קבצי PDF או EPUB נתמכים.")
        return
    temp_path = os.path.join(THUMB_DIR, doc.file_name)
    new_path = os.path.join(THUMB_DIR, "with_thumb_" + doc.file_name)
    file = await doc.get_file()
    await file.download_to_drive(temp_path)
    result = apply_thumbnail(temp_path, new_path, DEFAULT_THUMB_PATH)
    if result:
        await update.message.reply_document(document=open(new_path, "rb"))
    else:
        await update.message.reply_text("ארעה שגיאה במהלך הטמעת התמונה.")

if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Missing BOT_TOKEN environment variable.")
    os.makedirs(THUMB_DIR, exist_ok=True)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setthumb", set_thumb))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.run_polling()