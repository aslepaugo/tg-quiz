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

NEW_QUESTION, ANSWER, GIVE_UP = range(3)  # Corrected variable assignments


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_markdown_v2('Привет\! Я бот для викторин\!')
    return NEW_QUESTION


def new_question(update: Update, context: CallbackContext) -> int:
    quiz = context.bot_data['quiz']
    redis_connection = context.bot_data['redis_connection']
    question, answer = choice(list(quiz.items()))
    redis_connection.set(update.message.chat_id, answer)  # Save the correct answer in Redis
    update.message.reply_text(question, reply_markup=reply_markup)
    return ANSWER


def check_answer(update: Update, context: CallbackContext) -> int:
    redis_connection = context.bot_data['redis_connection']
    correct_answer = redis_connection.get(update.message.chat_id)  # Get the correct answer from Redis
    user_answer = update.message.text

    # Remove explanations from the correct answer
    pattern = r'(.*?)(?:\.\s|\(.+?\))'  # Pattern to separate phrases before a period and explanations in parentheses
    match = re.match(pattern, correct_answer)
    if match:
        correct_answer = match.group(1)

    if user_answer.lower() == correct_answer.lower():
        update.message.reply_text('Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».')
        return NEW_QUESTION
    else:
        update.message.reply_text('Неправильно... Попробуешь ещё раз?')

    return ANSWER


def give_up(update: Update, context: CallbackContext) -> int:
    redis_connection = context.bot_data['redis_connection']
    chat_id = update.message.chat_id
    correct_answer = redis_connection.get(chat_id)
    update.message.reply_text(f"Правильный ответ: {correct_answer}")

    return NEW_QUESTION


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
            ANSWER: [
                MessageHandler(Filters.regex('^Сдаться$'), give_up),
                MessageHandler(Filters.text & ~Filters.command, check_answer),
                
            ],
            GIVE_UP: [MessageHandler(Filters.regex('^Сдаться$'), give_up)],
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
