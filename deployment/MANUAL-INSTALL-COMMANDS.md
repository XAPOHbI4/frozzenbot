# 🚀 КОМАНДЫ ДЛЯ РУЧНОЙ УСТАНОВКИ FROZENBOT

## ШАГ 1: ПОДКЛЮЧЕНИЕ К СЕРВЕРУ
1. Зайдите в **GoDaddy панель управления**
2. Найдите ваш VPS
3. Кликните **"Console"** или **"Remote Access"**
4. Войдите как `adminvps` с паролем `C9!CuSfqC8NntoQ3`

---

## ШАГ 2: ПРОВЕРКА СИСТЕМЫ
```bash
# Проверяем систему
whoami
pwd
uname -a
sudo -l
```
**Результат:** Должны увидеть информацию о системе

---

## ШАГ 3: ОБНОВЛЕНИЕ СИСТЕМЫ (5 минут)
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем базовые пакеты
sudo apt install -y curl wget git nano htop unzip software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```
**Результат:** Система обновлена

---

## ШАГ 4: УСТАНОВКА PYTHON 3.11+ (3 минуты)
```bash
# Проверяем версию Python
python3 --version

# Если версия < 3.11, устанавливаем новую
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Проверяем установку
python3 --version
pip3 --version
```
**Результат:** Python 3.11+ установлен

---

## ШАГ 5: УСТАНОВКА NODE.JS 18+ (3 минуты)
```bash
# Устанавливаем Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Проверяем установку
node --version
npm --version
```
**Результат:** Node.js 18+ установлен

---

## ШАГ 6: УСТАНОВКА NGINX (2 минуты)
```bash
# Устанавливаем Nginx
sudo apt install -y nginx

# Запускаем и включаем автозагрузку
sudo systemctl start nginx
sudo systemctl enable nginx

# Проверяем статус
sudo systemctl status nginx
```
**Результат:** Nginx работает

---

## ШАГ 7: УСТАНОВКА MYSQL (5 минут)
```bash
# Устанавливаем MySQL
sudo apt install -y mysql-server

# Запускаем MySQL
sudo systemctl start mysql
sudo systemctl enable mysql

# Создаем базу данных и пользователя
sudo mysql -e "CREATE DATABASE IF NOT EXISTS frozenbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'frozenbot'@'localhost' IDENTIFIED BY 'FrozenBot2024!';"
sudo mysql -e "GRANT ALL PRIVILEGES ON frozenbot_db.* TO 'frozenbot'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Проверяем подключение
mysql -u frozenbot -pFrozenBot2024! -e "SHOW DATABASES;"
```
**Результат:** MySQL настроен с базой frozenbot_db

---

## ШАГ 8: УСТАНОВКА REDIS (2 минуты)
```bash
# Устанавливаем Redis
sudo apt install -y redis-server

# Запускаем Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Проверяем Redis
redis-cli ping
```
**Результат:** Redis отвечает PONG

---

## ШАГ 9: НАСТРОЙКА FIREWALL (2 минуты)
```bash
# Настраиваем UFW firewall
sudo ufw --force enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 8000

# Проверяем статус
sudo ufw status
```
**Результат:** Firewall настроен

---

## ШАГ 10: СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ И ДИРЕКТОРИЙ (1 минута)
```bash
# Создаем пользователя для приложения
sudo useradd -m -s /bin/bash frozenbot
sudo usermod -aG sudo frozenbot

# Создаем директории
sudo mkdir -p /var/www/frozenbot
sudo mkdir -p /var/log/frozenbot
sudo chown -R frozenbot:frozenbot /var/www/frozenbot
sudo chown -R frozenbot:frozenbot /var/log/frozenbot
```
**Результат:** Пользователь и директории созданы

---

## ШАГ 11: ЗАГРУЗКА ПРОЕКТА (3 минуты)
```bash
# Переходим в директорию проекта
cd /var/www/frozenbot

# Клонируем или создаем проект (временно создадим структуру)
sudo git clone https://github.com/your-username/frozenbot-project.git . || echo "Git clone failed, creating structure manually"

# Если git clone не сработал, создаем структуру вручную:
sudo mkdir -p backend/app/{api,bot,models,schemas,services,utils,core}
sudo mkdir -p frontend/{admin,webapp}
sudo mkdir -p deployment

# Меняем владельца
sudo chown -R frozenbot:frozenbot /var/www/frozenbot
```
**Результат:** Структура проекта создана

---

## ШАГ 12: СОЗДАНИЕ BACKEND ФАЙЛОВ (5 минут)

### Создаем requirements.txt:
```bash
cat > /var/www/frozenbot/backend/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
aiogram==3.2.0
sqlalchemy[asyncio]==2.0.23
alembic==1.12.1
asyncpg==0.29.0
aiomysql==0.2.0
pymysql==1.1.0
redis==5.0.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
aiofiles==23.2.1
httpx==0.25.2
Pillow==10.1.0
EOF
```

### Создаем .env файл:
```bash
cat > /var/www/frozenbot/backend/.env << 'EOF'
# Database
DATABASE_URL=mysql+aiomysql://frozenbot:FrozenBot2024!@localhost:3306/frozenbot_db
DATABASE_URL_SYNC=mysql+pymysql://frozenbot:FrozenBot2024!@localhost:3306/frozenbot_db

# Redis
REDIS_URL=redis://localhost:6379

# Telegram Bot
BOT_TOKEN=8324865395:AAHqDUmjR495VQ6CFLvZ8i83p3gppa_0qoM
ADMIN_ID=1050239011
WEBAPP_URL=https://domashniystandart.com

# API Settings - CRYPTOGRAPHICALLY SECURE KEYS
SECRET_KEY=wf3hx0-t07UkDEYduOmNJkQHkc9PfVCW_HRtb_jrnLg
JWT_SECRET=YbzUi9mOYGyXcY9Qfaw34j5QHJIYYfAczXfJ4A2F7WLQMBX_UCnvlL1e5hTi1WJNGBum4ADWhaINqkU86R9PWA
REFRESH_SECRET=3Z9Jki0La4efqkAKypCdpSgpy9jmffSvEe4C3SHElzoTLVwHdWA2bOBLm5n4WzpMyQU2OmfgpqEgjguD1gjgOQ
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment Configuration
ENVIRONMENT=production
DEBUG=false

# Telegram Payments
PAYMENT_PROVIDER_TOKEN=381764678:TEST:100
PAYMENT_WEBHOOK_URL=https://domashniystandart.com/api/payments/webhook

# CORS Settings
CORS_ORIGINS=https://domashniystandart.com,https://www.domashniystandart.com

# Business Settings
MIN_ORDER_AMOUNT=1500
PAYMENT_CARD_INFO="Карта: 1234 5678 9012 3456\nПолучатель: ООО 'Замороженная еда'"
EOF
```

---

## ШАГ 13: УСТАНОВКА PYTHON ЗАВИСИМОСТЕЙ (3 минуты)
```bash
# Переходим в backend директорию
cd /var/www/frozenbot/backend

# Создаем виртуальное окружение
sudo -u frozenbot python3 -m venv venv

# Активируем виртуальное окружение и устанавливаем зависимости
sudo -u frozenbot bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
```
**Результат:** Python зависимости установлены

---

## ШАГ 14: СОЗДАНИЕ ПРОСТОГО FASTAPI ПРИЛОЖЕНИЯ (3 минуты)
```bash
# Создаем основной файл приложения
cat > /var/www/frozenbot/backend/app/main.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

app = FastAPI(
    title="FrozenBot API",
    description="API for Frozen Food Telegram Bot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://domashniystandart.com",
        "https://www.domashniystandart.com",
        "http://localhost:3000",
        "http://localhost:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With"
    ],
)

@app.get("/")
async def root():
    return {"message": "FrozenBot API is running!", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "frozenbot-api"}

@app.get("/api/")
async def api_root():
    return {"message": "FrozenBot API v1.0", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Меняем владельца файлов
sudo chown -R frozenbot:frozenbot /var/www/frozenbot
```

---

## ШАГ 15: ТЕСТИРОВАНИЕ API (2 минуты)
```bash
# Запускаем API для тестирования
cd /var/www/frozenbot/backend
sudo -u frozenbot bash -c "source venv/bin/activate && python app/main.py" &

# Ждем 5 секунд и тестируем
sleep 5
curl http://localhost:8000/
curl http://localhost:8000/health

# Останавливаем тестовый запуск
pkill -f "python app/main.py"
```
**Результат:** API отвечает JSON сообщениями

---

## ШАГ 16: СОЗДАНИЕ SYSTEMD СЕРВИСА (3 минуты)
```bash
# Создаем systemd сервис для API
sudo tee /etc/systemd/system/frozenbot-api.service > /dev/null << 'EOF'
[Unit]
Description=FrozenBot FastAPI Application
After=network.target mysql.service redis-server.service

[Service]
Type=simple
User=frozenbot
WorkingDirectory=/var/www/frozenbot/backend
Environment=PATH=/var/www/frozenbot/backend/venv/bin
ExecStart=/var/www/frozenbot/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd и запускаем сервис
sudo systemctl daemon-reload
sudo systemctl enable frozenbot-api
sudo systemctl start frozenbot-api

# Проверяем статус
sudo systemctl status frozenbot-api
```
**Результат:** API запущен как сервис

---

## ШАГ 17: НАСТРОЙКА SSL С CERTBOT (5 минут)
```bash
# Устанавливаем snapd и certbot
sudo apt install -y snapd
sudo snap install core; sudo snap refresh core
sudo snap install --classic certbot

# Создаем symlink
sudo ln -sf /snap/bin/certbot /usr/bin/certbot

# Останавливаем nginx временно
sudo systemctl stop nginx

# Получаем SSL сертификат
sudo certbot certonly --standalone --agree-tos --no-eff-email --email admin@domashniystandart.com -d domashniystandart.com -d www.domashniystandart.com

# Запускаем nginx обратно
sudo systemctl start nginx
```
**Результат:** SSL сертификат получен

---

## ШАГ 18: НАСТРОЙКА NGINX (5 минут)
```bash
# Создаем конфигурацию nginx
sudo tee /etc/nginx/sites-available/frozenbot > /dev/null << 'EOF'
# HTTP redirect to HTTPS
server {
    listen 80;
    server_name domashniystandart.com www.domashniystandart.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Configuration
server {
    listen 443 ssl http2;
    server_name domashniystandart.com www.domashniystandart.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/domashniystandart.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domashniystandart.com/privkey.pem;

    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # API Proxy to FastAPI Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Root API endpoint
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # Logs
    access_log /var/log/nginx/frozenbot_access.log;
    error_log /var/log/nginx/frozenbot_error.log;
}
EOF

# Активируем конфигурацию
sudo ln -sf /etc/nginx/sites-available/frozenbot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию и перезапускаем nginx
sudo nginx -t
sudo systemctl restart nginx
```
**Результат:** Nginx настроен с SSL

---

## ШАГ 19: НАСТРОЙКА АВТООБНОВЛЕНИЯ SSL (1 минута)
```bash
# Добавляем автообновление SSL в crontab
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```
**Результат:** SSL будет автоматически обновляться

---

## ШАГ 20: ФИНАЛЬНАЯ ПРОВЕРКА (2 минуты)
```bash
# Проверяем все сервисы
sudo systemctl status frozenbot-api --no-pager
sudo systemctl status nginx --no-pager
sudo systemctl status mysql --no-pager
sudo systemctl status redis-server --no-pager

# Проверяем SSL сертификат
sudo certbot certificates

# Тестируем API через HTTPS
curl -k https://domashniystandart.com/
curl -k https://domashniystandart.com/health
```

---

## 🎉 ГОТОВО! ПРОВЕРЬТЕ В БРАУЗЕРЕ:
- **API:** https://domashniystandart.com/
- **API Docs:** https://domashniystandart.com/docs
- **Health Check:** https://domashniystandart.com/health

## 📋 ПОЛЕЗНЫЕ КОМАНДЫ:
```bash
# Просмотр логов API
sudo journalctl -u frozenbot-api -f

# Перезапуск API
sudo systemctl restart frozenbot-api

# Просмотр логов Nginx
sudo tail -f /var/log/nginx/frozenbot_error.log

# Перезапуск Nginx
sudo systemctl restart nginx
```

**Время установки: 40-50 минут**
**После завершения у вас будет работающий HTTPS API на домене!**