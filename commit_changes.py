#!/usr/bin/env python3
"""
Скрипт для коммита изменений в Git
"""

import subprocess
import sys

def run_git_command(command):
    """Выполняет git команду"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {command} - успешно")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {command} - ошибка")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {command} - исключение: {e}")
        return False

def main():
    print("🔄 Коммит изменений в Git...")
    print("=" * 50)
    
    # Добавляем файлы
    if not run_git_command("git add database.py telegram_bot.py"):
        return
    
    # Коммитим изменения
    commit_message = """Fix database file handling and improve /remove command

- Улучшена обработка файла sites.json в database.py
- Добавлена проверка на пустые и поврежденные файлы
- Создание резервных копий при повреждении
- Команда /remove теперь поддерживает URL и имя сайта
- Исправлена проблема с перезаписью sites.json при запуске"""
    
    if not run_git_command(f'git commit -m "{commit_message}"'):
        return
    
    # Пушим изменения
    if not run_git_command("git push origin master"):
        return
    
    print("\n🎉 Все изменения успешно отправлены в GitHub!")
    print("=" * 50)
    print("📋 Следующие шаги:")
    print("1. Обновите код на сервере: git pull origin master")
    print("2. Перезапустите контейнер: docker-compose restart")
    print("3. Протестируйте команду: /remove promineral.ru")

if __name__ == "__main__":
    main()
