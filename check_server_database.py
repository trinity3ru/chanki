#!/usr/bin/env python3
"""
Скрипт для проверки версии database.py на сервере
"""

def main():
    print("🔍 Проверка database.py на сервере")
    print("=" * 60)
    print()
    
    print("📋 Команды для выполнения на сервере:")
    print("=" * 60)
    print()
    
    print("1. Проверьте содержимое файла database.py:")
    print("   docker exec site-monitor-bot cat /app/database.py | head -50")
    print()
    
    print("2. Проверьте метод _load_sites:")
    print("   docker exec site-monitor-bot grep -A 20 '_load_sites' /app/database.py")
    print()
    
    print("3. Проверьте метод _ensure_database_exists:")
    print("   docker exec site-monitor-bot grep -A 10 '_ensure_database_exists' /app/database.py")
    print()
    
    print("4. Проверьте, есть ли проверка на пустые файлы:")
    print("   docker exec site-monitor-bot grep -n 'getsize' /app/database.py")
    print()
    
    print("5. Проверьте, есть ли создание резервных копий:")
    print("   docker exec site-monitor-bot grep -n 'backup' /app/database.py")
    print()
    
    print("6. Проверьте версию файла (дату изменения):")
    print("   docker exec site-monitor-bot ls -la /app/database.py")
    print()
    
    print("=" * 60)
    print("🎯 Что искать в новой версии:")
    print("=" * 60)
    print()
    print("✅ В методе _load_sites должна быть строка:")
    print("   if not os.path.exists(self.db_file) or os.path.getsize(self.db_file) == 0:")
    print()
    print("✅ В методе _ensure_database_exists должна быть строка:")
    print("   elif os.path.getsize(self.db_file) == 0:")
    print()
    print("✅ Должна быть строка с backup:")
    print("   backup_file = f\"{self.db_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}\"")
    print()
    print("=" * 60)
    print("🚨 Если этих строк НЕТ - значит на сервере старая версия!")
    print("   Нужно обновить код через git pull origin master")
    print()

if __name__ == "__main__":
    main()
