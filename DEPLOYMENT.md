# 🚀 Инструкция по развертыванию на сервере

## 📋 Шаги развертывания

### 1. Клонирование репозитория
```bash
git clone https://github.com/trinity3ru/chanki.git
cd chanki
```

### 2. Установка зависимостей
```bash
# Установка UV (если не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Установка зависимостей
uv venv
uv pip install -r requirements.txt
```

### 3. Настройка переменных окружения
```bash
# Создайте файл .env
cp env_template.txt .env

# Отредактируйте .env файл
nano .env
```

**Обязательные переменные в .env:**
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 4. Инициализация базы данных
```bash
# Создание пустой базы данных
uv run init_database.py
```

### 5. Запуск приложения
```bash
# Запуск в фоновом режиме
uv run main.py &

# Или с помощью systemd (рекомендуется)
sudo systemctl enable chanki
sudo systemctl start chanki
```

## 🔧 Настройка systemd (опционально)

Создайте файл `/etc/systemd/system/chanki.service`:

```ini
[Unit]
Description=Site Access Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/chanki
ExecStart=/path/to/uv run main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 📊 Проверка работы

### Проверка логов
```bash
# Просмотр логов
tail -f logs/monitor.log

# Проверка статуса systemd
sudo systemctl status chanki
```

### Проверка базы данных
```bash
# Просмотр сайтов в базе
cat sites.json | jq .
```

## 🔄 Обновление приложения

```bash
# Остановка приложения
sudo systemctl stop chanki

# Обновление кода
git pull origin master

# Перезапуск
sudo systemctl start chanki
```

## 🚨 Устранение неполадок

### Проблема: "Файл sites.json не найден"
```bash
# Решение: инициализация базы данных
uv run init_database.py
```

### Проблема: "Ошибка кодировки"
- Убедитесь, что файл `sites.json` в кодировке UTF-8
- Проверьте права доступа к файлу

### Проблема: "Бот не отвечает"
- Проверьте токен бота в `.env`
- Убедитесь, что бот запущен и работает
- Проверьте логи на наличие ошибок

## 📁 Структура файлов

```
chanki/
├── main.py              # Главный файл приложения
├── config.py            # Конфигурация
├── database.py          # Работа с базой данных
├── site_monitor.py      # Мониторинг сайтов
├── telegram_bot.py      # Telegram бот
├── scheduler.py         # Планировщик задач
├── sites.json           # База данных сайтов (создается автоматически)
├── .env                 # Переменные окружения
├── requirements.txt     # Зависимости Python
└── logs/                # Папка с логами
```

## 🔐 Безопасность

- **НЕ** коммитьте файл `.env` в git
- **НЕ** коммитьте файл `sites.json` в git (содержит пользовательские данные)
- Регулярно создавайте резервные копии `sites.json`
- Используйте HTTPS для всех URL в базе данных

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в папке `logs/`
2. Убедитесь, что все зависимости установлены
3. Проверьте права доступа к файлам
4. Создайте issue в репозитории GitHub
