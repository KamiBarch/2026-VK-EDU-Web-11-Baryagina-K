# 2026-VK-EDU-Web-11-Baryagina-K
Домашнее задание по курсу "Веб-технологии"


## Инструкция по запуску

Проект можно запустить локально или через Docker Compose.

### Требования

- Python 3.12 или новее для локального запуска
- Docker Desktop и Docker Compose для запуска через Docker


### Вариант 1. Локальный запуск

Создайте и активируйте виртуальное окружение.

**macOS/Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows PowerShell**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Установите зависимости и выполните миграции:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
```

Запустите локальный сервер:

```bash
python manage.py runserver
```

Откройте в браузере <http://127.0.0.1:8000/>.

### Вариант 2. Запуск через Docker Compose

Убедитесь, что Docker Desktop запущен. Откройте терминал в папке проекта и выполните:

```bash
docker compose up --build
```

Проект будет доступен по адресу <http://localhost:8000/>.

Чтобы остановить контейнеры, нажмите `Ctrl+C`.

### Список страниц

- `/` — главная страница, список новых вопросов и пагинация
- `/hot/` — список горячих вопросов
- `/tag/<название_тега>/` — вопросы по тегу
- `/question/<id>/` — страница вопроса и ответы
- `/ask/` — форма создания вопроса
- `/login/` — форма входа
- `/signup/` — форма регистрации
- `/profile/` — страница профиля
- `/question_card/` - карточка вопроса
- `/answer_card/` - карточка ответа

