# FrozenFoodBot Backend

Backend приложение для телеграм-бота продажи замороженных продуктов.

## Технологии

- **Python 3.11+**
- **FastAPI** - веб-фреймворк
- **aiogram 3.x** - Telegram Bot API
- **PostgreSQL** - база данных
- **SQLAlchemy 2.0** - ORM (async)
- **Alembic** - миграции
- **Redis** - кэширование
- **Docker** - контейнеризация

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка окружения

Скопируйте `.env` файл и настройте переменные:

```bash
cp .env.example .env
```

### 3. Запуск с Docker

```bash
docker-compose up -d
```

### 4. Применение миграций

```bash
alembic upgrade head
```

### 5. Создание тестовых данных

```bash
python -m app.utils.seed_data
```

### 6. Запуск приложения

```bash
python -m app.main
```

## API Endpoints

- `GET /` - главная страница
- `GET /health` - проверка здоровья
- `GET /api/products/` - список товаров
- `GET /api/categories/` - список категорий
- `GET /api/users/me` - текущий пользователь

## Bot Commands

### Пользователи:
- `/start` - начало работы
- `/help` - справка
- `/catalog` - каталог товаров

### Админ (ID: 1050239011):
- `/admin` - панель администратора
- `/stats` - быстрая статистика

## Структура проекта

```
backend/
├── app/
│   ├── api/          # FastAPI endpoints
│   ├── bot/          # Telegram bot
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── utils/        # Helpers
├── migrations/       # Alembic migrations
└── docker/          # Docker configs
```

## Разработка

### Создание миграции

```bash
alembic revision --autogenerate -m "Description"
```

### Применение миграций

```bash
alembic upgrade head
```

### Откат миграций

```bash
alembic downgrade -1
```

## Конфигурация

Основные настройки в `.env`:

- `BOT_TOKEN` - токен Telegram бота
- `ADMIN_ID` - ID администратора
- `DATABASE_URL` - URL базы данных
- `MIN_ORDER_AMOUNT` - минимальная сумма заказа
- `PAYMENT_CARD_INFO` - реквизиты для оплаты