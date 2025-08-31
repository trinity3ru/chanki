# 🚀 ЗАПУСК ПРИЛОЖЕНИЯ

## ⚡ Самый быстрый способ (рекомендуется)

### 1. Настройте UV (один раз)
```bash
source setup_uv.sh
```

### 2. Создайте .env файл
```bash
# Используйте шаблон
cp env_template.txt .env

# Или создайте напрямую
echo "TELEGRAM_BOT_TOKEN=ваш_токен_бота" > .env

# Ограничьте доступ к файлу
chmod 600 .env
```

### 3. Запустите приложение
```bash
uv run main.py
```

---

## 🔧 Альтернативный способ

### Если UV не работает:
```bash
# Добавьте UV в PATH вручную
source $HOME/.local/bin/env

# Проверьте что UV доступен
uv --version

# Запустите приложение
uv run main.py
```

---

## 🧪 Тестирование

### Запустите тесты:
```bash
source setup_uv.sh  # или source $HOME/.local/bin/env
uv run test_app.py
```

### Если тесты прошли - приложение готово!

---

## 🚨 Решение проблем

### Ошибка "command not found: uv"
```bash
# Решение 1: Используйте setup_uv.sh
source setup_uv.sh

# Решение 2: Добавьте в PATH вручную
source $HOME/.local/bin/env

# Решение 3: Добавьте в ~/.zshrc навсегда
echo 'source $HOME/.local/bin/env' >> ~/.zshrc
source ~/.zshrc
```

### Ошибка "Токен не найден"
```bash
# Проверьте .env файл
cat .env

# Пересоздайте если нужно
echo "TELEGRAM_BOT_TOKEN=ваш_токен" > .env
```

---

## 📱 После запуска

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Добавьте сайт: `/add https://google.com Google`
4. Проверьте: `/check`

---

## 🔒 Безопасность

### ⚠️ ВАЖНО: Проверьте перед загрузкой в git
```bash
# Убедитесь что .env НЕ отслеживается
git status

# .env не должен появляться в списке файлов для коммита
```

### Файлы, которые НЕ попадут в git:
- ✅ `.env` - токены и пароли
- ✅ `sites.json` - данные пользователей  
- ✅ `monitor.log` - логи приложения
- ✅ `__pycache__/` - Python кеш

**📖 Подробнее о безопасности: см. SECURITY.md**

---

**🎯 Приложение готово к работе!**

