#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных на сервере
Создает пустой файл sites.json если его нет
"""
import os
import json
import sys

def init_database():
    """
    Инициализирует базу данных сайтов
    """
    print("🔧 Инициализация базы данных...")
    
    # Путь к файлу базы данных
    db_file = "sites.json"
    
    # Проверяем, существует ли файл
    if os.path.exists(db_file):
        print(f"✅ Файл {db_file} уже существует")
        
        # Проверяем, что файл не пустой
        try:
            with open(db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    print(f"📊 В базе данных {len(data)} сайтов")
                    return True
                else:
                    print("⚠️  Файл пустой, инициализируем...")
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️  Ошибка чтения файла: {e}")
            print("🔄 Пересоздаем файл...")
    else:
        print(f"📝 Создаем новый файл {db_file}")
    
    # Создаем пустую базу данных
    empty_database = []
    
    try:
        with open(db_file, 'w', encoding='utf-8') as f:
            json.dump(empty_database, f, ensure_ascii=False, indent=2)
        
        print(f"✅ База данных {db_file} успешно инициализирована")
        print("💡 Теперь можно добавлять сайты через Telegram бота")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания файла: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\n🎯 Инициализация завершена успешно!")
    else:
        print("\n🚨 Ошибка инициализации!")
        sys.exit(1)
