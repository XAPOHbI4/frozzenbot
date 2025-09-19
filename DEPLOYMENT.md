# 🚀 Деплой FrozenFoodBot на сервер

## 📋 Быстрый старт

### Вариант 1: Автоматический деплой через GitHub Actions

1. **Создать репозиторий на GitHub**
2. **Добавить секреты в GitHub**:
   - `HOST` - IP адрес сервера
   - `USERNAME` - root или ubuntu
   - `SSH_KEY` - приватный SSH ключ
   - `BOT_TOKEN` - токен от @BotFather
   - `ADMIN_ID` - ваш Telegram ID

3. **Push в main ветку** → автоматический деплой!

### Вариант 2: Docker Compose (Рекомендуется)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/yourusername/frozenbot-project.git
cd frozenbot-project

# 2. Настроить environment
cp .env.production .env
nano .env  # отредактировать токены и пароли

# 3. Запустить
docker-compose -f docker-compose.prod.yml up -d
```

### Вариант 3: Ручная установка (для опытных)

Следуйте инструкциям в `deployment/SETUP-CHECKLIST.md`

---

## 🔧 Настройка

### 1. Environment переменные (.env)

```env
# Основные настройки
DOMAIN=yourdomain.com
BOT_TOKEN=1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ADMIN_ID=123456789
PAYMENT_PROVIDER_TOKEN=381764678:TEST:xxxxx

# База данных
POSTGRES_PASSWORD=secure_password_here
SECRET_KEY=your_secret_key_here

# Email для SSL
ACME_EMAIL=admin@yourdomain.com
```

### 2. DNS настройки

Добавьте A записи в DNS:
- `yourdomain.com` → IP сервера
- `www.yourdomain.com` → IP сервера

### 3. GitHub Secrets (для автодеплоя)

В настройках репозитория → Secrets and Variables → Actions:

```
HOST = 142.93.x.x
USERNAME = root
SSH_KEY = -----BEGIN OPENSSH PRIVATE KEY-----
          xxxxxxxxxxxxxxxxxxxxxxxxxxx
          -----END OPENSSH PRIVATE KEY-----
BOT_TOKEN = 1234567890:AAxxxxxxxxxxxx
ADMIN_ID = 123456789
```

---

## 🌐 Архитектура продакшена

```
┌─────────────────┐    ┌─────────────────┐
│   Traefik       │    │   Frontend      │
│   (SSL, Proxy)  │◄───┤   (Admin+WebApp)│
│   Port 80/443   │    │                 │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Backend API   │    │   Telegram Bot  │
│   (FastAPI)     │◄───┤   (aiogram)     │
│   Port 8000     │    │                 │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │
│   (Database)    │    │   (Cache/Queue) │
└─────────────────┘    └─────────────────┘
```

---

## 📊 Мониторинг

### Проверка сервисов

```bash
# Docker Compose
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f

# Или systemd (если используете скрипты)
systemctl status frozenbot-api
systemctl status frozenbot-bot
systemctl status nginx
```

### Логи

```bash
# API логи
docker-compose logs -f backend-api

# Bot логи
docker-compose logs -f telegram-bot

# Traefik логи
docker-compose logs -f traefik
```

### URL для проверки

- **API**: https://yourdomain.com/api/docs
- **Admin Panel**: https://yourdomain.com/admin
- **WebApp**: https://yourdomain.com/webapp
- **Traefik Dashboard**: https://traefik.yourdomain.com

---

## 🔒 Безопасность

### SSL сертификаты
- Автоматическое получение через Let's Encrypt
- Автообновление каждые 90 дней
- HTTPS редирект включен

### Firewall (ufw)
```bash
ufw allow 22     # SSH
ufw allow 80     # HTTP
ufw allow 443    # HTTPS
ufw enable
```

### Backup базы данных
```bash
# Создание бэкапа
docker-compose exec postgres pg_dump -U frozenbot frozenbot_db > backup.sql

# Восстановление
docker-compose exec -T postgres psql -U frozenbot frozenbot_db < backup.sql
```

---

## 🚨 Troubleshooting

### Частые проблемы:

**Bot не отвечает:**
```bash
docker-compose logs telegram-bot
# Проверьте BOT_TOKEN в .env
```

**SSL ошибка:**
```bash
# Проверьте DNS записи
nslookup yourdomain.com
# Проверьте порты
netstat -tulpn | grep :443
```

**База данных недоступна:**
```bash
docker-compose exec postgres psql -U frozenbot frozenbot_db
# Проверьте пароль в .env
```

### Обновление проекта:

```bash
# Остановить сервисы
docker-compose -f docker-compose.prod.yml down

# Обновить код
git pull origin main

# Пересобрать и запустить
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 📞 Поддержка

- **Документация API**: `/api/docs`
- **Логи**: `docker-compose logs -f [service_name]`
- **GitHub Issues**: для багов и вопросов

**Время установки**: 15-30 минут
**Сложность**: Средняя (с Docker Compose)