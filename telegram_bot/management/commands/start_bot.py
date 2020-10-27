import os
from telegram_bot import redis_lib
from telegram_bot import tg_rebus
# from django.config import settings
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        start_bot()


def start_bot():
    redis_conn = redis_lib.RedisDb(
        os.getenv('REDIS_HOST'),
        os.getenv('REDIS_PORT'),
        os.getenv('REDIS_PASSWORD')
    )

    bot = tg_rebus.TgDialogBot(
        os.getenv('TELEGRAM_ACCESS_TOKEN'),
        {
            'START': tg_rebus.start,
            'HANDLE_REBUS': tg_rebus.handle_rebus
        },
        redis_conn=redis_conn,
        puzzles=None,
        current_rebus=0,
        total_attempts=0,
        successful_attempts=[]
    )
    bot.start()
