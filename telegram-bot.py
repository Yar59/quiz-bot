import logging
from functools import partial

import redis
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from environs import Env

from tools import get_random_question, get_answer

logger = logging.getLogger(__name__)

(
    NEW_QUESTION,
    HANDLE_SOLUTION,
    GIVE_UP,
    CANCEL_QUIZ,
) = range(4)


def start(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Привет, это бот для викторин, чтобы начать викторину введи команду /quiz'
    )


def quiz(update: Update, context: CallbackContext) -> int:
    print(CallbackContext.args)
    custom_keyboard = [
        ['Новый вопрос', 'Сдаться'],
        ['Мой счет', 'Завершить викторину']
    ]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Начинаем викторину",
        reply_markup=reply_markup
    )
    return NEW_QUESTION


def handle_new_question(update: Update, context: CallbackContext, redis_db, file_path) -> int:
    question = get_random_question(file_path)
    update.message.reply_text(question)
    redis_db.set(update.effective_chat.id, question)
    return HANDLE_SOLUTION


def handle_solution_attempt(update: Update, context: CallbackContext, redis_db, file_path) -> int:
    question = redis_db.get(update.effective_chat.id)
    answer = get_answer(file_path, question)
    simple_answer = answer.split("(")[0].split(".")[0]
    if update.message.text.strip() == simple_answer.strip():
        update.message.reply_text('Молодец, ты угадал, хочешь попробовать ещё?')
        return NEW_QUESTION
    else:
        update.message.reply_text('Это неправильный ответ')
        return GIVE_UP


def handle_give_up(update: Update, context: CallbackContext, redis_db, file_path) -> int:
    question = redis_db.get(update.effective_chat.id)
    answer = get_answer(file_path, question)
    update.message.reply_text(f"Правильный ответ: {answer}")
    return NEW_QUESTION


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Надеюсь тебе понравилась викторина!', reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    env = Env()
    env.read_env()
    tg_token = env('TG_TOKEN')
    redis_host = env('REDIS_HOST')
    redis_port = env('REDIS_PORT')
    redis_db = env('REDIS_DB')
    redis_username = env('REDIS_USERNAME')
    redis_password = env('REDIS_PASSWORD')
    file_path = env('QUESTIONS_PATH', 'questions.json')

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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('quiz', quiz)],
        states={
            NEW_QUESTION: [
                MessageHandler(
                    Filters.regex('^Новый вопрос$'),
                    partial(handle_new_question, redis_db=redis_db, file_path=file_path)
                )
            ],
            HANDLE_SOLUTION: [
                MessageHandler(
                    Filters.regex('^Завершить викторину$'),
                    cancel
                ),
                MessageHandler(
                    Filters.text,
                    partial(handle_solution_attempt, redis_db=redis_db, file_path=file_path)
                ),
            ],
            GIVE_UP: [
                MessageHandler(
                    Filters.regex('^Сдаться$'),
                    partial(handle_give_up, redis_db=redis_db, file_path=file_path)
                ),
                MessageHandler(
                    Filters.text,
                    partial(handle_solution_attempt, redis_db=redis_db, file_path=file_path)
                )
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()

