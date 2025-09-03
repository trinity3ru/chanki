#!/usr/bin/env python3
"""
Простой скрипт для проверки статуса Git
"""

import subprocess
import os

def run_command(command):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🔍 Проверка статуса Git...")
    print("=" * 50)
    
    # Проверяем статус
    success, stdout, stderr = run_command("git status --porcelain")
    if success:
        if stdout.strip():
            print("📝 Измененные файлы:")
            print(stdout)
        else:
            print("✅ Нет изменений для коммита")
            return
    
    # Показываем статус
    success, stdout, stderr = run_command("git status")
    if success:
        print("\n📋 Полный статус:")
        print(stdout)
    else:
        print(f"❌ Ошибка: {stderr}")
        return
    
    print("\n" + "=" * 50)
    print("💡 Для коммита выполните:")
    print("git add .")
    print('git commit -m "Fix database and remove command"')
    print("git push origin master")

if __name__ == "__main__":
    main()
