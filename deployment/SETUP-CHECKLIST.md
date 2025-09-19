# 🚀 ЧЕКЛИСТ НАСТРОЙКИ СЕРВЕРА FROZENBOT

## ✅ ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ

### 📋 Данные которые нужны ОТ ВАС:

#### 🖥️ **Сервер:**
- [ ] IP адрес сервера: `_____._____._____.____`
- [ ] SSH логин: `root` или `ubuntu`
- [ ] SSH пароль или приватный ключ
- [ ] ОС: Ubuntu 20.04+ или Debian 11+

#### 🌐 **Домен (domashniystandart.com):**
- [ ] Доступ к DNS настройкам домена
- [ ] A запись: `domashniystandart.com → IP_СЕРВЕРА`
- [ ] A запись: `www.domashniystandart.com → IP_СЕРВЕРА`

#### 🤖 **Telegram Bot:**
- [ ] BOT_TOKEN от @BotFather: `xxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
- [ ] ADMIN_ID (ваш Telegram ID): `xxxxxxxxx`
- [ ] PAYMENT_PROVIDER_TOKEN (если есть): `xxxxxxxxx:TEST:xxx` или `xxxxxxxxx:LIVE:xxx`

#### 📧 **Email для SSL:**
- [ ] Email адрес для уведомлений SSL: `admin@domashniystandart.com`

---

## 🎯 ПЛАН ВЫПОЛНЕНИЯ (ПОШАГОВО)

### **ШАГ 1: ПОДКЛЮЧЕНИЕ К СЕРВЕРУ (2 минуты)**
```bash
# Подключение по SSH
ssh root@IP_СЕРВЕРА
# ИЛИ
ssh ubuntu@IP_СЕРВЕРА
```

**✅ Результат:** Подключились к серверу

---

### **ШАГ 2: НАСТРОЙКА DNS (5 минут)**
**Где:** В панели управления вашего регистратора домена

```
Тип записи: A
Имя: @
Значение: IP_СЕРВЕРА
TTL: 300

Тип записи: A
Имя: www
Значение: IP_СЕРВЕРА
TTL: 300
```

**✅ Результат:** `ping domashniystandart.com` возвращает IP сервера

---

### **ШАГ 3: БАЗОВАЯ НАСТРОЙКА СЕРВЕРА (10 минут)**
```bash
# Скачать скрипт настройки
wget https://raw.githubusercontent.com/your-repo/server-setup-minimal.sh
# ИЛИ скопировать содержимое файла server-setup-minimal.sh

# Запустить настройку
chmod +x server-setup-minimal.sh
sudo ./server-setup-minimal.sh
```

**✅ Результат:**
- Python 3.11+ установлен
- Node.js 18+ установлен
- Nginx, MySQL, Redis запущены
- Firewall настроен
- Пользователь frozenbot создан

---

### **ШАГ 4: ЗАГРУЗКА ПРОЕКТА (5 минут)**
```bash
# На вашем компьютере:
scp -r "C:\Users\XAPOHbI4\Desktop\Замороженная еда\frozenbot-project" root@IP_СЕРВЕРА:/var/www/

# На сервере:
cd /var/www
chown -R frozenbot:frozenbot frozenbot-project
```

**✅ Результат:** Проект загружен в `/var/www/frozenbot-project`

---

### **ШАГ 5: НАСТРОЙКА ENVIRONMENT (3 минуты)**
```bash
# На сервере
cd /var/www/frozenbot-project/backend
cp .env.production .env

# Отредактировать .env файл
nano .env
```

**Обновить эти строки:**
```env
BOT_TOKEN=ваш-реальный-токен-от-BotFather
ADMIN_ID=ваш-telegram-id
PAYMENT_PROVIDER_TOKEN=ваш-платежный-токен
DATABASE_URL=mysql+aiomysql://frozenbot:ПАРОЛЬ_ИЗ_mysql-credentials.txt@localhost:3306/frozenbot_db
```

**✅ Результат:** Environment переменные настроены

---

### **ШАГ 6: УСТАНОВКА SSL И DEPLOYMENT (10 минут)**
```bash
# На сервере
cd /var/www/frozenbot-project/deployment
chmod +x *.sh

# Запуск автоматической установки
./ssl-setup.sh
./production-deploy.sh
```

**✅ Результат:**
- SSL сертификат получен
- Nginx настроен
- Frontend собран
- Backend запущен
- Systemd сервисы работают

---

### **ШАГ 7: ПРОВЕРКА РАБОТЫ (2 минуты)**
```bash
# Проверка статуса сервисов
systemctl status frozenbot-api
systemctl status frozenbot-bot
systemctl status nginx

# Проверка в браузере:
# https://domashniystandart.com/api/docs
# https://domashniystandart.com/admin
# https://domashniystandart.com/webapp
```

**✅ Результат:** Все сервисы работают, сайт доступен

---

## 🚨 ВОЗМОЖНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ

### **Проблема: DNS не обновился**
```bash
# Проверка
nslookup domashniystandart.com
# Решение: подождать 10-30 минут или обратиться к регистратору
```

### **Проблема: SSL сертификат не получился**
```bash
# Проверка портов
ufw status
# Решение: убедиться что порты 80 и 443 открыты
```

### **Проблема: База данных не подключается**
```bash
# Проверка пароля
cat /root/mysql-credentials.txt
# Обновить в .env файле
```

### **Проблема: Bot не отвечает**
```bash
# Проверка логов
journalctl -u frozenbot-bot -f
# Проверка токена в .env
```

---

## 📞 ПОДДЕРЖКА

### **Логи для диагностики:**
```bash
# API логи
journalctl -u frozenbot-api -f

# Bot логи
journalctl -u frozenbot-bot -f

# Nginx логи
tail -f /var/log/nginx/frozenbot_error.log

# Системные логи
dmesg | tail
```

### **Перезапуск сервисов:**
```bash
systemctl restart frozenbot-api
systemctl restart frozenbot-bot
systemctl restart nginx
```

---

## 🎉 УСПЕШНАЯ УСТАНОВКА

### **После завершения у вас будет:**
- ✅ **API:** https://domashniystandart.com/api/
- ✅ **Admin Panel:** https://domashniystandart.com/admin
- ✅ **WebApp:** https://domashniystandart.com/webapp
- ✅ **SSL сертификат:** Автообновляемый Let's Encrypt
- ✅ **Мониторинг:** Логи и метрики настроены

### **Время установки:** 30-40 минут
### **Сложность:** Средняя (следуя инструкции)