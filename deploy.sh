#!/bin/bash

# Развертывание бота мониторинга сайтов на сервере с уже установленным Docker
# Использование: ./deploy.sh
#
# Скрипт ничего не устанавливает в систему и не трогает чужие контейнеры,
# сети и volume'ы - работает только с compose-проектом из этого каталога.

set -euo pipefail

cd "$(dirname "$0")"

echo "🚀 Развертывание бота мониторинга сайтов"
echo "========================================"

# Docker и Compose v2 должны быть установлены заранее
if ! command -v docker &> /dev/null; then
    echo "❌ Docker не найден. Установите Docker и запустите скрипт повторно."
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose v2 не найден (нужна команда 'docker compose')."
    exit 1
fi

# Проверяем конфигурацию
if [ ! -f .env ]; then
    echo "❌ Файл .env не найден!"
    echo "   cp docker.env.example .env && nano .env"
    exit 1
fi

if grep -qE 'TELEGRAM_BOT_TOKEN=(ваш_токен_бота_здесь|your_token|test_token)' .env; then
    echo "❌ В .env остался placeholder вместо реального токена бота."
    exit 1
fi

# Имя контейнера должно быть свободно, иначе конфликт с соседним проектом
existing=$(docker ps -a --filter 'name=^chanki-site-monitor$' --format '{{.Names}}' || true)
owned=$(docker compose ps -aq site-monitor 2>/dev/null || true)

if [ -n "$existing" ] && [ -z "$owned" ]; then
    echo "❌ Контейнер chanki-site-monitor занят другим проектом."
    echo "   Измените container_name в docker-compose.yml и повторите."
    exit 1
fi

echo "🔍 Проверяем конфигурацию Compose..."
docker compose config > /dev/null

echo "🏗️ Собираем образ..."
docker compose build

echo "🚀 Запускаем контейнер..."
docker compose up -d

echo ""
echo "📊 Статус:"
docker compose ps

echo ""
echo "📝 Последние логи:"
docker compose logs --tail=20 site-monitor

echo ""
echo "✅ Развертывание завершено!"
echo ""
echo "📋 Управление:"
echo "  🔍 Логи:        docker compose logs -f site-monitor"
echo "  🔄 Перезапуск:  docker compose restart site-monitor"
echo "  ⏹️  Остановка:   docker compose stop site-monitor"
echo "  📊 Статус:      docker compose ps"
echo ""
echo "📱 Найдите бота в Telegram и отправьте /start"
