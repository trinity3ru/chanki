#!/bin/bash

# Диагностика бота мониторинга сайтов
# Использование: ./diagnose.sh
#
# Только чтение: ничего не запускает, не перезапускает и не удаляет.

set -uo pipefail

cd "$(dirname "$0")"

echo "🔍 Диагностика бота мониторинга сайтов"
echo "======================================"

echo ""
echo "📊 Статус контейнера:"
docker compose ps

echo ""
echo "💾 Использование ресурсов:"
docker stats chanki-site-monitor --no-stream 2>/dev/null || echo "Контейнер не запущен"

echo ""
echo "📝 Последние логи (50 строк):"
docker compose logs --tail=50 site-monitor

echo ""
echo "🔐 ПРОВЕРКА КОНФИГУРАЦИИ"
echo "======================="

if [ -f ".env" ]; then
    # Значения не показываем - только наличие ключей
    echo "✅ Файл .env найден. Заданные переменные:"
    grep -oE '^[A-Z_]+' .env | sed 's/^/   /'

    if grep -qE 'TELEGRAM_BOT_TOKEN=(ваш_токен_бота_здесь|your_token|test_token)' .env; then
        echo "❌ В .env остался placeholder вместо реального токена!"
    fi
else
    echo "❌ Файл .env не найден!"
fi

echo ""
echo "💽 ДАННЫЕ ПРИЛОЖЕНИЯ"
echo "==================="

echo "📁 Volume'ы проекта:"
docker volume ls --filter 'name=chanki' --format '   {{.Name}}'

echo ""
echo "📊 Размер данных внутри контейнера:"
docker compose exec -T site-monitor du -sh /app/data /app/logs 2>/dev/null \
    || echo "   Контейнер не запущен, размер недоступен"

echo ""
echo "🌐 ПРОВЕРКА СЕТИ ИЗ КОНТЕЙНЕРА"
echo "============================="

docker compose exec -T site-monitor python -c \
    "import requests; requests.get('https://api.telegram.org', timeout=5); print('✅ Telegram API доступен')" \
    2>/dev/null || echo "❌ Telegram API недоступен или контейнер не запущен"

echo ""
echo "📞 ПОЛЕЗНЫЕ КОМАНДЫ"
echo "=================="
echo "   Логи в реальном времени:  docker compose logs -f site-monitor"
echo "   Перезапуск:               docker compose restart site-monitor"
echo ""
echo "✅ Диагностика завершена!"
