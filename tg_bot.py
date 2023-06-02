import logging
import os
import redis
import re

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
        redis_connection = context.bot_data['redis_connection']
        question, answer = choice(list(quiz.items()))
        update.message.reply_text(question, reply_markup=reply_markup)
        redis_connection.set(update.message.chat_id, answer)
        print(redis_connection.get(update.message.chat_id))
    else:
        redis_connection = context.bot_data['redis_connection']
        correct_answer = redis_connection.get(update.message.chat_id)
        user_answer = update.message.text
        if user_answer.lower() in correct_answer.lower():
            update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».')
        else:
            update.message.reply_text('Неправильно... Попробуешь ещё раз?')


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    tg_bot_api_token = os.environ["TG_BOT_API_TOKEN"]
    updater = Updater(tg_bot_api_token)
    redis_connection = redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=os.environ["REDIS_PORT"],
        password=os.environ["REDIS_PASSWORD"],
        username=os.environ["REDIS_USERNAME"],
        db=0,
        decode_responses=True
    )
    quiz = open_quiz('./quiz-questions/1vs1200.txt')
    dispatcher = updater.dispatcher
    dispatcher.bot_data['quiz'] = quiz
    dispatcher.bot_data['redis_connection'] = redis_connection
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, reply))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
