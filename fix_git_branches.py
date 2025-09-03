#!/usr/bin/env python3
"""
Скрипт для исправления проблемы с ветками Git на сервере
"""

def main():
    print("🔧 Исправление проблемы с ветками Git на сервере")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Сначала посмотрим, что у нас есть:")
    print("   git branch -a")
    print()
    
    print("2. Посмотрим различия между ветками:")
    print("   git log --oneline --graph --all -10")
    print()
    
    print("3. Выберем стратегию слияния (рекомендую merge):")
    print("   git config pull.rebase false")
    print()
    
    print("4. Теперь попробуем слить изменения:")
    print("   git pull origin master")
    print()
    
    print("5. Если возникнут конфликты, разрешим их:")
    print("   git status")
    print("   # Отредактируйте файлы с конфликтами")
    print("   git add .")
    print("   git commit -m 'Merge master into main'")
    print()
    
    print("6. Альтернативный способ - принудительное обновление:")
    print("   git fetch origin")
    print("   git reset --hard origin/master")
    print()
    
    print("7. Проверим, что обновилось:")
    print("   grep -n 'getsize' database.py")
    print()
    
    print("8. Перезапустим контейнер:")
    print("   docker-compose restart")
    print()
    
    print("=" * 60)
    print("🎯 Рекомендуемая последовательность:")
    print("=" * 60)
    print()
    print("git config pull.rebase false")
    print("git pull origin master")
    print("docker-compose restart")
    print()
    print("Если не сработает:")
    print("git fetch origin")
    print("git reset --hard origin/master")
    print("docker-compose restart")
    print()

if __name__ == "__main__":
    main()
