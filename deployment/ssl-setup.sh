#!/bin/bash
# SSL Setup Script for FrozenFoodBot
# Domain: domashniystandart.com

echo "🔐 SSL УСТАНОВКА ДЛЯ DOMASHNIYSTANDART.COM"
echo "=========================================="

# Проверяем, что скрипт запущен от root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Этот скрипт должен запускаться от root (sudo)"
   exit 1
fi

# Обновляем систему
echo "📦 Обновление системы..."
apt update && apt upgrade -y

# Устанавливаем Nginx если не установлен
if ! command -v nginx &> /dev/null; then
    echo "📦 Установка Nginx..."
    apt install nginx -y
    systemctl enable nginx
fi

# Устанавливаем Certbot
echo "📦 Установка Certbot для SSL..."
apt install snapd -y
snap install core; snap refresh core
snap install --classic certbot

# Создаем symlink для certbot
ln -sf /snap/bin/certbot /usr/bin/certbot

# Останавливаем Nginx временно для получения сертификата
systemctl stop nginx

# Получаем SSL сертификат
echo "🔐 Получение SSL сертификата для domashniystandart.com..."
certbot certonly --standalone --agree-tos --no-eff-email --email admin@domashniystandart.com -d domashniystandart.com -d www.domashniystandart.com

# Проверяем успешность получения сертификата
if [ -f "/etc/letsencrypt/live/domashniystandart.com/fullchain.pem" ]; then
    echo "✅ SSL сертификат успешно получен!"

    # Копируем конфигурацию Nginx
    echo "📝 Настройка Nginx конфигурации..."
    cp /path/to/nginx-config.conf /etc/nginx/sites-available/frozenbot
    ln -sf /etc/nginx/sites-available/frozenbot /etc/nginx/sites-enabled/

    # Удаляем default конфигурацию если есть
    rm -f /etc/nginx/sites-enabled/default

    # Проверяем конфигурацию Nginx
    nginx -t

    if [ $? -eq 0 ]; then
        echo "✅ Nginx конфигурация корректна"
        systemctl start nginx
        systemctl reload nginx
        echo "🚀 Nginx запущен с SSL!"
    else
        echo "❌ Ошибка в конфигурации Nginx"
        systemctl start nginx  # Запускаем хотя бы базовый Nginx
        exit 1
    fi

    # Настраиваем автообновление сертификата
    echo "⏰ Настройка автообновления SSL..."
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

    echo ""
    echo "🎉 SSL УСТАНОВКА ЗАВЕРШЕНА!"
    echo "==============================="
    echo "✅ Домен: https://domashniystandart.com"
    echo "✅ SSL сертификат активен"
    echo "✅ Nginx настроен"
    echo "✅ Автообновление SSL настроено"
    echo ""
    echo "🔗 Проверьте: https://domashniystandart.com"

else
    echo "❌ Ошибка получения SSL сертификата"
    systemctl start nginx
    exit 1
fi

# Показываем статус
echo "📊 Статус служб:"
systemctl status nginx --no-pager -l
echo ""
echo "🔐 Статус SSL:"
certbot certificates