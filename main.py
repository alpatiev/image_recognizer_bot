import os
import sys
import config
import logging
import aiohttp
import asyncio
import recognizer
from PIL import Image
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Logger setup
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("* SERVER STARTED")
    user = update.effective_user
    await update.message.reply_text("Welcome! Send me image or type /help to list all comands.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("The server is stopped!")
    if os.path.exists('buff.jpg'):
        os.remove('buff.jpg')
        print("* SERVER STOPPED: Buffer image deleted successfully.")
    else:
        print("* SERVER STOPPED: Buffer image not found.")
    sys.exit()

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot is waiting for image. Image must be in .jpg / .jpeg format.\n\nTo change recognition language:\n/ru - Russian\n/en - English\n/ru_en - Russian + English\n\nControl bot:\n/start - Start bot\n/stop - Shut down server\n\nOther:\n/help - List of commands")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo_objects = update.message.photo
    photo_file = await context.bot.get_file(photo_objects[-1])
    if photo_file.file_path.endswith('.jpg') or photo_file.file_path.endswith('.jpeg'): 
        async with aiohttp.ClientSession() as session:
            async with session.get(photo_file.file_path) as response:
                image_bytes = await response.read()
                result_text = recognize_text_from_image(image_bytes, len(image_bytes))
                if result_text != "":
                    await context.bot.send_photo(chat_id=update.message.chat_id, photo=open("buff.jpg", "rb"), caption=result_text)
                else:
                    await context.bot.send_message(chat_id=update.message.chat_id, text="Text not recognized.")
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"Image must be in JPG format.")

async def ru_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("* LOADED IN MEMORY - [RU]")
    recognizer.prepare_reader_model(["ru"])
    await update.message.reply_text("Recognition language is set to Russian.")

async def en_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("* LOADED IN MEMORY - [EN]")
    recognizer.prepare_reader_model(["en"])
    await update.message.reply_text("Recognition language is set to English.")

async def ru_en_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("* LOADED IN MEMORY - [RU, EN]")
    recognizer.prepare_reader_model(["ru", "en"])
    await update.message.reply_text("Recognition languages is set to Russian + English.")

# Logic

def recognize_text_from_image(image_data, size):
    print(f"* START PROCESSING IMG {size} B")
    ocr_result = recognizer.proccess_image(image_data)
    if ocr_result[0] != "":
        ocr_result[1].save('buff.jpg')
        print(f"* RESULT: {ocr_result[1]} {ocr_result[0]}")
    else:
        print(f"* RESULT: TEXT NOT RECOGNIZED")
        if os.path.exists('buff.jpg'):
            os.remove('buff.jpg')
            print("* BUFFER: REMOVED")
        else:
            print("* BUFFER: FAILED TO REMOVE")
    return ocr_result[0]

# Main

def main() -> None:
    # app
    application = Application.builder().token(config.TOKEN).build()

    # commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop))

    # language recognition
    application.add_handler(CommandHandler("ru", ru_language))
    application.add_handler(CommandHandler("en", en_language))
    application.add_handler(CommandHandler("ru_en", ru_en_language))

    # image handling
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # start host
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
