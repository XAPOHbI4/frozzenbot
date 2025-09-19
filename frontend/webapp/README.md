# FrozenBot WebApp - Product Catalog

React-приложение для каталога замороженных продуктов с интеграцией Telegram WebApp.

## 🚀 Функциональность

### ✅ Реализовано (FE-003)

1. **Каталог товаров по категориям**
   - Сетка карточек товаров 2x2
   - Фильтрация по категориям
   - Карточки товаров с фото, названием, описанием, ценой
   - Кнопки +/- для управления количеством

2. **Корзина и заказ**
   - Боковая панель "Заказ" с выбранными товарами
   - Управление количеством товаров в корзине
   - Подсчет итоговой суммы
   - Кнопка "Заказать" с валидацией минимальной суммы (1500₽)

3. **Telegram WebApp интеграция**
   - Получение данных пользователя из Telegram
   - Автозаполнение формы заказа
   - Haptic feedback при взаимодействии
   - Адаптация к теме Telegram

4. **Responsive дизайн**
   - Mobile-first подход
   - Адаптация под размеры экрана Telegram
   - Touch-friendly интерфейс

## 📁 Структура проекта

```
src/
├── components/
│   ├── Cart/
│   │   ├── CartSidebar.tsx     # Боковая панель корзины
│   │   ├── CartSidebar.css     # Стили корзины
│   │   └── index.ts            # Экспорты корзины
│   ├── Category/
│   │   ├── CategoryFilter.tsx  # Фильтр категорий
│   │   ├── CategoryFilter.css  # Стили фильтра
│   │   └── index.ts            # Экспорты категорий
│   ├── Product/
│   │   ├── ProductCard.tsx     # Карточка товара
│   │   ├── ProductCard.css     # Стили карточки
│   │   └── index.ts            # Экспорты товаров
│   └── Payment/                # Существующие компоненты оплаты
├── hooks/
│   ├── useCatalog.ts          # Хук для каталога
│   └── usePayment.ts          # Хук для оплаты (существующий)
├── pages/
│   ├── Catalog.tsx            # Главная страница каталога
│   ├── Catalog.css            # Стили каталога
│   └── Checkout.tsx           # Страница оформления заказа
├── services/
│   ├── apiClient.ts           # API клиент + LocalCartManager
│   └── paymentService.ts      # Сервис оплаты (существующий)
├── styles/
│   ├── index.css              # Глобальные стили
│   └── App.css                # Стили приложения
├── types/
│   └── index.ts               # TypeScript типы
├── utils/
│   ├── telegram.ts            # Утилиты Telegram WebApp
│   ├── telegramIntegration.ts # Расширенная интеграция
│   └── webappConfig.ts        # Конфигурация приложения
├── App.tsx                    # Главное приложение
└── main.tsx                   # Точка входа
```

## 🛠 Технологии

- **React 18** с TypeScript
- **Vite** для сборки и разработки
- **Telegram WebApp SDK** для интеграции
- **CSS Modules** с CSS переменными
- **LocalStorage** для корзины

## 📋 API Endpoints

```typescript
// Используемые endpoints
GET /api/categories/          // Список категорий
GET /api/products/           // Товары с фильтрацией
GET /api/users/me           // Текущий пользователь
POST /api/orders/           // Создание заказа
```

## 🎨 Дизайн-система

### Цвета
- **Основной**: #007bff (синий)
- **Успех**: #28a745 (зеленый)
- **Предупреждение**: #ffc107 (желтый)
- **Ошибка**: #dc3545 (красный)

### Компоненты
- Карточки товаров с тенями
- Кнопки с haptic feedback
- Адаптивная сетка товаров
- Боковая панель корзины

## 🔧 Установка и запуск

### Требования
- Node.js 16+
- npm или yarn

### Установка зависимостей
```bash
npm install
```

### Запуск разработки
```bash
npm run dev
```

### Сборка для продакшена
```bash
npm run build
```

### Предпросмотр сборки
```bash
npm run preview
```

## 🌐 Окружения

### Development
- API URL: `http://localhost:8000`
- Telegram WebApp SDK: Подключен
- Hot reload включен

### Production
- API URL: `https://api.frozenbot.example.com`
- Оптимизированная сборка
- Service worker готов

## 📱 Telegram Integration

### Функции WebApp
- ✅ Haptic feedback при действиях
- ✅ Тема Telegram (светлая/темная)
- ✅ MainButton для checkout
- ✅ BackButton для навигации
- ✅ Данные пользователя
- ✅ Viewport management

### События
```typescript
// Haptic feedback примеры
telegramIntegration.haptic.addToCart()     // Добавление в корзину
telegramIntegration.haptic.checkout()      // Оформление заказа
telegramIntegration.haptic.success()       // Успешное действие
```

## 🎯 Особенности UX

1. **Корзина**
   - Sticky bottom bar на мобильных
   - Slide-out sidebar на десктоп
   - Валидация минимальной суммы заказа

2. **Товары**
   - Lazy loading изображений
   - Placeholder для отсутствующих фото
   - Анимации при добавлении в корзину

3. **Навигация**
   - Horizontal scroll для категорий
   - Back button интеграция
   - Touch-friendly кнопки (44px+)

## 🔍 Отладка

### Telegram WebApp
```javascript
// Проверка окружения
if (window.Telegram?.WebApp) {
  console.log('Telegram WebApp доступен');
  console.log('User:', window.Telegram.WebApp.initDataUnsafe.user);
}
```

### LocalStorage
```javascript
// Проверка корзины
console.log(localStorage.getItem('frozen_food_cart'));
```

## 📝 TODO

- [ ] Добавить loading скелетоны
- [ ] Оптимизировать изображения
- [ ] Добавить offline support
- [ ] Implement PWA features
- [ ] Add error boundaries

## 👥 Команда

- **Frontend**: React + TypeScript + Telegram WebApp
- **Backend**: Django + DRF (BE-005)
- **Integration**: FE-003 Product Catalog

## 📄 Лицензия

MIT License - FrozenBot Project