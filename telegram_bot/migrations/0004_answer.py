# Generated by Django 3.1.2 on 2020-10-23 16:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0003_rebus'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField(verbose_name='Текст вопроса')),
                ('rebus', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='telegram_bot.rebus', verbose_name='Ребус')),
            ],
            options={
                'verbose_name': 'Ответ',
                'verbose_name_plural': 'Ответы',
            },
        ),
    ]
