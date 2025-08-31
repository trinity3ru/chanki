#!/bin/bash

# Скрипт для настройки UV в PATH
# Запустите: source setup_uv.sh

echo "🔧 Настройка UV в PATH..."

# Проверяем наличие UV
if ! command -v uv &> /dev/null; then
    echo "❌ UV не найден. Устанавливаем..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Добавляем UV в PATH
export PATH="$HOME/.local/bin:$PATH"

# Проверяем что UV доступен
if command -v uv &> /dev/null; then
    echo "✅ UV успешно добавлен в PATH"
    echo "📦 Версия UV: $(uv --version)"
    echo ""
    echo "💡 Теперь вы можете использовать команды:"
    echo "   uv pip install -r requirements.txt"
    echo "   uv run main.py"
    echo "   uv run test_app.py"
    echo ""
    echo "⚠️  ВАЖНО: В каждой новой сессии терминала запускайте:"
    echo "   source setup_uv.sh"
    echo ""
    echo "🔗 Или добавьте в ~/.zshrc для автоматической загрузки:"
    echo "   echo 'source $(pwd)/setup_uv.sh' >> ~/.zshrc"
else
    echo "❌ Ошибка: UV не удалось добавить в PATH"
    exit 1
fi

