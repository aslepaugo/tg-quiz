import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters


logger = logging.getLogger(__name__)
custom_keyboard = [
    ['Новый вопрос', 'Сдвться'],
    ['Мой счет']
    ]
reply_markup = ReplyKeyboardMarkup(custom_keyboard)


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2('Привет! Я бот для викторин!')


def reply(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.message.text, reply_markup=reply_markup)


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    tg_bot_api_token = os.environ["TG_BOT_API_TOKEN"]
    updater = Updater(tg_bot_api_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))    
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
