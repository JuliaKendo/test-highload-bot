from django.shortcuts import render
from datetime import datetime

from .models import User


def check_user(telegram_id):
    try:
        user = User.objects.get(telegram_id=telegram_id)
        return True
    except User.DoesNotExist:
        return False


def add_new_user(full_name, phone_number, telegram_id):
    if not check_user():
        return 'This user already exist'
    else:
        new_user = User(
            full_name=full_name,
            phone_number=phone_number,
            telegram_id=telegram_id,
            created_at=datetime.now()
            )
        new_user.save()
        return 'Added new user'



# from telegram_bot.models import User
# from telegram_bot.views import
