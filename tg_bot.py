import logging
import os

from dotenv import load_dotenv
from random import choice
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters

from quiz_util import open_quiz


logger = logging.getLogger(__name__)
custom_keyboard = [
    ['Новый вопрос', 'Сдаться'],
    ['Мой счет']
    ]
reply_markup = ReplyKeyboardMarkup(custom_keyboard)


def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2('Привет\! Я бот для викторин\!')


def reply(update: Update, context: CallbackContext) -> None:
    if update.message.text == 'Новый вопрос':
        quiz = context.bot_data['quiz']
        question, answer = choice(list(quiz.items()))
        update.message.reply_text(question, reply_markup=reply_markup)


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    tg_bot_api_token = os.environ["TG_BOT_API_TOKEN"]
    updater = Updater(tg_bot_api_token)
    quiz = open_quiz('./quiz-questions/1vs1200.txt')

    dispatcher = updater.dispatcher
    dispatcher.bot_data['quiz'] = quiz
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
