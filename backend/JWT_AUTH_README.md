# JWT Authentication System для FrozenBot

Полная JWT Authentication система с Role-Based Access Control (RBAC), реализованная для FrozenBot проекта.

## Обзор системы

### Основные компоненты

- **JWT Token Management** - Генерация, валидация, blacklisting токенов
- **Role-Based Access Control** - Система ролей: User, Manager, Admin
- **Password Security** - Хеширование паролей, валидация сложности
- **Rate Limiting** - Защита от атак перебора
- **Telegram Integration** - Аутентификация через Telegram WebApp
- **Session Management** - Управление сессиями пользователей
- **Security Middleware** - Защита API endpoints

### Роли пользователей

1. **USER** - Базовый пользователь
   - Создание заказов
   - Просмотр своих заказов
   - Просмотр каталога продуктов

2. **MANAGER** - Менеджер
   - Все права USER
   - Управление продуктами (создание, редактирование, удаление)
   - Управление категориями
   - Просмотр всех заказов
   - Изменение статусов заказов

3. **ADMIN** - Администратор
   - Все права MANAGER
   - Создание новых пользователей
   - Доступ к админ панели
   - Доступ к аналитике
   - Управление системными настройками

## Архитектура

### Файловая структура

```
backend/app/
├── models/user.py          # Расширенная модель User с ролями
├── utils/
│   ├── jwt.py             # JWT утилиты
│   ├── security.py        # Security утилиты
│   └── telegram.py        # Telegram WebApp утилиты
├── services/auth.py       # Authentication service
├── middleware/auth.py     # Auth middleware и dependencies
├── api/auth.py           # Authentication endpoints
└── schemas/auth.py       # Authentication schemas
```

### JWT Токены

#### Access Token
- **Время жизни**: 30 минут (по умолчанию)
- **Назначение**: Авторизация API запросов
- **Содержит**: user_id, role, telegram_id, username

#### Refresh Token
- **Время жизни**: 30 дней (по умолчанию)
- **Назначение**: Обновление access токенов
- **Безопасность**: Может быть отозван, blacklisted

#### Blacklisting
- Redis-based token blacklisting
- Автоматическая очистка истекших записей
- User-based blacklisting (отзыв всех токенов пользователя)

## API Endpoints

### Authentication Endpoints

#### POST /api/auth/login
Вход в систему с username/password

**Request:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    ...
  }
}
```

#### POST /api/auth/telegram
Аутентификация через Telegram WebApp

**Request:**
```json
{
  "init_data": "query_id=AAH...&user=%7B%22id%22%3A123456789..."
}
```

#### POST /api/auth/refresh
Обновление access токена

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### POST /api/auth/logout
Выход из системы

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### GET /api/auth/me
Информация о текущем пользователе

**Headers:**
```
Authorization: Bearer <access_token>
```

#### PUT /api/auth/change-password
Смена пароля

**Request:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "NewSecurePassword123!"
}
```

#### POST /api/auth/register
Регистрация нового пользователя (только для админов)

**Request:**
```json
{
  "username": "manager1",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "role": "manager"
}
```

## Защищенные Endpoints

### Products API
- **POST/PUT/DELETE** `/api/products/*` - Manager/Admin только
- **GET** endpoints остаются публичными

### Orders API
- **GET** `/api/orders/{id}` - Пользователь может видеть только свои заказы
- **PUT** `/api/orders/{id}/status` - Manager/Admin только
- **GET** `/api/orders/stats/*` - Manager/Admin только

### Admin API
- **Все endpoints** `/api/admin/*` - Admin только

### Categories API
- **POST/PUT/DELETE** - Manager/Admin только
- **GET** - публичные

## Middleware и Dependencies

### Основные Dependencies

```python
from app.middleware.auth import (
    get_current_user,              # Опциональная аутентификация
    require_authenticated_user,     # Обязательная аутентификация
    require_admin_user,            # Только админ
    require_manager_or_admin,      # Менеджер или админ
    require_roles([UserRole.ADMIN]), # Проверка конкретных ролей
    require_permissions(["admin:access"]) # Проверка разрешений
)
```

### Rate Limiting

```python
from app.middleware.auth import auth_rate_limit, api_rate_limit

@router.post("/login", dependencies=[Depends(auth_rate_limit)])
async def login(...):
    pass
```

### Пример использования

```python
@router.post("/products/")
async def create_product(
    product_data: ProductCreateRequest,
    current_user: User = Depends(require_manager_or_admin),
    db: AsyncSession = Depends(get_async_session)
):
    # Только Manager или Admin могут создавать продукты
    pass

@router.get("/admin/analytics")
async def get_analytics(
    admin_user: User = Depends(require_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    # Только Admin может получить аналитику
    pass
```

## Security Features

### Password Security
- **Минимальные требования**: 8 символов, заглавные, строчные, цифры, спецсимволы
- **Хеширование**: bcrypt с автогенерируемым salt
- **Валидация**: Проверка распространенных паттернов, повторяющихся символов

### Rate Limiting
- **Authentication**: 10 попыток за 15 минут
- **API requests**: 100 запросов в минуту
- **Account lockout**: 5 неудачных попыток → блокировка на 30 минут

### Security Headers
Автоматически добавляются через middleware:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security`
- `Content-Security-Policy`

### Audit Logging
- Все события аутентификации логируются
- Неудачные попытки входа
- Изменения паролей
- Административные действия

## Конфигурация

### Environment Variables

```env
# JWT Settings
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis for token blacklisting
REDIS_URL=redis://localhost:6379

# Rate limiting
AUTH_RATE_LIMIT_ATTEMPTS=10
AUTH_RATE_LIMIT_WINDOW=15
API_RATE_LIMIT_ATTEMPTS=100
API_RATE_LIMIT_WINDOW=1

# Account security
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
PASSWORD_MIN_LENGTH=8
PASSWORD_MAX_LENGTH=128

# Telegram Bot
BOT_TOKEN=your-telegram-bot-token
```

## Миграции базы данных

Необходимо выполнить миграцию для добавления новых полей в модель User:

```sql
-- Добавить новые поля в таблицу users
ALTER TABLE users ADD COLUMN email VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';
ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN password_changed_at TIMESTAMP;

-- Индексы для производительности
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_username ON users(username);
```

## Тестирование

### Запуск тестов

```bash
# Все тесты аутентификации
pytest tests/unit/test_auth/

# Конкретные тесты
pytest tests/unit/test_auth/test_jwt.py
pytest tests/unit/test_auth/test_security.py
pytest tests/unit/test_auth/test_auth_service.py
pytest tests/unit/test_auth/test_middleware.py

# С покрытием кода
pytest tests/unit/test_auth/ --cov=app.utils.jwt --cov=app.services.auth --cov=app.middleware.auth
```

### Мокирование внешних зависимостей

Тесты используют моки для:
- Redis соединения
- Telegram API
- Email сервисов
- Database sessions

## Интеграция с Frontend

### TypeScript Types

Shared types доступны в `shared/types/auth.ts`:

```typescript
import { User, UserRole, LoginRequest, LoginResponse } from '@/shared/types/auth';

// Пример использования
const loginData: LoginRequest = {
  username: 'admin',
  password: 'password123'
};
```

### React Context

Система предоставляет типы для React auth context:

```typescript
import { AuthContextType, UseAuthReturn } from '@/shared/types/auth';

const useAuth = (): UseAuthReturn => {
  // Implementation
};
```

## Развертывание

### Production Checklist

1. **Environment Variables**
   - [ ] SECRET_KEY установлен в криптографически стойкое значение
   - [ ] REDIS_URL указывает на production Redis
   - [ ] CORS_ORIGINS ограничен реальными доменами
   - [ ] BOT_TOKEN установлен для production бота

2. **Database**
   - [ ] Выполнены миграции
   - [ ] Созданы индексы
   - [ ] Настроено резервное копирование

3. **Redis**
   - [ ] Настроен Redis для токен blacklisting
   - [ ] Настроено backup Redis данных
   - [ ] Настроены limits по памяти

4. **Security**
   - [ ] HTTPS включен
   - [ ] Security headers настроены
   - [ ] Rate limiting активен
   - [ ] Логирование аудита включено

5. **Monitoring**
   - [ ] Мониторинг неудачных попыток входа
   - [ ] Алерты на подозрительную активность
   - [ ] Performance мониторинг JWT операций

## Устранение неполадок

### Частые проблемы

#### "Invalid or expired token"
- Проверить время на сервере
- Убедиться что Redis доступен
- Проверить SECRET_KEY

#### "Rate limit exceeded"
- Проверить настройки rate limiting
- Очистить Redis ключи для тестирования
- Убедиться что IP корректно определяется

#### "Account is temporarily locked"
- Проверить failed_login_attempts в БД
- Сбросить блокировку: `UPDATE users SET failed_login_attempts=0, locked_until=NULL WHERE id=?`

#### Telegram authentication fails
- Проверить BOT_TOKEN
- Убедиться что webhook URL корректен
- Проверить валидацию initData

### Логирование

Важные логи для мониторинга:
```
# Успешная аутентификация
INFO: Successful authentication for user: 1

# Неудачная попытка входа
WARNING: Invalid password for user: 1

# Блокировка аккаунта
WARNING: Account locked for user: 1

# Подозрительная активность
WARNING: Rate limit exceeded for IP 192.168.1.1
```

## Поддержка

Для вопросов по JWT Authentication системе:
1. Проверить логи приложения
2. Проверить Redis соединение
3. Проверить database connectivity
4. Создать issue в репозитории с детальным описанием проблемы

---

**Версия документации**: 1.0
**Последнее обновление**: 2024-01-01