#!/usr/bin/env python3
"""
Быстрый коммит изменений
"""

import subprocess
import sys

def run_command(command):
    """Выполняет команду"""
    print(f"🔄 Выполняю: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Успешно")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print(f"❌ Ошибка: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def main():
    print("🚀 Быстрый коммит изменений...")
    print("=" * 50)
    
    # Добавляем все файлы
    if not run_command("git add ."):
        return
    
    # Коммитим
    if not run_command('git commit -m "Fix database file handling - prevent sites.json from being overwritten"'):
        return
    
    # Пушим
    if not run_command("git push origin master"):
        return
    
    print("\n🎉 Все изменения отправлены в GitHub!")
    print("=" * 50)
    print("📋 Теперь на сервере выполните:")
    print("git pull origin master")
    print("docker-compose restart")

if __name__ == "__main__":
    main()
