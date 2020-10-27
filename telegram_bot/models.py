from django.utils import timezone
from django.db import models


class RebusManager(models.Manager):

    def get_fresh_rebuses(self, telegram_id):
        fresh_rebuses = self.exclude(rebus_attempts__user__telegram_id=telegram_id).values('text', 'image')
        return fresh_rebuses

    def get_old_rebuses(self, telegram_id):
        old_rebuses = self.filter(rebus_attempts__user__telegram_id=telegram_id)\
            .values('id', 'text', 'image').distinct()
        return old_rebuses


class RebusAttemptManager(models.Manager):

    def get_amount_user_attempts(self, rebus_id, telegram_id, time=None):
        time = time if time else timezone.now()
        attempts = self.filter(user__telegram_id=telegram_id, rebus__id=rebus_id)
        draw = Draw.objects.filter(start_at__lte=time, end_at__gte=time)
        try:
            range_time = [draw.start_at, draw.end_at]
            amount_attempts = attempts.filter(rebus_sendet_at__range=range_time).count()
            return amount_attempts
        except AttributeError:
            return 0


class User(models.Model):
    full_name = models.CharField(
                'Полное имя',
                max_length=200,
                blank=True,
                null=True
            )
    phone_number = models.CharField(
                'Номер телефона',
                max_length=20,
                blank=True,
                null=True
            )
    exclude_from_export = models.BooleanField(
            'Исключить из экспорт',
            default=False,
            db_index=True
            )
    created_at = models.DateTimeField(
            verbose_name='Зарегестрирован в',
            db_index=True,
            blank=True,
            null=True,
            )
    telegram_id = models.IntegerField(
                'Telegram Id',
                blank=True,
                null=True
            )

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def __str__(self):
        return f'{self.full_name}'


class Draw(models.Model):
    title = models.CharField('Названия розыгрыша', max_length=200)
    start_at = models.DateTimeField(
            verbose_name='Страт розыгрыша',
            default=timezone.now,
            db_index=True,
            auto_now=False,
            auto_now_add=False,
            )
    end_at = models.DateTimeField(
            verbose_name='Окончания розыгрыша',
            db_index=True,
            auto_now=False,
            auto_now_add=False,
            )

    class Meta:
        verbose_name = 'Розыгрышь'
        verbose_name_plural = 'Розыгрыши'

    def __str__(self):
        return self.title


class Rebus(models.Model):
    text = models.TextField('Текст', blank=True, null=True)
    image = models.ImageField('Изображения')
    published = models.BooleanField('Опубликовать', default=False)
    hint = models.TextField('Подсказка', blank=True, null=True)
    objects = RebusManager()

    class Meta:
        verbose_name = 'Ребус'
        verbose_name_plural = 'Ребусы'

    def __str__(self):
        return f'Ребус {self.id}'


class Answer(models.Model):
    rebus = models.ForeignKey(
            Rebus,
            on_delete=models.SET_NULL,
            verbose_name='Ребус',
            related_name='answers',
            null=True,
            )
    answer = models.CharField('Ответ', max_length=100)

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'


class RebusAttempt(models.Model):
    rebus = models.ForeignKey(
            Rebus,
            on_delete=models.SET_NULL,
            verbose_name='Ребус',
            related_name='rebus_attempts',
            null=True,
            )
    user = models.ForeignKey(
            User,
            on_delete=models.SET_NULL,
            verbose_name='Участник',
            related_name='user_attempts',
            null=True,
            )
    answer_recieved_at = models.DateTimeField(
            verbose_name='Ответ получен в',
            db_index=True,
            blank=True,
            null=True,
            )
    success = models.BooleanField('Успешно', default=False)
    answer = models.CharField('Ответ Юзера', max_length=100)
    rebus_sendet_at = models.DateTimeField(
            verbose_name='Ребус отправлен в',
            db_index=True,
            blank=True,
            null=True,
            )
    objects = RebusAttemptManager()

    class Meta:
        verbose_name = 'Попытка решить ребус'
        verbose_name_plural = 'Попытки решить ребус'

    def __str__(self):
        return self.user.full_name


class PollResult(models.Model):
    user = models.ForeignKey(
            User,
            verbose_name='Участник',
            on_delete=models.SET_NULL,
            null=True
            )
    current_question = models.SlugField('Текущий вопрос')
    poll_finished = models.BooleanField('Закончил опрос', default=False)
    started_at = models.DateTimeField(
            verbose_name='Начал опрос в',
            db_index=True,
            blank=True,
            null=True,
            )
    ended_at = models.DateTimeField(
            verbose_name='Закончил опрос в',
            db_index=True,
            blank=True,
            null=True,
            )

    class Meta:
        verbose_name = 'Опрос'
        verbose_name_plural = 'Опросы'

    def __str__(self):
        return f'Опрос_{self.id}'


class PollQuestionAnswerPair(models.Model):
    quiz = models.ForeignKey(
            PollResult,
            verbose_name='Опрос',
            on_delete=models.SET_NULL,
            null=True
            )
    question = models.TextField('Вопрос')
    answer = models.CharField('Ответ', max_length=200)
    asked_at = models.DateTimeField(
            verbose_name='Получил вопрос в',
            db_index=True,
            blank=True,
            null=True,
            )
    answered_at = models.DateTimeField(
            verbose_name='Ответил в',
            db_index=True,
            blank=True,
            null=True,
            )

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return f'Вопрос_{self.id}'
