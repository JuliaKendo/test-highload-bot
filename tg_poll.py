import os
import json
import logging
import textwrap

from dotenv import load_dotenv

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater
)

from libs import logger_lib
from libs import redis_lib

logger = logging.getLogger('hightload_bot')


class TgDialogBot(object):

    def __init__(self, tg_token, states_functions, **params):
        self.tg_token = tg_token
        self.params = params
        self.states_functions = states_functions
        self.updater = Updater(token=tg_token)
        self.updater.dispatcher.add_handler(CallbackQueryHandler(self.handle_users_reply))
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text, self.handle_users_reply))
        self.updater.dispatcher.add_handler(CommandHandler('start', self.handle_users_reply))
        self.updater.dispatcher.add_error_handler(self.error)

    def start(self):
        self.updater.start_polling()

    def handle_users_reply(self, bot, update):
        if update.message:
            user_reply = update.message.text
            chat_id = update.message.chat_id
        elif update.callback_query:
            user_reply = update.callback_query.data
            chat_id = update.callback_query.message.chat_id
        else:
            return

        if user_reply == '/start':
            user_state = 'START'
        else:
            user_state = self.params['redis_conn'].get_value(chat_id, 'state')

        state_handler = self.states_functions[user_state]
        next_state = state_handler(bot, update, self.params)
        self.params['redis_conn'].add_value(chat_id, 'state', next_state)

    def error(self, bot, update, error):
        logger.exception(f'Ошибка бота: {error}')


def start(bot, update, params):
    message = show_start_keyboard(bot, update.message.chat_id)
    params['message_id'] = message.message_id
    params['redis_conn'].add_value(update.message.chat_id, 'question_number', 0)
    return 'HANDLE_POLL'


def handle_poll(bot, update, params):
    if update.message and update.message.text:
        chat_id = update.message.chat_id
        if update.message.text == 'Опрос':
            question_number = int(params['redis_conn'].get_value(chat_id, 'question_number'))
            show_next_question(bot, chat_id, question_number, params['poll_questions'])
            params['redis_conn'].add_value(chat_id, 'question_number', question_number + 1)
            delete_messages(bot, chat_id, update.message.message_id, 2)
            return 'HANDLE_POLL'
        else:
            question_number = handle_choice_of_answer(chat_id, update.message.text, params)
            if not question_number:
                question_number = int(params['redis_conn'].get_value(chat_id, 'question_number'))
            if question_number == len(params['poll_questions']):
                show_end_message(bot, chat_id)
                delete_messages(bot, chat_id, update.message.message_id)
                return 'START'
            else:
                show_next_question(bot, chat_id, question_number, params['poll_questions'])
                params['redis_conn'].add_value(chat_id, 'question_number', question_number + 1)
                delete_messages(bot, chat_id, update.message.message_id, 2)
                return 'HANDLE_POLL'


def handle_choice_of_answer(chat_id, answer, params):
    question_number = int(params['redis_conn'].get_value(chat_id, 'question_number'))
    message = params['poll_questions'][question_number - 1]
    next_question = [item['next_question'] for item in message['answer options'] if item['value'] == answer]
    if next_question:
        return next_question[0]


def show_start_keyboard(bot, chat_id):
    message = textwrap.dedent('''
        Здравствуйте! Примите, пожалуйста, участие в опросе,
        посвященном изучению оценки удовлетворенности работы
        с нашей компанией.
        Ваши ответы помогут нам улучшить нашу работу и сделать
        условия сотрудничества более выгодными для всех клиентов.''')
    keyboard = KeyboardButton(text="Опрос")
    reply_markup = ReplyKeyboardMarkup(
        [[keyboard]],
        one_time_keyboard=True,
        row_width=1,
        resize_keyboard=True
    )
    return bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_next_question(bot, chat_id, question_number, questions):
    message = questions[question_number]
    answer_options = message['answer options']
    if answer_options:
        reply_markup = ReplyKeyboardMarkup(
            [[item['value'] for item in answer_options]],
            one_time_keyboard=True,
            row_width=1,
            resize_keyboard=True
        )
        bot.send_message(chat_id=chat_id, text=message['question'], reply_markup=reply_markup)
    else:
        bot.send_message(chat_id=chat_id, text=message['question'])


def show_end_message(bot, chat_id):
    message = textwrap.dedent('''
        Спасибо за пройденный опрос.
        Подойдите на стенд Миран,
        покажите данное сообщение и получите футболку!!''')
    reply_markup = ReplyKeyboardMarkup(
        [['Завершить опрос']],
        one_time_keyboard=True,
        row_width=1,
        resize_keyboard=True
    )
    bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def delete_messages(bot, chat_id, message_id, message_numbers=1):
    if not message_id:
        return
    for offset_id in range(message_numbers):
        bot.delete_message(chat_id=chat_id, message_id=int(message_id) - offset_id)


def read_poll_questions():
    with open('questions_to_clients.txt', 'r') as file_handler:
        poll_questions = json.load(file_handler)
    return poll_questions


def main():
    load_dotenv()

    logger_lib.initialize_logger(
        logger,
        os.getenv('TG_LOG_TOKEN'),
        os.getenv('TG_CHAT_ID')
    )
    redis_conn = redis_lib.RedisDb(
        os.getenv('REDIS_HOST'),
        os.getenv('REDIS_PORT'),
        os.getenv('REDIS_PASSWORD')
    )

    bot = TgDialogBot(
        os.getenv('TELEGRAM_ACCESS_TOKEN'),
        {
            'START': start,
            'HANDLE_POLL': handle_poll
        },
        redis_conn=redis_conn,
        poll_questions=read_poll_questions()
    )
    bot.start()


if __name__ == '__main__':
    main()
