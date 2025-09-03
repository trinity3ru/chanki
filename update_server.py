#!/usr/bin/env python3
"""
Скрипт для обновления кода на сервере
Копирует исправленный telegram_bot.py на сервер и перезапускает контейнер
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - успешно")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - ошибка")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} - исключение: {e}")
        return False
    return True

def main():
    print("🚀 Обновление кода на сервере...")
    print("=" * 50)
    
    # Проверяем, что файл telegram_bot.py существует
    if not os.path.exists("telegram_bot.py"):
        print("❌ Файл telegram_bot.py не найден!")
        return
    
    print("📋 Инструкции для обновления на сервере:")
    print("=" * 50)
    print()
    print("1. Скопируйте файл telegram_bot.py на сервер:")
    print("   scp telegram_bot.py root@your-server:/home/chanki/")
    print()
    print("2. Подключитесь к серверу:")
    print("   ssh root@your-server")
    print()
    print("3. Перейдите в директорию проекта:")
    print("   cd /home/chanki")
    print()
    print("4. Остановите контейнер:")
    print("   docker-compose down")
    print()
    print("5. Запустите контейнер заново:")
    print("   docker-compose up -d")
    print()
    print("6. Проверьте логи:")
    print("   docker logs site-monitor-bot")
    print()
    print("=" * 50)
    print("🎯 После обновления команда /remove promineral.ru должна работать!")
    print("   (Сайт имеет ID = 8, но теперь можно удалять по URL)")

if __name__ == "__main__":
    main()
