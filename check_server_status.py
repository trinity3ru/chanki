#!/usr/bin/env python3
"""
Скрипт для проверки статуса сервера и файла sites.json
"""

def main():
    print("🔍 Диагностика проблемы с sites.json на сервере")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Проверьте размер файла sites.json на хосте:")
    print("   ls -la sites.json")
    print()
    
    print("2. Проверьте размер файла в контейнере:")
    print("   docker exec site-monitor-bot ls -la /app/host_data/sites.json")
    print()
    
    print("3. Проверьте содержимое файла в контейнере:")
    print("   docker exec site-monitor-bot cat /app/host_data/sites.json")
    print()
    
    print("4. Проверьте переменные окружения:")
    print("   docker exec site-monitor-bot env | grep SITES")
    print()
    
    print("5. Проверьте логи приложения:")
    print("   docker logs --tail 20 site-monitor-bot")
    print()
    
    print("6. Проверьте права доступа к файлу:")
    print("   ls -la host_data/")
    print()
    
    print("=" * 60)
    print("🚨 Возможные причины проблемы:")
    print("=" * 60)
    print()
    print("1. Файл sites.json перезаписывается при запуске")
    print("2. Неправильные права доступа к файлу")
    print("3. Проблема с монтированием volume в Docker")
    print("4. Приложение создает новый пустой файл при инициализации")
    print()
    
    print("💡 Решение:")
    print("=" * 60)
    print()
    print("1. Скопируйте ваш файл sites.json в контейнер:")
    print("   docker cp sites.json site-monitor-bot:/app/host_data/sites.json")
    print()
    print("2. Проверьте, что файл скопировался:")
    print("   docker exec site-monitor-bot ls -la /app/host_data/sites.json")
    print()
    print("3. Перезапустите контейнер:")
    print("   docker-compose restart")
    print()

if __name__ == "__main__":
    main()
