# highload-bot

Техническое задания читать [здесь](https://gist.github.com/pelid/4d613e23f4b0f45d347a86a281d2968a)

## Что нужно знать: 
Описания `QuerySet.Manager()`, типы данных и формат и как с ними работать. 
https://gist.github.com/djeck1432/bb72050ff7a51d746bfb81ee8f391db0


## Переменные окружения

`TELEGRAM_ACCESS_TOKEN` - токен бота;

`DEBUG` - режим отладки, по дефолту `False`

`SECRET_KEY` - секретный ключ `Django`

## Как установить

1) Скачать репозиторий:
```bash
git clone https://github.com/LevelUp-developers/highload-bot.git
```
2) Перейти в репозиторий:
```bash
cd highload-bot
```
3) Установить библиотеки и зависимости:
```bash
pip3 install -r requiremets.txt
```
4) Выполнить миграцию:
```bash
python3 manage.py migrate
```
5) Запустить сервер:
```bash
python3 manage.py runserver
```

## Как попасть в админку
Создайте `superuser`
```bash
python3 manage.py createsuperuser
```
Запустите сервер:
```bash
python3 manage.py runserver
```
Перейдите по ссылке в [127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)

## Как запустить `Bot`

Выполните команду:

```bash
python3 manage.py start_bot``
```



