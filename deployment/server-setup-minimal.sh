#!/bin/bash
# Минимальная настройка сервера для FrozenFoodBot
# Выполнять на чистом Ubuntu сервере

echo "🚀 НАСТРОЙКА СЕРВЕРА ДЛЯ FROZENBOT"
echo "=================================="

# Проверка root прав
if [[ $EUID -ne 0 ]]; then
   echo "❌ Запустите от root: sudo bash server-setup-minimal.sh"
   exit 1
fi

# Обновление системы
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Установка базовых пакетов
echo "📦 Установка базовых пакетов..."
apt install -y \
    curl \
    wget \
    git \
    nano \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Установка Python 3.11+
echo "🐍 Установка Python..."
apt install -y python3 python3-pip python3-venv python3-dev

# Установка Node.js 18+
echo "📦 Установка Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Установка Nginx
echo "🌐 Установка Nginx..."
apt install -y nginx
systemctl enable nginx

# Установка MySQL
echo "🗄️ Установка MySQL..."
apt install -y mysql-server
systemctl enable mysql

# Установка Redis
echo "📋 Установка Redis..."
apt install -y redis-server
systemctl enable redis-server

# Настройка firewall
echo "🔥 Настройка Firewall..."
ufw --force enable
ufw allow ssh
ufw allow http
ufw allow https
ufw allow 8000  # FastAPI (временно)

# Создание пользователя для приложения
echo "👤 Создание пользователя frozenbot..."
useradd -m -s /bin/bash frozenbot
usermod -aG sudo frozenbot

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p /var/www/frozenbot
mkdir -p /var/log/frozenbot
chown -R frozenbot:frozenbot /var/www/frozenbot
chown -R frozenbot:frozenbot /var/log/frozenbot

# Настройка MySQL
echo "🗄️ Настройка MySQL..."
systemctl start mysql

# Создание базы данных и пользователя
MYSQL_PASSWORD=$(openssl rand -base64 12)
echo "Пароль MySQL: $MYSQL_PASSWORD" > /root/mysql-credentials.txt

mysql <<EOF
CREATE DATABASE IF NOT EXISTS frozenbot_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'frozenbot'@'localhost' IDENTIFIED BY '$MYSQL_PASSWORD';
GRANT ALL PRIVILEGES ON frozenbot_db.* TO 'frozenbot'@'localhost';
FLUSH PRIVILEGES;
EOF

# Тестирование подключения
echo "🧪 Тестирование компонентов..."
systemctl status nginx --no-pager -l | head -5
systemctl status mysql --no-pager -l | head -5
systemctl status redis-server --no-pager -l | head -5

python3 --version
node --version
npm --version

echo ""
echo "✅ БАЗОВАЯ НАСТРОЙКА СЕРВЕРА ЗАВЕРШЕНА!"
echo "======================================="
echo "🐍 Python: $(python3 --version)"
echo "📦 Node.js: $(node --version)"
echo "🌐 Nginx: Установлен и запущен"
echo "🗄️ MySQL: Установлен и настроен"
echo "📋 Redis: Установлен и запущен"
echo "🔥 Firewall: Настроен"
echo ""
echo "📝 ВАЖНЫЕ ФАЙЛЫ:"
echo "MySQL пароль: /root/mysql-credentials.txt"
echo ""
echo "🔗 СЛЕДУЮЩИЙ ШАГ:"
echo "Загрузите проект: scp -r frozenbot-project/ root@server:/var/www/"
echo "Затем запустите: /var/www/frozenbot-project/deployment/production-deploy.sh"