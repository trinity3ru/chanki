"""
Тестовый скрипт для проверки основных функций приложения
Запускается без телеграм бота для отладки
"""
import json
from datetime import datetime
from database import SitesDatabase
from site_monitor import SiteMonitor

def test_database():
    """Тестирование базы данных"""
    print("🧪 Тестирование базы данных...")
    
    # Создаем экземпляр БД
    db = SitesDatabase("test_sites.json")
    
    # Тестируем добавление сайтов
    print("  📝 Добавляю тестовые сайты...")
    
    # Добавляем несколько тестовых сайтов
    test_sites = [
        ("https://google.com", "Google", 12345),
        ("https://yandex.ru", "Yandex", 12345),
        ("https://github.com", "GitHub", 67890)
    ]
    
    for url, name, user_id in test_sites:
        success = db.add_site(url, name, user_id)
        print(f"    {'✅' if success else '❌'} {name}: {url}")
    
    # Тестируем получение сайтов
    print("\n  📋 Получаю все сайты...")
    all_sites = db.get_all_sites()
    print(f"    Всего сайтов: {len(all_sites)}")
    
    for site in all_sites:
        print(f"    ID: {site['id']}, Название: {site['name']}, URL: {site['url']}")
    
    # Тестируем получение сайтов пользователя
    print("\n  👤 Получаю сайты пользователя 12345...")
    user_sites = db.get_sites_by_user(12345)
    print(f"    Сайтов у пользователя: {len(user_sites)}")
    
    # Тестируем обновление статуса
    print("\n  🔄 Обновляю статус сайта...")
    if all_sites:
        first_site = all_sites[0]
        db.update_site_status(first_site['id'], 'ok', 'test_hash_123')
        print(f"    Статус обновлен для: {first_site['name']}")
    
    # Тестируем удаление сайта
    print("\n  🗑️ Удаляю тестовый сайт...")
    if len(all_sites) > 1:
        site_to_remove = all_sites[1]
        success = db.remove_site(site_to_remove['id'])
        print(f"    {'✅' if success else '❌'} Удален: {site_to_remove['name']}")
    
    print("✅ Тестирование базы данных завершено\n")
    return db

def test_monitor(database):
    """Тестирование монитора сайтов"""
    print("🧪 Тестирование монитора сайтов...")
    
    # Создаем экземпляр монитора
    monitor = SiteMonitor(database)
    
    # Получаем активные сайты
    active_sites = database.get_active_sites()
    
    if not active_sites:
        print("  ⚠️ Нет активных сайтов для тестирования")
        return
    
    print(f"  🔍 Тестирую мониторинг {len(active_sites)} сайтов...")
    
    # Тестируем проверку одного сайта
    test_site = active_sites[0]
    print(f"    Проверяю: {test_site['name']} ({test_site['url']})")
    
    try:
        status, message, content_hash = monitor.check_site(test_site)
        print(f"      Статус: {status}")
        print(f"      Сообщение: {message}")
        print(f"      Хеш: {content_hash[:20] if content_hash else 'None'}...")
        
        # Показываем сводку по сайту
        summary = monitor.get_site_summary(test_site)
        print(f"      Сводка:\n{summary}")
        
    except Exception as e:
        print(f"      ❌ Ошибка при проверке: {str(e)}")
    
    print("✅ Тестирование монитора завершено\n")

def test_config():
    """Тестирование конфигурации"""
    print("🧪 Тестирование конфигурации...")
    
    try:
        import config
        print(f"  ⏰ Интервал проверки: {config.CHECK_INTERVAL_HOURS} часов")
        print(f"  ⏱️ Таймаут запроса: {config.REQUEST_TIMEOUT} секунд")
        print(f"  📏 Мин. длина контента: {config.MIN_CONTENT_LENGTH} символов")
        print(f"  🔐 Алгоритм хеширования: {config.CONTENT_HASH_ALGORITHM}")
        print(f"  📁 Файл БД: {config.SITES_DATABASE_FILE}")
        print(f"  📝 Файл логов: {config.LOG_FILE}")
        
        if config.TELEGRAM_BOT_TOKEN:
            print(f"  🤖 Токен бота: {'*' * 20}...")
        else:
            print("  ⚠️ Токен бота не найден")
            
        print("✅ Конфигурация загружена успешно\n")
        
    except Exception as e:
        print(f"  ❌ Ошибка загрузки конфигурации: {str(e)}\n")

def cleanup_test_files():
    """Очистка тестовых файлов"""
    import os
    
    test_files = ["test_sites.json"]
    
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️ Удален тестовый файл: {file}")

def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестирования приложения мониторинга сайтов")
    print("=" * 60)
    
    try:
        # Тестируем конфигурацию
        test_config()
        
        # Тестируем базу данных
        db = test_database()
        
        # Тестируем монитор
        test_monitor(db)
        
        print("🎉 Все тесты завершены успешно!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка при тестировании: {str(e)}")
        
    finally:
        # Очищаем тестовые файлы
        print("\n🧹 Очистка тестовых файлов...")
        cleanup_test_files()
        print("✅ Очистка завершена")

if __name__ == "__main__":
    main()

