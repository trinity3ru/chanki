#!/usr/bin/env python3
"""
Скрипт для переключения на ветку master и удаления main
"""

def main():
    print("🔄 Переключение на ветку master и удаление main")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Переключитесь на ветку master:")
    print("   git checkout master")
    print()
    
    print("2. Убедитесь, что у вас последняя версия:")
    print("   git pull origin master")
    print()
    
    print("3. Удалите ветку main:")
    print("   git branch -D main")
    print()
    
    print("4. Удалите удаленную ветку main:")
    print("   git push origin --delete main")
    print()
    
    print("5. Установите master как основную ветку:")
    print("   git branch --set-upstream-to=origin/master master")
    print()
    
    print("6. Проверьте, что все работает:")
    print("   git status")
    print("   git log --oneline -3")
    print()
    
    print("7. Проверьте, что код обновился:")
    print("   grep -n 'getsize' database.py")
    print()
    
    print("8. Перезапустите контейнер:")
    print("   docker-compose restart")
    print()
    
    print("=" * 60)
    print("🎯 Альтернативный способ (если master не существует):")
    print("=" * 60)
    print()
    print("1. Создайте ветку master из origin/master:")
    print("   git checkout -b master origin/master")
    print()
    print("2. Удалите ветку main:")
    print("   git branch -D main")
    print()
    print("3. Установите master как основную:")
    print("   git branch --set-upstream-to=origin/master master")
    print()
    
    print("=" * 60)
    print("✅ После этого:")
    print("=" * 60)
    print()
    print("- Все коммиты будут идти в master")
    print("- На сервере будет актуальный код")
    print("- Файл sites.json не будет затираться")
    print("- Команда /remove promineral.ru будет работать")
    print()

if __name__ == "__main__":
    main()
