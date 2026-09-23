"""
Тестовый скрипт для проверки основных функций приложения
Запускается без телеграм бота для отладки

Проверки базы данных и детекции изменений работают офлайн.
Проверка реального сайта требует доступа в интернет и делается последней.
"""
import asyncio
import json
import os
import shutil
import tempfile
from types import SimpleNamespace
import config
from database import SitesDatabase
from site_monitor import SiteMonitor

# Перепроверку упавшего сайта в тестах не ждем
config.ERROR_RETRY_DELAY_SECONDS = 0

USER_A = 12345
USER_B = 67890


def make_database(workdir: str) -> SitesDatabase:
    """
    Создает изолированную базу данных для тестов

    Args:
        workdir (str): Временная директория

    Returns:
        SitesDatabase: Экземпляр базы данных
    """
    return SitesDatabase(
        db_file=os.path.join(workdir, 'sites.json'),
        snapshots_dir=os.path.join(workdir, 'snapshots')
    )


def test_database(workdir: str) -> SitesDatabase:
    """Тестирование базы данных"""
    print("🧪 Тестирование базы данных...")

    db = make_database(workdir)

    # Добавление сайтов
    print("  📝 Добавляю тестовые сайты...")
    assert db.add_site("https://google.com", "Google", USER_A)
    assert db.add_site("https://yandex.ru", "Yandex", USER_A)
    assert db.add_site("https://github.com", "GitHub", USER_B)
    print("    ✅ Добавлено 3 сайта")

    # Дубликат в пределах пользователя запрещен
    assert not db.add_site("https://google.com", "Google снова", USER_A)
    print("    ✅ Повторный URL у того же пользователя отклонен")

    # Тот же URL у другого пользователя разрешен
    assert db.add_site("https://google.com", "Google", USER_B)
    print("    ✅ Тот же URL у другого пользователя принят")

    # Разделение по пользователям
    assert len(db.get_sites_by_user(USER_A)) == 2
    assert len(db.get_sites_by_user(USER_B)) == 2
    print("    ✅ Сайты разделены по пользователям")

    # Обновление статуса с текстом ошибки
    yandex = [s for s in db.get_sites_by_user(USER_A) if 'yandex' in s['url']][0]
    db.update_site_status(yandex['id'], 'error', error_message='HTTP ошибка: 503')
    yandex = db.get_site_by_id(yandex['id'])
    assert yandex['last_status'] == 'error'
    assert yandex['last_error'] == 'HTTP ошибка: 503'
    assert yandex['error_count'] == 1
    print("    ✅ Статус и причина ошибки сохранены")

    # Чужой сайт удалить нельзя
    github = db.get_sites_by_user(USER_B)[0]
    assert not db.remove_site(github['id'], USER_A)
    print("    ✅ Удаление чужого сайта отклонено")

    # ID остальных сайтов не должны сдвигаться после удаления
    ids_before = {s['id']: s['url'] for s in db.get_all_sites()}
    assert db.remove_site(yandex['id'], USER_A)
    ids_after = {s['id']: s['url'] for s in db.get_all_sites()}
    del ids_before[yandex['id']]
    assert ids_before == ids_after, f"ID сдвинулись: {ids_before} != {ids_after}"
    print("    ✅ ID оставшихся сайтов не изменились")

    # Новый сайт получает свежий ID, а не переиспользованный
    assert db.add_site("https://example.com", "Example", USER_A)
    new_id = max(s['id'] for s in db.get_all_sites())
    assert new_id not in ids_before
    print(f"    ✅ Новому сайту выдан свежий ID: {new_id}")

    print("✅ Тестирование базы данных завершено\n")
    return db


def test_snapshots(workdir: str):
    """Тестирование хранения снимков контента"""
    print("🧪 Тестирование снимков контента...")

    db = make_database(os.path.join(workdir, 'snap'))
    db.add_site("https://example.com", "Example", USER_A)
    site_id = db.get_all_sites()[0]['id']

    assert db.get_snapshot(site_id) == ''
    db.save_snapshot(site_id, "Текст страницы")
    assert db.get_snapshot(site_id) == "Текст страницы"
    print("    ✅ Снимок сохраняется и читается")

    # Контент не должен попадать в JSON базы
    with open(db.db_file, 'r', encoding='utf-8') as f:
        raw = f.read()
    assert "Текст страницы" not in raw
    print("    ✅ Текст страницы не хранится в sites.json")

    # Снимок удаляется вместе с сайтом
    db.remove_site(site_id, USER_A)
    assert not os.path.exists(db._snapshot_path(site_id))
    print("    ✅ Снимок удален вместе с сайтом")

    print("✅ Тестирование снимков завершено\n")


def test_migration(workdir: str):
    """Тестирование миграции со старого формата базы"""
    print("🧪 Тестирование миграции старого формата...")

    migration_dir = os.path.join(workdir, 'migration')
    os.makedirs(migration_dir, exist_ok=True)
    db_file = os.path.join(migration_dir, 'sites.json')

    old_format = [
        {'id': 1, 'url': 'https://a.ru', 'name': 'A', 'user_id': USER_A,
         'last_content': 'много текста' * 100, 'check_count': 5, 'error_count': 0},
        {'id': 2, 'url': 'https://b.ru', 'name': 'B', 'user_id': USER_A,
         'last_content': 'еще текста' * 100, 'check_count': 3, 'error_count': 1},
    ]
    with open(db_file, 'w', encoding='utf-8') as f:
        json.dump(old_format, f, ensure_ascii=False)

    db = SitesDatabase(db_file=db_file, snapshots_dir=os.path.join(migration_dir, 'snapshots'))
    sites = db.get_all_sites()

    assert len(sites) == 2
    assert all('last_content' not in s for s in sites)
    print("    ✅ Старые записи прочитаны, last_content выброшен")

    # Следующий ID продолжает нумерацию, а не начинает заново
    db.add_site("https://c.ru", "C", USER_A)
    assert max(s['id'] for s in db.get_all_sites()) == 3
    print("    ✅ Нумерация ID продолжена корректно")

    print("✅ Тестирование миграции завершено\n")


def test_change_detection(workdir: str):
    """Тестирование логики детекции изменений (без сети)"""
    print("🧪 Тестирование детекции изменений...")

    db = make_database(os.path.join(workdir, 'detect'))
    monitor = SiteMonitor(db)

    base = "Обычный текст главной страницы. " * 50

    # Идентичный контент
    significant, description = monitor._is_significant_change(base, base)
    assert not significant, description
    print(f"    ✅ Идентичный контент: {description}")

    # Полная замена контента
    significant, description = monitor._is_significant_change(base, "Совсем другой текст " * 50)
    assert significant, description
    print(f"    ✅ Полная замена: {description}")

    # Пустой старый снимок считается изменением
    significant, _ = monitor._is_significant_change("", base)
    assert significant
    print("    ✅ Отсутствие старого снимка считается изменением")

    print("✅ Тестирование детекции завершено\n")


class FakeResponse:
    """Подставной HTTP-ответ, чтобы проверять check_site без сети"""

    def __init__(self, text: str, status_code: int = 200):
        self.text = text
        self.status_code = status_code


def test_js_site(workdir: str):
    """Тестирование сайтов, которые рисуют текст через JavaScript (без сети)"""
    print("🧪 Тестирование JS-сайтов...")

    db = make_database(os.path.join(workdir, 'js'))
    monitor = SiteMonitor(db)
    db.add_site("https://spa.example", "SPA", USER_A)
    site = db.get_all_sites()[0]

    padding = "<!-- " + "x" * 200 + " -->"

    # SPA: текста нет, но есть скрипты - сайт доступен
    spa_html = (f"<html><head><title>SPA</title></head><body>{padding}"
                "<div id=\"app\"></div><script src=\"bundle.js\"></script></body></html>")
    monitor.session.get = lambda *args, **kwargs: FakeResponse(spa_html)

    status, message, content_hash = monitor.check_site(site)
    assert status == 'ok', message
    assert content_hash is None
    saved = db.get_site_by_id(site['id'])
    assert saved['last_status'] == 'ok' and saved['last_error'] is None
    assert saved['last_content_hash'] is None and db.get_snapshot(site['id']) == ''
    print(f"    ✅ SPA считается доступной: {message}")

    # Пустая страница без скриптов - по-прежнему ошибка
    empty_html = f"<html><head><title>Пусто</title></head><body>{padding}</body></html>"
    monitor.session.get = lambda *args, **kwargs: FakeResponse(empty_html)

    status, message, _ = monitor.check_site(site)
    assert status == 'error', message
    print(f"    ✅ Пустая страница без скриптов - ошибка: {message}")

    print("✅ Тестирование JS-сайтов завершено\n")


def test_retry(workdir: str):
    """Тестирование перепроверки перед объявлением ошибки (без сети)"""
    print("🧪 Тестирование перепроверки...")

    db = make_database(os.path.join(workdir, 'retry'))
    monitor = SiteMonitor(db)
    db.add_site("https://flaky.example", "Flaky", USER_A)
    site = db.get_all_sites()[0]

    page = "<html><body>" + "Нормальный текст страницы. " * 10 + "</body></html>"

    # Первый запрос падает, второй успешен - ошибки нет и она не посчитана
    responses = [FakeResponse('', 502), FakeResponse(page)]
    monitor.session.get = lambda *args, **kwargs: responses.pop(0)

    status, message, _ = monitor.check_site(site)
    assert status == 'ok', message
    assert not responses
    assert db.get_site_by_id(site['id'])['error_count'] == 0
    print("    ✅ Разовый сбой не считается ошибкой")

    # Оба запроса падают - ошибка записана один раз
    responses = [FakeResponse('', 502), FakeResponse('', 503)]
    status, message, _ = monitor.check_site(site)
    assert status == 'error' and message == "HTTP ошибка: 503", message
    assert db.get_site_by_id(site['id'])['error_count'] == 1
    print(f"    ✅ Повторный сбой - ошибка: {message}")

    print("✅ Тестирование перепроверки завершено\n")


def test_notifications():
    """Тестирование уведомлений только о смене состояния (без сети)"""
    print("🧪 Тестирование уведомлений по событиям...")

    from scheduler import MonitoringScheduler

    stub_bot = SimpleNamespace(database=None, monitor=None)
    scheduler = MonitoringScheduler(stub_bot)

    def entry(name, previous_status, message='сообщение', user_id=USER_A):
        site = {'name': name, 'user_id': user_id, 'last_status': previous_status}
        return {'site': site, 'message': message, 'content_hash': None}

    results = {
        'ok': [entry('Стабильный', 'ok'), entry('Поднялся', 'error'),
               entry('Новый', None), entry('Мелкие правки', 'minor_change')],
        'error': [entry('Упал', 'ok', 'HTTP ошибка: 500'), entry('Лежит', 'error'),
                  entry('Новый битый', None, 'Таймаут')],
        'changed': [entry('Обновился', 'ok', 'Значительные изменения'),
                    entry('Чужой', 'ok', user_id=USER_B)],
    }

    sent = []

    async def send_message(chat_id, text):
        sent.append((chat_id, text))

    context = SimpleNamespace(bot=SimpleNamespace(send_message=send_message))
    asyncio.run(scheduler._send_notifications(context, results))

    by_user = dict(sent)
    assert set(by_user) == {USER_A, USER_B}, sent
    text = by_user[USER_A]
    for name in ('Упал', 'Новый битый', 'Поднялся', 'Обновился'):
        assert name in text, f"нет события '{name}':\n{text}"
    for name in ('Стабильный', 'Лежит', 'Новый\n', 'Мелкие правки', 'Чужой'):
        assert name not in text, f"лишнее упоминание '{name}':\n{text}"
    print("    ✅ В уведомлении только упавшие, поднявшиеся и изменившиеся сайты")

    # Пользователь без событий уведомления не получает
    sent.clear()
    quiet = {'ok': [entry('Стабильный', 'ok')], 'error': [entry('Лежит', 'error')], 'changed': []}
    asyncio.run(scheduler._send_notifications(context, quiet))
    assert not sent, sent
    print("    ✅ Без событий уведомление не отправляется")

    print("✅ Тестирование уведомлений завершено\n")


def test_config():
    """Тестирование конфигурации"""
    print("🧪 Тестирование конфигурации...")

    import config
    print(f"  ⏰ Интервал проверки: {config.CHECK_INTERVAL_HOURS} часов")
    print(f"  ⏱️ Таймаут запроса: {config.REQUEST_TIMEOUT} секунд")
    print(f"  🚦 Первая проверка через: {config.FIRST_CHECK_DELAY_SECONDS} секунд")
    print(f"  📏 Мин. длина контента: {config.MIN_CONTENT_LENGTH} символов")
    print(f"  📁 Файл БД: {config.SITES_DATABASE_FILE}")
    print(f"  📸 Снимки: {config.SNAPSHOTS_DIR}")
    print(f"  📝 Файл логов: {config.LOG_FILE}")

    if config.TELEGRAM_BOT_TOKEN:
        print(f"  🤖 Токен бота: {'*' * 20}...")
    else:
        print("  ⚠️ Токен бота не найден")

    print("✅ Конфигурация загружена успешно\n")


def test_live_check(database: SitesDatabase):
    """Проверка реального сайта (требует интернет)"""
    print("🧪 Проверка реального сайта (нужен интернет)...")

    monitor = SiteMonitor(database)
    active_sites = database.get_active_sites()

    if not active_sites:
        print("  ⚠️ Нет активных сайтов для проверки\n")
        return

    test_site = active_sites[0]
    print(f"    Проверяю: {test_site['name']} ({test_site['url']})")

    try:
        status, message, content_hash = monitor.check_site(test_site)
        print(f"      Статус: {status}")
        print(f"      Сообщение: {message}")
        print(f"      Хеш: {content_hash[:20] if content_hash else 'None'}...")

        summary = monitor.get_site_summary(database.get_site_by_id(test_site['id']))
        print(f"      Сводка:\n{summary}")
    except Exception as e:
        print(f"      ❌ Ошибка при проверке: {str(e)}")

    print("✅ Проверка реального сайта завершена\n")


def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестирования приложения мониторинга сайтов")
    print("=" * 60)

    workdir = tempfile.mkdtemp(prefix='chanki-test-')
    print(f"📂 Временная директория: {workdir}\n")

    try:
        test_config()
        db = test_database(workdir)
        test_snapshots(workdir)
        test_migration(workdir)
        test_change_detection(workdir)
        test_js_site(workdir)
        test_retry(workdir)
        test_notifications()
        test_live_check(db)

        print("🎉 Все тесты завершены успешно!")

    except AssertionError as e:
        print(f"❌ Проверка не прошла: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Критическая ошибка при тестировании: {str(e)}")
        raise
    finally:
        print("\n🧹 Очистка временных файлов...")
        shutil.rmtree(workdir, ignore_errors=True)
        print("✅ Очистка завершена")


if __name__ == "__main__":
    main()
