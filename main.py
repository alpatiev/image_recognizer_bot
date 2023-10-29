import os
import sys
import queue
import random
import config
import logging
import aiohttp
import asyncio
import recognizer
from PIL import Image
from telegram import ForceReply, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Logger setup

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Image processing variables

image_queue = queue.Queue()

# Command handlers

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"* BOT STARTED BY USER: {update.effective_user.full_name}")
    user = update.effective_user
    await update.message.reply_text("Welcome! Send me image or type /help to list all comands.")

async def language_check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if recognizer.language_selected == ["ru"]:
        await update.message.reply_text("Current recognition language is Russian.")
    elif recognizer.language_selected == ["en"]:
        await update.message.reply_text("Current recognition language is English.")
    else:
        await update.message.reply_text("Current recognition languages is Russian + English.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot is waiting for image. Image must be in .jpg / .jpeg format.\n\nTo change recognition language:\n/ru - Russian\n/en - English\n/ru_en - Russian + English\n\nControl bot:\n/start - Start bot\n\nSettings:\n/color - Change text color\n\nOther:\n/language - Show language\n/help - List of commands")

async def ru_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("* LOADED IN MEMORY - [RU]")
    recognizer.prepare_reader_model(["ru"])
    await update.message.reply_text("Recognition language is set to Russian.")

async def en_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("* LOADED IN MEMORY - [EN]")
    recognizer.prepare_reader_model(["en"])
    await update.message.reply_text("Recognition language is set to English.")

async def ru_en_language_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("* LOADED IN MEMORY - [RU, EN]")
    recognizer.prepare_reader_model(["ru", "en"])
    await update.message.reply_text("Recognition languages is set to Russian + English.")

async def color_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("GREEN", callback_data="GREEN")],
                [InlineKeyboardButton("RED", callback_data="RED")],
                [InlineKeyboardButton("BLACK", callback_data="BLACK")],
                [InlineKeyboardButton("BLUE", callback_data="BLUE")],
                [InlineKeyboardButton("PURPLE", callback_data="PURPLE")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Choose color for textboxes: ", reply_markup=reply_markup)

async def color_command_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    recognizer.setup_recognizer_color(config.COLORS_DICT.get(query.data))
    await query.answer()
    await query.edit_message_text(text=f"Selected color: {query.data}")

# Input handlers

async def any_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if random.random() > 0.7:   
        async with aiohttp.ClientSession() as session:
            async with session.get(config.EXCUSES_API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    if data:
                        excuse = data[0]["excuse"]
                        if excuse:
                            await update.message.reply_text(excuse)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photo_objects = update.message.photo
    photo_file = await context.bot.get_file(photo_objects[-1])
    if photo_file.file_path.endswith('.jpg') or photo_file.file_path.endswith('.jpeg'): 
            async with aiohttp.ClientSession() as session:
                async with session.get(photo_file.file_path) as response:
                    image_bytes = await response.read()
                    result_text = await recognize_text_from_image(update,
                                                                  context,
                                                                  image_bytes, 
                                                                  len(image_bytes))
                    if result_text != "":
                        await context.bot.send_photo(chat_id=update.message.chat_id, photo=open("buff.jpg", "rb"), caption=result_text)
                    else:
                        await context.bot.send_message(chat_id=update.message.chat_id, text="Text not recognized.")
    else:
        await context.bot.send_message(chat_id=update.message.chat_id, text=f"Image must be in JPG format.")   

# Logic

async def recognize_text_from_image(update, context, image_data, size):
    print(f"* START PROCESSING IMG {size} B")
    loop = asyncio.get_running_loop()
    ocr_result = await loop.run_in_executor(None, recognizer.proccess_image, image_data)
    if ocr_result[0]!= "":
        await loop.run_in_executor(None, ocr_result[1].save, 'buff.jpg')
        print(f"* RESULT: {ocr_result[1]} {ocr_result[0]}")
    else:
        print(f"* RESULT: TEXT NOT RECOGNIZED")
    return ocr_result[0]

# Main

def main() -> None:
    # app
    application = Application.builder().token(config.TOKEN).build()

    # command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("color", color_command))
    application.add_handler(CommandHandler("language", language_check_command))
    application.add_handler(CommandHandler("ru", ru_language_command))
    application.add_handler(CommandHandler("en", en_language_command))
    application.add_handler(CommandHandler("ru_en", ru_en_language_command))

    # command callbacks
    application.add_handler(CallbackQueryHandler(color_command_button))

    # messages handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message_handler))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))

    # start host
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
