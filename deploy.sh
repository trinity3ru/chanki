#!/bin/bash

# Скрипт для развертывания приложения мониторинга сайтов на VPS
# Использование: ./deploy.sh

set -e

echo "🚀 Развертывание приложения мониторинга сайтов на VPS"
echo "=================================================="

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Устанавливаем..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

# Проверяем наличие UV
if ! command -v uv &> /dev/null; then
    echo "📦 Устанавливаем UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

# Создаем виртуальное окружение
echo "🔧 Создаем виртуальное окружение..."
python3 -m venv venv
source venv/bin/activate

# Устанавливаем зависимости
echo "📚 Устанавливаем зависимости..."
pip install -r requirements.txt

# Создаем systemd сервис
echo "⚙️ Создаем systemd сервис..."
sudo tee /etc/systemd/system/site-monitor.service > /dev/null <<EOF
[Unit]
Description=Site Monitoring Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd и включаем сервис
echo "🔄 Настраиваем автозапуск..."
sudo systemctl daemon-reload
sudo systemctl enable site-monitor

echo "✅ Развертывание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Создайте файл .env с токеном бота:"
echo "   echo 'TELEGRAM_BOT_TOKEN=ваш_токен' > .env"
echo ""
echo "2. Запустите сервис:"
echo "   sudo systemctl start site-monitor"
echo ""
echo "3. Проверьте статус:"
echo "   sudo systemctl status site-monitor"
echo ""
echo "4. Просмотр логов:"
echo "   sudo journalctl -u site-monitor -f"
echo ""
echo "🎯 Приложение готово к работе!"

