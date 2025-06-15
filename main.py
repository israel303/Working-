import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from dotenv import load_dotenv

from Utils import add_thumbnail_to_pdf, add_thumbnail_to_epub, get_user_thumbnail_path

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# מצב למעקב אחרי בקשת הגדרת thumbnail
class ThumbnailState(StatesGroup):
    waiting_for_photo = State()

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.reply("👋 ברוך הבא! שלח קובץ PDF או EPUB כדי לקבל אותו עם thumbnail.\n\nלהגדרת thumbnail אישי:\n1. שלח /setthumb\n2. שלח תמונה\n\nלאיפוס התמונה: /resetthumb")

@dp.message_handler(commands=['setthumb'])
async def set_thumbnail_command(message: types.Message):
    await message.reply("📸 שלח עכשיו את התמונה שברצונך להגדיר כ-thumbnail.")
    await ThumbnailState.waiting_for_photo.set()

@dp.message_handler(state=ThumbnailState.waiting_for_photo, content_types=types.ContentTypes.ANY)
async def receive_thumbnail_photo(message: types.Message, state: FSMContext):
    # ננסה לחלץ תמונה גם אם זה קובץ או תמונה רגילה
    if message.photo:
        photo = message.photo[-1]
    elif message.document and message.document.mime_type.startswith("image/"):
        photo = message.document
    else:
        await message.reply("⚠️ אנא שלח תמונה רגילה או קובץ תמונה.")
        return

    photo_path = f"thumbs/{message.from_user.id}.jpg"
    await photo.download(destination_file=photo_path)
    await message.reply("✅ התמונה נשמרה כ-thumbnail בהצלחה.")
    await state.finish()
    photo = message.photo[-1]
    photo_path = f"thumbs/{message.from_user.id}.jpg"
    await photo.download(destination_file=photo_path)
    await message.reply("✅ התמונה נשמרה כ-thumbnail בהצלחה.")
    await state.finish()

@dp.message_handler(commands=['resetthumb'])
async def reset_thumbnail(message: types.Message):
    thumb_path = get_user_thumbnail_path(message.from_user.id)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)
        await message.reply("🔄 התמונה אופסה בהצלחה.")
    else:
        await message.reply("❌ לא קיימת תמונה לשיוך.")

@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_document(message: types.Message):
    document = message.document
    file_name = document.file_name.lower()

    if not (file_name.endswith(".pdf") or file_name.endswith(".epub")):
        await message.reply("⚠️ רק קבצי PDF או EPUB נתמכים.")
        return

    file_path = f"temp/{document.file_name}"
    await document.download(destination_file=file_path)

    thumb_path = get_user_thumbnail_path(message.from_user.id)
    output_path = f"temp/output_{document.file_name}"

    try:
        if file_name.endswith(".pdf"):
            add_thumbnail_to_pdf(file_path, thumb_path, output_path)
        else:
            add_thumbnail_to_epub(file_path, thumb_path, output_path)

        await message.reply_document(InputFile(output_path), caption="📄 הנה הקובץ עם ה-thumbnail שלך.")
    except Exception as e:
        await message.reply(f"❌ שגיאה: {e}")
    finally:
        # ניקוי קבצים זמניים
        if os.path.exists(file_path): os.remove(file_path)
        if os.path.exists(output_path): os.remove(output_path)

if __name__ == '__main__':
    os.makedirs("thumbs", exist_ok=True)
    os.makedirs("temp", exist_ok=True)
    executor.start_polling(dp, skip_updates=True)