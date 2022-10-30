import logging

import redis
import telegram
from telegram import Update
from telegram.ext import Updater
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from environs import Env

from tools import get_random_question

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


def echo(update: Update, context: CallbackContext):
    if update.message.text == 'Новый вопрос':
        question, answer = get_random_question('questions.json')
        context.bot.send_message(chat_id=update.effective_chat.id, text=question)
        r.set(update.effective_chat.id, question)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)


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

    r = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

    updater = Updater(token=tg_token)

    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)
    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)
    quiz_handler = CommandHandler('quiz', quiz)
    dispatcher.add_handler(quiz_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()

