#!/bin/bash

# Скрипт для развертывания приложения мониторинга сайтов на VPS с Docker
# Использование: ./docker-deploy.sh

set -e

echo "🐳 Развертывание приложения мониторинга сайтов с Docker"
echo "======================================================"

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Устанавливаем..."
    
    # Обновляем систему
    sudo apt update && sudo apt upgrade -y
    
    # Устанавливаем Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Добавляем пользователя в группу docker
    sudo usermod -aG docker $USER
    
    echo "✅ Docker установлен. Перезайдите в систему для применения изменений группы."
    echo "Затем запустите скрипт повторно."
    exit 0
fi

# Проверяем наличие Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "📦 Устанавливаем Docker Compose..."
    
    # Скачиваем Docker Compose
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    echo "✅ Docker Compose установлен"
fi

# Проверяем наличие .env файла
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo ""
    echo "📝 Создайте файл .env с токеном бота:"
    echo "echo 'TELEGRAM_BOT_TOKEN=ваш_токен_здесь' > .env"
    echo ""
    echo "🤖 Получить токен можно у @BotFather в Telegram"
    exit 1
fi

# Создаем директории для данных
echo "📁 Создаем директории для данных..."
mkdir -p data logs

# Устанавливаем права доступа
chmod 755 data logs

# Проверяем синтаксис docker-compose.yml
echo "🔍 Проверяем конфигурацию Docker Compose..."
docker-compose config > /dev/null

# Останавливаем существующие контейнеры (если есть)
echo "🔄 Останавливаем существующие контейнеры..."
docker-compose down || true

# Собираем образ
echo "🏗️ Собираем Docker образ..."
docker-compose build

# Запускаем контейнеры
echo "🚀 Запускаем приложение..."
docker-compose up -d

# Проверяем статус
echo "📊 Проверяем статус контейнеров..."
docker-compose ps

# Показываем логи
echo "📝 Последние логи приложения:"
docker-compose logs --tail=20 site-monitor

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Управление приложением:"
echo "  🔍 Просмотр логов:     docker-compose logs -f site-monitor"
echo "  🔄 Перезапуск:         docker-compose restart site-monitor"
echo "  ⏹️  Остановка:          docker-compose stop"
echo "  🗑️  Удаление:           docker-compose down"
echo "  📊 Статус:             docker-compose ps"
echo ""
echo "📱 Найдите вашего бота в Telegram и отправьте /start"
echo ""
echo "🎯 Приложение запущено и готово к работе!"
