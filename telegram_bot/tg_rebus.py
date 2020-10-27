import os
import json
import random
import textwrap
import rollbar

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

from .models import Rebus
from .views import check_user


rollbar.init(os.getenv('ROLLBAR_TOKEN'))

MAX_PUZZLES_TO_WIN = 3


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
            if check_user(chat_id):
                print('Пользователь найден')
            else:
                print('Пользователь не найден')

            user_state = 'START'
        else:
            user_state = self.params['redis_conn'].get_value(chat_id, 'rebus_state')

        state_handler = self.states_functions[user_state]
        next_state = state_handler(bot, update, self.params)
        self.params['redis_conn'].add_value(chat_id, 'rebus_state', next_state)

    def error(self, bot, update, error):
        rollbar.report_exc_info()


def start(bot, update, params):
    fresh_rebuses = Rebus.objects.get_fresh_rebuses(update.message.chat_id)
    print(fresh_rebuses)
    show_start_keyboard(bot, update.message.chat_id)
    params['look_forward'] = False
    params['current_rebus'] = 0
    params['total_attempts'] = 0
    params['successful_attempts'] = []
    return 'HANDLE_REBUS'


def handle_rebus(bot, update, params):
    if not update.message or not update.message.text:
        return 'HANDLE_REBUS'
    chat_id = update.message.chat_id
    if update.message.text == 'Начать игру' or 'Продолжить (' in update.message.text:
        params['look_forward'] = False
        params['current_rebus'] = random.choice(
            [value for value in range(len(params['puzzles']) - 1) if value not in params['successful_attempts']]
        )
        show_rebus(bot, chat_id, params['current_rebus'], params['puzzles'])
        delete_messages(bot, chat_id, update.message.message_id, 2)
        return 'HANDLE_REBUS'
    elif update.message.text == 'Получить подсказку':
        show_hint(bot, chat_id, params['current_rebus'], params['puzzles'])
        return 'HANDLE_REBUS'
    elif update.message.text == 'Закончить игру':
        show_end_message(bot, chat_id, params)
        return 'START'
    else:
        return handle_answer(bot, chat_id, update.message.text, params)


def handle_answer(bot, chat_id, answer, params):
    params['total_attempts'] += 1
    if check_answer(chat_id, answer, params):
        add_successful_attempt(params)
        if len(params['successful_attempts']) == MAX_PUZZLES_TO_WIN:
            show_end_message(bot, chat_id, params)
            return 'START'
        else:
            params['look_forward'] = True
            go_to_next_rebus(bot, chat_id, 'Верный ответ. Продолжим?', params)
            return 'HANDLE_REBUS'
    else:
        if params['look_forward']:
            bot.send_message(chat_id=chat_id, text='Нажмите кнопку <<Продолжить>> или <<Закончить игру>>')
        else:
            bot.send_message(chat_id=chat_id, text='Ответ не верный. Попробуйте еще раз.')
        return 'HANDLE_REBUS'


def check_answer(chat_id, answer, params):
    rebus = params['puzzles'][params['current_rebus']]
    return rebus['answer'] == answer


def show_start_keyboard(bot, chat_id):
    message = textwrap.dedent('''
        Разгадайте ребусы и получите подарок.''')
    keyboard = KeyboardButton(text="Начать игру")
    reply_markup = ReplyKeyboardMarkup(
        [[keyboard]],
        one_time_keyboard=True,
        row_width=1,
        resize_keyboard=True
    )
    return bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)


def show_rebus(bot, chat_id, rebus_number, puzzles, description=''):
    rebus = puzzles[rebus_number]
    reply_markup = ReplyKeyboardMarkup(
        [['Получить подсказку'], ['Закончить игру']],
        one_time_keyboard=True,
        row_width=1,
        resize_keyboard=True
    )
    bot.send_photo(
        chat_id=chat_id,
        photo=open(rebus['image'], 'rb'),
        reply_markup=reply_markup,
        caption=' '.join([item for item in (rebus['description'], description) if item])
    )


def show_hint(bot, chat_id, rebus_number, puzzles, description=''):
    rebus = puzzles[rebus_number]
    if rebus['hint']:
        bot.send_message(chat_id=chat_id, text=rebus['hint'])
    else:
        bot.send_message(chat_id=chat_id, text='Подсказка отсутствует')


def go_to_next_rebus(bot, chat_id, description, params):
    reply_markup = ReplyKeyboardMarkup(
        [[f'✅ Продолжить ({len(params["successful_attempts"])} из {params["total_attempts"]} успешно)'], ['Закончить игру']],
        one_time_keyboard=True,
        row_width=1,
        resize_keyboard=True
    )
    bot.send_message(chat_id=chat_id, text=description, reply_markup=reply_markup)


def show_end_message(bot, chat_id, params):
    if len(params['successful_attempts']) == MAX_PUZZLES_TO_WIN:
        message = textwrap.dedent('''
            Поздравляем. Подойдите на стенд Миран,
            покажите данное сообщение и получите рюкзак/сумку!!''')
    else:
        message = textwrap.dedent(f'''
            Спасибо за участие в игре.
            Вы угалади {len(params["successful_attempts"])} из {params["total_attempts"]} ребусов''')

    reply_markup = ReplyKeyboardMarkup(
        [['Игра закончена']],
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


def add_successful_attempt(params):
    params['successful_attempts'].append(params['current_rebus'])


def read_puzzles():
    with open('puzzles.txt', 'r') as file_handler:
        puzzles = json.load(file_handler)
    return puzzles
