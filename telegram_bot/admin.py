from django.contrib import admin
from .models import (
    User, Draw,
    Rebus, RebusAttempt, Answer,
    PollResult, PollQuestionAnswerPair
    )


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


class PollQuestionAnswerPairInline(admin.TabularInline):
    model = PollQuestionAnswerPair
    extra = 1


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    pass


@admin.register(Rebus)
class RebusAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]


@admin.register(RebusAttempt)
class RebusAttemptAdmin(admin.ModelAdmin):
    pass


@admin.register(PollResult)
class PollResultAdmin(admin.ModelAdmin):
    inlines = [PollQuestionAnswerPairInline]
