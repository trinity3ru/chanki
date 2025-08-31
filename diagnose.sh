#!/bin/bash

# Скрипт диагностики приложения мониторинга сайтов
# Использование: ./diagnose.sh

echo "🔍 Диагностика приложения мониторинга сайтов"
echo "============================================="

# Проверяем Docker развертывание
if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
    echo ""
    echo "🐳 DOCKER РАЗВЕРТЫВАНИЕ ОБНАРУЖЕНО"
    echo "================================="
    
    echo "📊 Статус контейнеров:"
    docker-compose ps
    
    echo ""
    echo "📝 Последние логи контейнера:"
    docker-compose logs --tail=20 site-monitor
    
    echo ""
    echo "💾 Использование ресурсов:"
    docker stats site-monitor-bot --no-stream 2>/dev/null || echo "Контейнер не запущен"
    
else
    echo ""
    echo "📦 ОБЫЧНОЕ РАЗВЕРТЫВАНИЕ"
    echo "======================"
    
    echo "🔍 Поиск процессов Python:"
    ps aux | grep python | grep -v grep
    
    echo ""
    echo "📝 Локальные логи (последние 20 строк):"
    if [ -f "monitor.log" ]; then
        tail -20 monitor.log
    else
        echo "Файл monitor.log не найден"
    fi
    
    echo ""
    echo "🔧 Статус systemd сервиса (если используется):"
    sudo systemctl status site-monitor 2>/dev/null || echo "Сервис site-monitor не найден"
fi

echo ""
echo "🔐 ПРОВЕРКА КОНФИГУРАЦИИ"
echo "======================="

echo "📄 Содержимое .env файла:"
if [ -f ".env" ]; then
    cat .env | sed 's/TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=***скрыто***/'
else
    echo "❌ Файл .env не найден!"
fi

echo ""
echo "🌐 ПРОВЕРКА СЕТЕВОГО ПОДКЛЮЧЕНИЯ"
echo "==============================="

echo "📡 Проверка доступности Telegram API:"
if curl -s --connect-timeout 5 "https://api.telegram.org" > /dev/null; then
    echo "✅ Telegram API доступен"
else
    echo "❌ Telegram API недоступен"
fi

echo ""
echo "🔍 Проверка DNS:"
if nslookup api.telegram.org > /dev/null 2>&1; then
    echo "✅ DNS работает"
else
    echo "❌ Проблемы с DNS"
fi

echo ""
echo "📂 ФАЙЛЫ ПРОЕКТА"
echo "==============="

echo "📋 Основные файлы:"
ls -la *.py *.json *.log 2>/dev/null || echo "Некоторые файлы отсутствуют"

echo ""
echo "💾 Размер файлов данных:"
du -sh sites.json monitor.log 2>/dev/null || echo "Файлы данных не найдены"

echo ""
echo "🏥 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ"
echo "============================="

if [ ! -f ".env" ]; then
    echo "❌ Создайте файл .env с токеном бота"
    echo "   echo 'TELEGRAM_BOT_TOKEN=ваш_токен' > .env"
fi

if [ -f ".env" ]; then
    if grep -q "test_token\|ваш_токен\|your_token" .env; then
        echo "❌ Замените тестовый токен на реальный в файле .env"
    fi
fi

echo ""
echo "📞 ДЛЯ ПОЛУЧЕНИЯ ПОДРОБНЫХ ЛОГОВ:"
echo "================================"

if [ -f "docker-compose.yml" ]; then
    echo "🐳 Docker логи в реальном времени:"
    echo "   docker-compose logs -f site-monitor"
    echo ""
    echo "🐳 Перезапуск контейнера:"
    echo "   docker-compose restart site-monitor"
else
    echo "📦 Локальные логи в реальном времени:"
    echo "   tail -f monitor.log"
    echo ""
    echo "📦 Ручной запуск для отладки:"
    echo "   source setup_uv.sh && uv run main.py"
fi

echo ""
echo "✅ Диагностика завершена!"
