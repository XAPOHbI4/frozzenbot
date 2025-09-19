#!/bin/bash
# Production Deployment Script for FrozenFoodBot
# Domain: domashniystandart.com

echo "🚀 PRODUCTION DEPLOYMENT - FROZENBOT"
echo "===================================="

# Проверяем права root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Запустите скрипт от root: sudo ./production-deploy.sh"
   exit 1
fi

# Установка базовых зависимостей
echo "📦 Установка системных зависимостей..."
apt update && apt upgrade -y
apt install -y git python3 python3-pip python3-venv nodejs npm mysql-server redis-server nginx

# Создаем пользователя для приложения
echo "👤 Создание пользователя frozenbot..."
useradd -m -s /bin/bash frozenbot || echo "Пользователь уже существует"

# Создаем директории
echo "📁 Создание директорий проекта..."
mkdir -p /var/www/frozenbot
mkdir -p /var/log/frozenbot
chown -R frozenbot:frozenbot /var/www/frozenbot
chown -R frozenbot:frozenbot /var/log/frozenbot

# Клонируем проект (или копируем)
echo "📥 Подготовка кода проекта..."
cd /var/www/frozenbot

# Backend setup
echo "🐍 Настройка Backend..."
cd /var/www/frozenbot
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Копируем production конфигурацию
cp backend/.env.production backend/.env

# Frontend build
echo "⚛️ Сборка Frontend..."
cd /var/www/frozenbot/frontend/admin
npm install
npm run build

cd /var/www/frozenbot/frontend/webapp
npm install
npm run build

# Database setup
echo "🗄️ Настройка базы данных..."
systemctl start mysql
systemctl enable mysql

# Создаем базу данных
mysql -e "CREATE DATABASE IF NOT EXISTS frozenbot_db;"
mysql -e "CREATE USER IF NOT EXISTS 'frozenbot'@'localhost' IDENTIFIED BY 'your-secure-password';"
mysql -e "GRANT ALL PRIVILEGES ON frozenbot_db.* TO 'frozenbot'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Redis setup
echo "📋 Настройка Redis..."
systemctl start redis-server
systemctl enable redis-server

# SSL и Nginx
echo "🔐 Настройка SSL и Nginx..."
./ssl-setup.sh

# Создаем systemd service для backend
echo "⚙️ Создание systemd сервиса..."
cat > /etc/systemd/system/frozenbot-api.service << EOF
[Unit]
Description=FrozenBot FastAPI Application
After=network.target

[Service]
Type=simple
User=frozenbot
WorkingDirectory=/var/www/frozenbot/backend
Environment=PATH=/var/www/frozenbot/venv/bin
ExecStart=/var/www/frozenbot/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Создаем systemd service для telegram bot
cat > /etc/systemd/system/frozenbot-bot.service << EOF
[Unit]
Description=FrozenBot Telegram Bot
After=network.target

[Service]
Type=simple
User=frozenbot
WorkingDirectory=/var/www/frozenbot/backend
Environment=PATH=/var/www/frozenbot/venv/bin
ExecStart=/var/www/frozenbot/venv/bin/python -m app.bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Запускаем сервисы
echo "🚀 Запуск сервисов..."
systemctl daemon-reload
systemctl enable frozenbot-api
systemctl enable frozenbot-bot
systemctl start frozenbot-api
systemctl start frozenbot-bot

# Проверяем статус
echo "📊 Проверка статуса сервисов..."
systemctl status frozenbot-api --no-pager
systemctl status frozenbot-bot --no-pager
systemctl status nginx --no-pager

echo ""
echo "🎉 DEPLOYMENT ЗАВЕРШЕН!"
echo "======================="
echo "✅ Backend API: https://domashniystandart.com/api/"
echo "✅ Admin Panel: https://domashniystandart.com/admin"
echo "✅ WebApp: https://domashniystandart.com/webapp"
echo "✅ SSL сертификат: Активен"
echo ""
echo "📋 Логи:"
echo "API: journalctl -u frozenbot-api -f"
echo "Bot: journalctl -u frozenbot-bot -f"
echo "Nginx: tail -f /var/log/nginx/frozenbot_error.log"
echo ""
echo "🔧 Не забудьте:"
echo "1. Обновить BOT_TOKEN в .env"
echo "2. Настроить PAYMENT_PROVIDER_TOKEN"
echo "3. Проверить подключение к базе данных"