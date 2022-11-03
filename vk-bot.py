import random

import redis
import vk_api as vk
from vk_api.longpoll import VkLongPoll, VkEventType
from environs import Env


def echo(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message=event.text,
        random_id=random.randint(1, 1000)
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
            echo(event, vk_api)


if __name__ == '__main__':
    main()
