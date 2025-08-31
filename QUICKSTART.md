# ⚡ Быстрый запуск за 3 шага

## 🚀 Шаг 1: Создайте .env файл
```bash
echo "TELEGRAM_BOT_TOKEN=ваш_токен_бота" > .env
```

## 🔧 Шаг 2: Установите зависимости
```bash
# ВАЖНО: Сначала добавьте UV в PATH!
source $HOME/.local/bin/env

# Затем установите зависимости
uv pip install -r requirements.txt
```

## 🎯 Шаг 3: Запустите приложение
```bash
# Убедитесь что UV в PATH
source $HOME/.local/bin/env

# Запустите приложение
uv run main.py
```

---

## ⚠️ Важное замечание

**UV нужно добавлять в PATH в каждой новой сессии терминала:**
```bash
source $HOME/.local/bin/env
```

**Или добавьте в ~/.zshrc для автоматической загрузки:**
```bash
echo 'source $HOME/.local/bin/env' >> ~/.zshrc
source ~/.zshrc
```

---

## 📱 Тестирование в Telegram

1. Найдите вашего бота
2. Отправьте `/start`
3. Добавьте сайт: `/add https://google.com Google`
4. Проверьте: `/check`

## 🔄 Автоматический мониторинг

- ✅ Проверка каждые 6 часов
- 📱 Уведомления в Telegram
- 📝 Логи в monitor.log
- 💾 Данные в sites.json

---

**🎉 Готово! Ваш бот мониторинга работает!**
