#!/bin/bash

# Быстрое исправление проблем с правами доступа для Docker
echo "🔧 Исправление прав доступа для Docker контейнера..."

# Останавливаем контейнеры
echo "⏹️ Останавливаем контейнеры..."
docker-compose down

# Создаем необходимые директории
echo "📁 Создаем директории..."
mkdir -p data logs

# Создаем файлы
echo "📄 Создаем файлы..."
touch sites.json
touch logs/monitor.log

# Инициализируем sites.json если он пустой
if [ ! -s sites.json ]; then
    echo "[]" > sites.json
fi

# Устанавливаем правильные права доступа
echo "🔒 Устанавливаем права доступа..."
chmod 755 data logs
chmod 644 sites.json
chmod 666 logs/monitor.log

# Устанавливаем владельца (UID 1000 = пользователь sitebot в контейнере)
echo "👤 Устанавливаем владельца файлов..."
sudo chown -R 1000:1000 data logs sites.json 2>/dev/null || {
    echo "⚠️ Не удалось установить владельца, пробуем без sudo..."
    chown -R 1000:1000 data logs sites.json 2>/dev/null || {
        echo "⚠️ Устанавливаем права 777 для совместимости..."
        chmod 777 data logs
        chmod 666 sites.json logs/monitor.log
    }
}

# Проверяем результат
echo ""
echo "📊 Текущие права доступа:"
ls -la data logs sites.json logs/monitor.log 2>/dev/null

# Пересобираем и запускаем
echo ""
echo "🏗️ Пересборка контейнера..."
docker-compose build --no-cache

echo "🚀 Запуск контейнера..."
docker-compose up -d

# Ждем и проверяем
sleep 5
echo ""
echo "📊 Статус контейнера:"
docker-compose ps

echo ""
echo "📝 Последние логи:"
docker-compose logs --tail=10 site-monitor

echo ""
echo "✅ Исправление завершено!"
echo "Для просмотра логов в реальном времени: docker-compose logs -f site-monitor"
