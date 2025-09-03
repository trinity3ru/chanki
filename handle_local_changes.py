#!/usr/bin/env python3
"""
Скрипт для обработки локальных изменений на сервере
"""

def main():
    print("🔧 Обработка локальных изменений на сервере")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Посмотрим, какие изменения есть:")
    print("   git status")
    print()
    
    print("2. Посмотрим, что изменилось в telegram_bot.py:")
    print("   git diff telegram_bot.py")
    print()
    
    print("3. Вариант A - Сохранить изменения (stash):")
    print("   git stash")
    print("   git checkout master")
    print("   git pull origin master")
    print("   # Если нужно применить изменения обратно:")
    print("   git stash pop")
    print()
    
    print("4. Вариант B - Отбросить изменения (рекомендуется):")
    print("   git checkout -- telegram_bot.py")
    print("   git checkout master")
    print("   git pull origin master")
    print()
    
    print("5. Вариант C - Принудительно сбросить все:")
    print("   git reset --hard HEAD")
    print("   git checkout master")
    print("   git pull origin master")
    print()
    
    print("=" * 60)
    print("🎯 Рекомендуемая последовательность:")
    print("=" * 60)
    print()
    print("git status")
    print("git diff telegram_bot.py")
    print("git checkout -- telegram_bot.py")
    print("git checkout master")
    print("git pull origin master")
    print("grep -n 'getsize' database.py")
    print("docker-compose restart")
    print()
    
    print("=" * 60)
    print("💡 Объяснение:")
    print("=" * 60)
    print()
    print("- git checkout -- telegram_bot.py - отбросит локальные изменения")
    print("- Это безопасно, так как все важные изменения уже в GitHub")
    print("- После этого вы получите актуальный код с исправлениями")
    print()

if __name__ == "__main__":
    main()
