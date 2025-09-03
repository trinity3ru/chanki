#!/usr/bin/env python3
"""
Скрипт для восстановления sites.json на сервере
"""

import json
import os

def main():
    print("🔄 Восстановление sites.json на сервере")
    print("=" * 50)
    print()
    
    # Читаем локальный файл sites.json
    if not os.path.exists("sites.json"):
        print("❌ Файл sites.json не найден в текущей директории!")
        return
    
    try:
        with open("sites.json", "r", encoding="utf-8") as f:
            sites_data = json.load(f)
        
        print(f"✅ Загружено {len(sites_data)} сайтов из локального файла")
        
        # Показываем список сайтов
        print("\n📋 Список сайтов:")
        for site in sites_data:
            print(f"  ID {site['id']}: {site['name']} ({site['url']})")
        
        print("\n📋 Команды для восстановления на сервере:")
        print("=" * 50)
        print()
        
        print("1. Остановите контейнер:")
        print("   docker-compose down")
        print()
        
        print("2. Скопируйте файл sites.json в контейнер:")
        print("   docker cp sites.json site-monitor-bot:/app/host_data/sites.json")
        print()
        
        print("3. Проверьте, что файл скопировался:")
        print("   docker exec site-monitor-bot ls -la /app/host_data/sites.json")
        print()
        
        print("4. Проверьте содержимое файла:")
        print("   docker exec site-monitor-bot head -5 /app/host_data/sites.json")
        print()
        
        print("5. Запустите контейнер:")
        print("   docker-compose up -d")
        print()
        
        print("6. Проверьте логи:")
        print("   docker logs --tail 10 site-monitor-bot")
        print()
        
        print("=" * 50)
        print("🎯 После восстановления команда /remove promineral.ru должна работать!")
        
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")

if __name__ == "__main__":
    main()
