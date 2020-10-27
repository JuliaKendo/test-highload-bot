import os
import logging
import textwrap
import phonenumbers

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
        self.updater.dispatcher.add_handler(MessageHandler(Filters.text | Filters.contact, self.handle_users_reply))
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
    show_auth_keyboard(bot, update.message.chat_id)
    return 'HANDLE_AUTH'


def handle_auth(bot, update, params):
    if update.message and update.message.contact:
        phone_number = update.message.contact.phone_number
        if phone_number and phonenumbers.is_valid_number(phonenumbers.parse(phone_number, 'RU')):
            bot.send_message(chat_id=update.message.chat_id, text=f'Введите Ваше Имя и Фамилию:')
            return 'HANDLE_AUTH'
        else:
            message = 'Вы ввели неверный номер телефона. Попробуйте еще раз:'
            bot.send_message(chat_id=update.message.chat_id, text=message)
            return 'HANDLE_AUTH'
    elif update.message and update.message.text:
        if update.message.text == 'Авторизоваться':
            show_send_contact_keyboard(bot, update.message.chat_id)
            bot.delete_message(chat_id=update.message.chat_id, message_id=update.message.message_id)
            return 'HANDLE_AUTH'
        else:
            show_auth_end_keyboard(bot, update.message.chat_id)
            return 'START'


def show_auth_keyboard(bot, chat_id):
    message = textwrap.dedent('''
        Перед началом использования необходимо отправить номер телефона.
        Пожалуйста, нажмите на кнопку Авторизоваться ниже:''')
    auth_keyboard = KeyboardButton(text="Авторизоваться")
    reply_markup = ReplyKeyboardMarkup(
        [[auth_keyboard]],
        one_time_keyboard=True,
        row_width=1,
        resize_keyboard=True
    )
    bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_send_contact_keyboard(bot, chat_id):
    message = '''Продолжая регистрацию вы соглашаетесь с политикой конфиденциальности'''
    contact_keyboard = KeyboardButton(text="Передать контакт", request_contact=True)
    reply_markup = ReplyKeyboardMarkup(
        [[contact_keyboard]],
        one_time_keyboard=True,
        row_width=1,
        resize_keyboard=True
    )
    bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_auth_end_keyboard(bot, chat_id):
    message = '''Благодарим Вас за авторизацию'''
    auth_end_keyboard = KeyboardButton(text="Продолжить")
    reply_markup = ReplyKeyboardMarkup(
        [[auth_end_keyboard]],
        one_time_keyboard=True,
        row_width=1,
        resize_keyboard=True
    )
    bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


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
            'HANDLE_AUTH': handle_auth
        },
        redis_conn=redis_conn
    )
    bot.start()


if __name__ == '__main__':
    main()
