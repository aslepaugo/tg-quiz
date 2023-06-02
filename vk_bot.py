import logging
import os
import re
import redis
import random

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from dotenv import load_dotenv

from quiz_util import open_quiz


load_dotenv()

keyboard = VkKeyboard(one_time=True)

keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
keyboard.add_line()
keyboard.add_button('Мой счет', color=VkKeyboardColor.PRIMARY)

NEW_QUESTION, ANSWER, GIVE_UP = range(3)


def start(event, vk, quiz, redis_connection):
    print("start")
    print(event.user_id)

    vk.messages.send(
        user_id=event.user_id,
        message='Привет! Я бот для викторин!',
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )
    return NEW_QUESTION


def new_question(event, vk, quiz, redis_connection):
    question, answer = random.choice(list(quiz.items()))
    redis_connection.set(event.user_id, answer)
    vk.messages.send(
        user_id=event.user_id,
        message=question,
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )
    return ANSWER


def check_answer(event, vk, quiz, redis_connection):
    correct_answer = redis_connection.get(event.user_id)
    user_answer = event.text

    pattern = r'(.*?)(?:\.\s|\(.+?\))'
    match = re.match(pattern, correct_answer)
    if match:
        correct_answer = match.group(1)

    if user_answer.lower() == correct_answer.lower():
        vk.messages.send(
            user_id=event.user_id,
            message='Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».',
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )
        return NEW_QUESTION
    else:
        vk.messages.send(
            user_id=event.user_id,
            message='Неправильно... Попробуешь ещё раз?',
            random_id=random.randint(1, 1000),
            keyboard=keyboard.get_keyboard()
        )
    return ANSWER


def give_up(event, vk, quiz, redis_connection):
    correct_answer = redis_connection.get(event.user_id)
    vk.messages.send(
        user_id=event.user_id,
        message=f"Правильный ответ: {correct_answer}",
        random_id=random.randint(1, 1000),
        keyboard=keyboard.get_keyboard()
    )
    return NEW_QUESTION


def main():
    logging.basicConfig(level=logging.INFO)

    vk_token = os.environ["VK_TOKEN"]
    vk_session = vk_api.VkApi(token=vk_token)
    vk = vk_session.get_api()

    redis_connection = redis.Redis(
        host=os.environ["REDIS_HOST"],
        port=os.environ["REDIS_PORT"],
        password=os.environ["REDIS_PASSWORD"],
        username=os.environ["REDIS_USERNAME"],
        db=0,
        decode_responses=True
    )

    quiz = open_quiz('./quiz-questions/1vs1200.txt')
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            print(event.text)
            if event.text == 'Начать':
                state = start(event, vk, quiz, redis_connection)
            elif event.text == 'Новый вопрос':
                state = new_question(event, vk, quiz, redis_connection)
            elif event.text == 'Сдаться':
                state = give_up(event, vk, quiz, redis_connection)
            else:
                state = check_answer(event, vk, quiz, redis_connection)
            if state == ANSWER:
                state = GIVE_UP
            elif state == NEW_QUESTION:
                state = start(event, vk, quiz, redis_connection)


if __name__ == "__main__":
    main()
