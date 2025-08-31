#!/bin/bash

# Скрипт для исправления проблем с Docker volumes
# Исправляет ошибку "IsADirectoryError: monitor.log"

echo "🔧 Исправление проблем с Docker volumes..."
echo "========================================="

# Останавливаем контейнеры
echo "⏹️ Останавливаем контейнеры..."
docker-compose down

# Удаляем неправильно созданные директории
echo "🗑️ Удаляем неправильно созданные файлы/директории..."
sudo rm -rf sites.json monitor.log 2>/dev/null || rm -rf sites.json monitor.log

# Создаем правильные директории
echo "📁 Создаем правильную структуру директорий..."
mkdir -p data logs

# Создаем пустые файлы
echo "📄 Создаем файлы данных..."
touch sites.json
echo "[]" > sites.json
touch monitor.log

# Устанавливаем права доступа
echo "🔒 Настраиваем права доступа..."
chmod 755 data logs
chmod 644 sites.json monitor.log

# Проверяем .env файл
echo "🔍 Проверяем конфигурацию..."
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "Создайте его: echo 'TELEGRAM_BOT_TOKEN=ваш_токен' > .env"
    exit 1
fi

if grep -q "test_token\|ваш_токен\|your_token" .env; then
    echo "⚠️ В .env обнаружен тестовый токен. Замените его на реальный!"
fi

# Пересобираем образ
echo "🏗️ Пересобираем Docker образ..."
docker-compose build --no-cache

# Запускаем контейнеры
echo "🚀 Запускаем контейнеры..."
docker-compose up -d

# Ждем немного и проверяем статус
sleep 5
echo ""
echo "📊 Статус контейнеров:"
docker-compose ps

echo ""
echo "📝 Последние логи:"
docker-compose logs --tail=10 site-monitor

echo ""
echo "✅ Исправление завершено!"
echo ""
echo "Для мониторинга логов в реальном времени:"
echo "docker-compose logs -f site-monitor"
