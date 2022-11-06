import logging

import redis
import vk_api as vk
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from environs import Env

from load_questions import get_random_question, get_answer, load_questions_answers


def handle_messages(event, vk_api, redis_db, questions_answers):
    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.POSITIVE)
    question = redis_db.get(event.user_id)
    if not question:
        question = get_random_question(questions_answers)
        redis_db.set(event.user_id, question)
        vk_api.messages.send(
            user_id=event.user_id,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard(),
            message='Рады приветствовать тебя на нашей викторине, жми "Новый вопрос" чтобы получить вопрос'
        )
    else:
        answer = get_answer(questions_answers, question)
        if event.text == "Новый вопрос":
            question = get_random_question(questions_answers)
            redis_db.set(event.user_id, question)
            vk_api.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard(),
                message=f'Вопрос:\n{question}'
            )
        elif event.text == "Сдаться":
            question = get_random_question(questions_answers)
            redis_db.set(event.user_id, question)
            vk_api.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard(),
                message=f'Правильный ответ:\n{answer}\nВот новый вопрос:\n{question}'
            )
        elif event.text == "Мой счет":
            question = get_random_question(questions_answers)
            redis_db.set(event.user_id, question)
            vk_api.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard(),
                message='Прости, я не умею считать :('
            )
        elif event.text == answer.split("(")[0].split(".")[0]:
            vk_api.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard(),
                message=f'Молодец! Правильный ответ!\nЖми на "Новый вопрос"'
            )
        else:
            vk_api.messages.send(
                user_id=event.user_id,
                random_id=get_random_id(),
                keyboard=keyboard.get_keyboard(),
                message='Это неправильный ответ, попробуй еще раз.'
            )


def main():
    env = Env()
    env.read_env()
    redis_host = env('REDIS_HOST')
    redis_port = env('REDIS_PORT')
    redis_db = env('REDIS_DB')
    redis_username = env('REDIS_USERNAME')
    redis_password = env('REDIS_PASSWORD')
    file_path = env('QUESTIONS_PATH', 'questions.json')
    vk_api_key = env('VK_API_KEY')

    questions_answers = load_questions_answers(file_path)

    redis_db = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        username=redis_username,
        password=redis_password,
        decode_responses=True
    )

    vk_session = vk.VkApi(token=vk_api_key)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            try:
                handle_messages(event, vk_api, redis_db, questions_answers)
            except:
                logging.exception()


if __name__ == '__main__':
    main()
