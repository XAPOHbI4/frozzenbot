# Система уведомлений FrozenBot (BE-014)

## Обзор

Система уведомлений FrozenBot обеспечивает полный цикл автоматических уведомлений для пользователей и администраторов. Система включает в себя отслеживание статусов заказов, обратную связь от клиентов, отложенные уведомления и comprehensive API для управления.

## Архитектура

### Основные компоненты

1. **NotificationService** - основной сервис для отправки уведомлений
2. **NotificationScheduler** - планировщик отложенных задач
3. **Модели данных** - для хранения истории уведомлений и обратной связи
4. **API endpoints** - для управления уведомлениями через REST API
5. **Bot handlers** - обработчики обратной связи в Telegram боте

### Схема базы данных

#### Notifications
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL,  -- 'user' или 'admin'
    target_telegram_id BIGINT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    title VARCHAR(255),
    message TEXT NOT NULL,
    order_id INTEGER REFERENCES orders(id),
    user_id INTEGER REFERENCES users(id),
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    metadata JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    inline_keyboard JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### FeedbackRating
```sql
CREATE TABLE feedback_ratings (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    notification_id INTEGER REFERENCES notifications(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

#### NotificationTemplate
```sql
CREATE TABLE notification_templates (
    id SERIAL PRIMARY KEY,
    notification_type VARCHAR(50) UNIQUE NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    title_template VARCHAR(255),
    message_template TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    delay_minutes INTEGER DEFAULT 0,
    description TEXT,
    variables JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);
```

## Типы уведомлений

### Пользовательские уведомления

1. **ORDER_CREATED** - заказ создан
2. **ORDER_CONFIRMED** - заказ подтвержден (после оплаты)
3. **ORDER_PREPARING** - заказ готовится
4. **ORDER_READY** - заказ готов к выдаче
5. **ORDER_COMPLETED** - заказ выполнен
6. **ORDER_CANCELLED** - заказ отменен
7. **PAYMENT_SUCCESS** - успешная оплата
8. **PAYMENT_FAILED** - ошибка оплаты
9. **FEEDBACK_REQUEST** - запрос обратной связи

### Административные уведомления

1. **ADMIN_NEW_ORDER** - новый заказ
2. **ADMIN_PAYMENT_FAILED** - ошибка оплаты
3. **ADMIN_DAILY_STATS** - ежедневная статистика

## Использование

### NotificationService

```python
from app.services.notification import NotificationService
from app.models.notification import NotificationType, NotificationTarget

# Создание сервиса
notification_service = NotificationService(db)

# Отправка уведомления
await notification_service.send_notification(
    telegram_id=123456789,
    message="Ваш заказ готов!",
    notification_type=NotificationType.ORDER_READY,
    target_type=NotificationTarget.USER,
    order_id=1,
    user_id=1,
    title="Заказ готов"
)

# Уведомление о создании заказа
await notification_service.notify_order_created(order)

# Уведомление об изменении статуса
await notification_service.notify_order_status_change(order, old_status)

# Уведомление об успешной оплате
await notification_service.notify_payment_success(order, payment_data)

# Сохранение обратной связи
feedback = await notification_service.save_feedback_rating(
    order_id=1,
    user_id=1,
    rating=5,
    feedback_text="Отличный сервис!"
)
```

### NotificationScheduler

```python
from app.utils.scheduler import scheduler, schedule_feedback_request

# Запуск планировщика
await scheduler.start()

# Планирование задачи обратной связи
await schedule_feedback_request(
    order_id=1,
    user_id=1,
    telegram_id=123456789,
    delay_hours=1
)

# Планирование уведомления с задержкой
await scheduler.schedule_notification(
    telegram_id=123456789,
    message="Напоминание о заказе",
    notification_type="order_reminder",
    delay_minutes=60
)
```

## API Endpoints

### Уведомления

- `POST /api/notifications/` - создать уведомление
- `GET /api/notifications/` - получить список уведомлений
- `GET /api/notifications/{id}` - получить уведомление по ID
- `POST /api/notifications/{id}/retry` - повторить отправку
- `DELETE /api/notifications/{id}` - удалить уведомление

### Статистика

- `GET /api/notifications/stats/overview` - общая статистика
- `GET /api/notifications/stats/by-type` - статистика по типам

### Обратная связь

- `POST /api/notifications/feedback` - создать отзыв
- `GET /api/notifications/feedback` - получить отзывы
- `GET /api/notifications/feedback/stats` - статистика отзывов

### Шаблоны

- `POST /api/notifications/templates` - создать шаблон
- `GET /api/notifications/templates` - получить шаблоны

### Планировщик

- `GET /api/notifications/scheduler/tasks` - получить запланированные задачи
- `POST /api/notifications/scheduler/tasks/{id}/cancel` - отменить задачу

### Обработка

- `POST /api/notifications/process-scheduled` - обработать запланированные
- `POST /api/notifications/retry-failed` - повторить неудачные

## Обработчики бота

### Команды пользователя

- `/my_feedback` - показать историю отзывов

### Callback handlers

- `rate_order_{order_id}_{rating}` - оценка заказа
- `feedback_comment_{order_id}` - запрос комментария
- `feedback_done_{order_id}` - завершение обратной связи

### Администраторские команды

- `/feedback_stats` - статистика обратной связи

## Интеграция с существующими сервисами

### PaymentService

Система автоматически интегрируется с PaymentService для отправки уведомлений о статусе платежей:

```python
# В PaymentService при успешной оплате
await notification_service.notify_payment_success(order, payment_data)

# При ошибке оплаты
await notification_service.notify_payment_failed(order, error_message)
```

### OrderService

Интеграция с OrderService для уведомлений о статусах заказов:

```python
# При создании заказа
await notification_service.notify_order_created(order)

# При изменении статуса
await notification_service.notify_order_status_change(order, old_status)
```

## Конфигурация

### Настройки в config.py

```python
# ID администратора для уведомлений
ADMIN_ID = 123456789

# Настройки планировщика
SCHEDULER_CHECK_INTERVAL = 30  # секунды
FEEDBACK_DELAY_HOURS = 1
MAX_RETRY_ATTEMPTS = 3
```

### Переменные окружения

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_TELEGRAM_ID=123456789
```

## Мониторинг и логирование

### Логи

Система записывает подробные логи всех операций:

- Отправка уведомлений
- Ошибки Telegram API
- Обработка обратной связи
- Выполнение запланированных задач

### Метрики

Доступные метрики через API:

- Общее количество уведомлений
- Успешность доставки
- Статистика по типам уведомлений
- Средняя оценка обратной связи
- Распределение оценок

## Запуск и развертывание

### Запуск планировщика

Планировщик автоматически запускается при старте приложения в `main.py`:

```python
from app.utils.scheduler import start_scheduler, stop_scheduler

# При старте
await start_scheduler()

# При остановке
await stop_scheduler()
```

### Миграции базы данных

Добавьте новые модели в Alembic:

```bash
alembic revision --autogenerate -m "Add notification system"
alembic upgrade head
```

### Инициализация шаблонов

Создайте базовые шаблоны уведомлений:

```python
from app.models.notification import NotificationTemplate, NotificationType, NotificationTarget

# Шаблон для подтверждения заказа
template = NotificationTemplate(
    notification_type=NotificationType.ORDER_CONFIRMED,
    target_type=NotificationTarget.USER,
    title_template="Заказ подтвержден",
    message_template="✅ Ваш заказ #{order_id} подтвержден!\\n\\nМы начинаем его готовить.",
    enabled=True
)
```

## Тестирование

### Unit тесты

```bash
pytest tests/test_notifications.py
pytest tests/test_feedback_handlers.py
pytest tests/test_notification_api.py
```

### Интеграционные тесты

```bash
pytest tests/ -k "integration"
```

### Покрытие тестами

```bash
pytest --cov=app.services.notification --cov=app.utils.scheduler --cov=app.api.notifications
```

## Безопасность

### Валидация данных

- Все API endpoints используют Pydantic для валидации
- Проверка прав доступа для административных функций
- Санитизация пользовательского ввода

### Ограничения

- Максимум 3 попытки повтора для неудачных уведомлений
- Ограничение длины комментариев (1000 символов)
- Rate limiting для API endpoints

## Мониторинг производительности

### Ключевые метрики

- Время отклика API endpoints
- Скорость обработки запланированных задач
- Процент успешной доставки уведомлений
- Среднее время отправки уведомлений

### Алерты

Настройте алерты для:

- Высокого процента неудачных уведомлений
- Задержки в обработке запланированных задач
- Ошибок Telegram API

## Troubleshooting

### Частые проблемы

1. **Уведомления не отправляются**
   - Проверьте токен бота
   - Убедитесь, что пользователь не заблокировал бота
   - Проверьте логи на ошибки API

2. **Запланированные задачи не выполняются**
   - Убедитесь, что планировщик запущен
   - Проверьте системное время
   - Проверьте подключение к базе данных

3. **Обратная связь не сохраняется**
   - Проверьте callback handlers
   - Убедитесь в корректности данных заказа
   - Проверьте права доступа к базе данных

### Диагностика

```python
# Проверка состояния планировщика
from app.utils.scheduler import scheduler
print(f"Scheduler running: {scheduler.running}")
print(f"Scheduled tasks: {len(scheduler.tasks)}")

# Статистика уведомлений
stats = await notification_service.get_notification_stats(days=1)
print(f"Success rate: {stats['success_rate']}%")
```

## Roadmap

### Планируемые улучшения

1. **Шаблоны уведомлений**
   - Веб-интерфейс для управления шаблонами
   - Поддержка переменных в шаблонах
   - A/B тестирование сообщений

2. **Расширенная аналитика**
   - Дашборд с метриками в реальном времени
   - Экспорт отчетов
   - Интеграция с системами мониторинга

3. **Дополнительные каналы**
   - Email уведомления
   - SMS уведомления
   - Push уведомления в веб-приложении

4. **Персонализация**
   - Настройки уведомлений пользователя
   - Timezone support
   - Локализация сообщений

## Заключение

Система уведомлений FrozenBot обеспечивает полный цикл коммуникации с клиентами, от создания заказа до получения обратной связи. Система спроектирована с учетом масштабируемости, надежности и простоты использования.

Для получения дополнительной информации обращайтесь к документации API или исходному коду в соответствующих модулях.