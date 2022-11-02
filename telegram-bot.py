import logging
from functools import partial

import redis
import telegram
from telegram import Update
from telegram.ext import Updater
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from environs import Env

from tools import get_random_question, get_answer

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def echo(update: Update, context: CallbackContext, redis_db):
    if update.message.text == 'Новый вопрос':
        question, answer = get_random_question('questions.json')
        context.bot.send_message(chat_id=update.effective_chat.id, text=question)
        redis_db.set(update.effective_chat.id, question)
    elif update.message.text == 'Сдаться':
        question = redis_db.get(update.effective_chat.id)
        answer = get_answer('questions.json', question)
        message = f'Правильный ответ на этот вопрос:\n{answer}'
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    else:
        question = redis_db.get(update.effective_chat.id)
        answer = get_answer('questions.json', question)
        simple_answer = answer.split("(")[0].split(".")[0].split(",")[0]
        if update.message.text.strip() == simple_answer.strip():
            context.bot.send_message(chat_id=update.effective_chat.id, text='Молодец, ты угадал, хочешь попробовать ещё?')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text='Это неправильный ответ')


def quiz(update: Update, context: CallbackContext):
    print(CallbackContext.args)
    custom_keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счет']
    ]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Начинаем викторину",
        reply_markup=reply_markup
    )


def main():
    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    redis_host = env('REDIS_HOST')
    redis_port = env('REDIS_PORT')
    redis_db = env('REDIS_DB')
    redis_username = env('REDIS_USERNAME')
    redis_password = env('REDIS_PASSWORD')

    redis_db = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        username=redis_username,
        password=redis_password,
        decode_responses=True
    )

    updater = Updater(token=tg_token)

    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), partial(echo, redis_db=redis_db))
    dispatcher.add_handler(echo_handler)
    quiz_handler = CommandHandler('quiz', partial(quiz, redis_db=redis_db))
    dispatcher.add_handler(quiz_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()

