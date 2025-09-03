#!/usr/bin/env python3
"""
Скрипт для диагностики проблемы с обновлением на сервере
"""

def main():
    print("🔍 Диагностика проблемы с обновлением на сервере")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Проверьте текущий коммит на сервере:")
    print("   git log --oneline -5")
    print()
    
    print("2. Проверьте статус Git на сервере:")
    print("   git status")
    print()
    
    print("3. Проверьте, есть ли изменения для pull:")
    print("   git fetch origin")
    print("   git log HEAD..origin/master --oneline")
    print()
    
    print("4. Попробуйте принудительно обновить:")
    print("   git pull origin master")
    print()
    
    print("5. Проверьте, что файл обновился:")
    print("   ls -la database.py")
    print("   grep -n 'getsize' database.py")
    print()
    
    print("6. Если файл не обновился, проверьте права доступа:")
    print("   ls -la .git/")
    print("   whoami")
    print()
    
    print("=" * 60)
    print("🚨 Возможные причины:")
    print("=" * 60)
    print()
    print("1. Git pull не выполнился корректно")
    print("2. Файл заблокирован или имеет неправильные права")
    print("3. Конфликт слияния")
    print("4. Кэширование в Docker")
    print()
    
    print("💡 Альтернативное решение:")
    print("=" * 60)
    print()
    print("Если git pull не работает, скопируйте файл вручную:")
    print()
    print("1. Скопируйте database.py на сервер:")
    print("   scp database.py root@your-server:/home/chanki/")
    print()
    print("2. Перезапустите контейнер:")
    print("   docker-compose restart")
    print()
    print("3. Проверьте, что обновилось:")
    print("   docker exec site-monitor-bot grep -n 'getsize' /app/database.py")
    print()

if __name__ == "__main__":
    main()
