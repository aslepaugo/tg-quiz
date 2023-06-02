import logging
import os
import re
import redis

from dotenv import load_dotenv
from random import choice
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

from quiz_util import open_quiz


logger = logging.getLogger(__name__)
custom_keyboard = [
    ['Новый вопрос', 'Сдаться'],
    ['Мой счет']
]
reply_markup = ReplyKeyboardMarkup(custom_keyboard)

NEW_QUESTION, ANSWER = range(2)  # Состояния разговора


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_markdown_v2('Привет\! Я бот для викторин\!')
    return NEW_QUESTION


def new_question(update: Update, context: CallbackContext) -> int:
    quiz = context.bot_data['quiz']
    redis_connection = context.bot_data['redis_connection']
    question, answer = choice(list(quiz.items()))
    redis_connection.set(update.message.chat_id, answer)  # Сохраняем правильный ответ в Redis
    update.message.reply_text(question, reply_markup=reply_markup)
    return ANSWER


def check_answer(update: Update, context: CallbackContext) -> int:
    redis_connection = context.bot_data['redis_connection']
    correct_answer = redis_connection.get(update.message.chat_id)  # Получаем правильный ответ из Redis
    user_answer = update.message.text

    # Удаляем пояснения из правильного ответа
    pattern = r'(.*?)(?:\.\s|\(.+?\))'  # Паттерн для разделения на фразы перед точкой и пояснениями в скобках
    match = re.match(pattern, correct_answer)
    print(correct_answer)
    if match:
        correct_answer = match.group(1)
    print(correct_answer)
    if user_answer.lower() == correct_answer.lower():
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».')
        return NEW_QUESTION
    else:
        update.message.reply_text('Неправильно... Попробуешь ещё раз?')

    return ANSWER


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text('Диалог завершен.')
    return ConversationHandler.END


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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NEW_QUESTION: [MessageHandler(Filters.regex('^Новый вопрос$'), new_question)],
            ANSWER: [MessageHandler(Filters.text & ~Filters.command, check_answer)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_handler)

    dispatcher.bot_data['quiz'] = quiz
    dispatcher.bot_data['redis_connection'] = redis_connection

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
