# 2026-VK-EDU-Web-11-Baryagina-K
Домашнее задание по курсу "Веб-технологии"


## Требования

- Python 3.12 или новее (локальный запуск проверен на Django 6.1.2).
- Docker с командой `docker compose`. PostgreSQL 17 запускается в Docker, Django — локально.

Выполняйте команды из корня проекта, рядом с `manage.py`.

## Настройка окружения

**Windows PowerShell**

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
Copy-Item .env.example .env.local
Copy-Item .env.example .env.docker
```

**macOS / Linux**

```bash
python3.12 -m venv venv
source venv/bin/activate
cp .env.example .env.local
cp .env.example .env.docker
```

Если используете другой подходящий Python, укажите его исполняемый файл при создании `venv`.

| Переменная | `.env.local` | `.env.docker` |
| --- | --- | --- |
| `SECRET_KEY` | Свой случайный ключ | Тот же ключ |
| `DEBUG` | `True` | `True` |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `localhost,127.0.0.1` |
| `DB_NAME`, `DB_USER` | `best_faq` для обеих переменных | Те же значения |
| `DB_PASSWORD` | Свой пароль базы | Тот же пароль |
| `DB_HOST` | `127.0.0.1` | `db` |
| `DB_PORT` | `5433` | `5432` |

`5433` — порт компьютера в проверенной конфигурации. Если в `docker-compose.yml` проброшен другой порт, укажите его в `.env.local`. Не добавляйте `.env.local` и `.env.docker` в Git. Если база уже создана, используйте её действующие имя, пользователя и пароль.

## Запуск

В активном виртуальном окружении установите зависимости и запустите PostgreSQL:

```bash
python -m pip install -r requirements.txt
docker compose --env-file .env.docker up -d db
docker compose --env-file .env.docker ps
```

Когда `db` получит статус `healthy`, выполните:

```bash
python manage.py migrate
python manage.py runserver
```

Сайт откроется по адресу <http://127.0.0.1:8000/>.

## Тестовые данные

После миграций в новой базе ещё нет вопросов и ответов. Чтобы добавить демоданные, выполните в активном `venv` после миграций — до запуска сервера или в отдельном терминале:

```bash
python manage.py fill_db 10
```

Команда добавит 100 вопросов и 1 000 ответов. Повторный запуск добавляет новую порцию, а не заменяет существующие записи.

## Адреса

| Путь | Страница |
| --- | --- |
| `/` | Новые вопросы — **New Questions** |
| `/hot/` | Вопросы по рейтингу — **Hot Questions** |
| `/tag/<slug>/` | Вопросы по тегу; откройте ссылку в секции **Tags** или на карточке вопроса |
| `/question/<id>/` | Вопрос и ответы на него |
| `/login/` | Вход в существующую учётную запись |
| `/admin/` | Админка Django. Для создания локального суперпользователя: `python manage.py createsuperuser` |
