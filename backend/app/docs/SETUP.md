# Установка и настройка системы уведомлений

## Быстрый старт

### 1. Обновите базу данных

Добавьте новые модели в миграцию Alembic:

```bash
alembic revision --autogenerate -m "Add notification system models"
alembic upgrade head
```

### 2. Обновите импорты

Убедитесь, что в `app/models/__init__.py` импортированы новые модели:

```python
from .notification import Notification, NotificationTemplate, FeedbackRating
```

### 3. Конфигурация

Добавьте в `config.py` (если еще не добавлено):

```python
# Telegram
ADMIN_TELEGRAM_ID: int = Field(default=0)

@property
def admin_id(self) -> int:
    return self.ADMIN_TELEGRAM_ID
```

### 4. Переменные окружения

Добавьте в `.env`:

```bash
ADMIN_TELEGRAM_ID=123456789  # ID администратора в Telegram
```

### 5. Запуск

Система автоматически запустится при старте приложения. Планировщик уведомлений будет работать в фоне.

## Проверка работы

### 1. Тестирование API

```bash
# Получить статистику уведомлений
curl http://localhost:8000/api/notifications/stats/overview

# Получить список уведомлений
curl http://localhost:8000/api/notifications/

# Обработать запланированные уведомления
curl -X POST http://localhost:8000/api/notifications/process-scheduled
```

### 2. Тестирование в боте

- Создайте заказ через бота
- Проверьте получение уведомлений
- После выполнения заказа проверьте запрос обратной связи

### 3. Запуск тестов

```bash
pytest tests/test_notifications.py -v
pytest tests/test_feedback_handlers.py -v
pytest tests/test_notification_api.py -v
```

## Возможные проблемы

### База данных

Если таблицы не создались автоматически, создайте их вручную:

```sql
-- Выполните SQL из NOTIFICATIONS_SYSTEM.md
```

### Импорты

Если возникают ошибки импорта, проверьте:

1. Все новые файлы добавлены в правильные папки
2. `__init__.py` файлы обновлены
3. Пути импортов корректны

### Scheduler

Если планировщик не работает:

1. Проверьте, что он запускается в `main.py`
2. Убедитесь, что нет ошибок в логах
3. Проверьте подключение к базе данных

## Интеграция с существующим кодом

Система спроектирована для работы с существующими сервисами. Основные точки интеграции:

1. **PaymentService** - автоматически использует новые методы уведомлений
2. **OrderService** - расширен методами для уведомлений
3. **Bot handlers** - добавлены обработчики обратной связи

Все legacy методы сохранены для обратной совместимости.