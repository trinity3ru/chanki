"""
Модуль для работы с файловой базой данных сайтов
Обеспечивает CRUD операции для управления списком сайтов

Метаданные сайтов хранятся в JSON файле, снимки контента - отдельными
файлами в SNAPSHOTS_DIR, чтобы JSON не разрастался на мегабайты.
"""
import json
import os
import tempfile
import threading
from datetime import datetime
from typing import List, Dict, Optional
import config

# Пустое состояние базы: next_id никогда не переиспользуется,
# поэтому ID сайта стабилен на всю его жизнь
EMPTY_STATE = {'next_id': 1, 'sites': []}


def _atomic_write(path: str, text: str):
    """
    Атомарно записывает текст в файл

    Пишем во временный файл в той же директории и подменяем цель через
    os.replace - так файл никогда не остается наполовину записанным.

    Args:
        path (str): Путь к целевому файлу
        text (str): Содержимое для записи
    """
    directory = os.path.dirname(path) or '.'
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix='.tmp')

    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


class SitesDatabase:
    """
    Класс для работы с файловой базой данных сайтов
    Хранит информацию о сайтах в JSON файле
    """

    def __init__(self, db_file: str = None, snapshots_dir: str = None):
        """
        Инициализация базы данных

        Args:
            db_file (str): Путь к файлу базы данных
            snapshots_dir (str): Директория для снимков контента
        """
        self.db_file = db_file or config.SITES_DATABASE_FILE
        self.snapshots_dir = snapshots_dir or config.SNAPSHOTS_DIR

        # Проверки сайтов выполняются в рабочих потоках, поэтому цикл
        # "прочитать файл - изменить - записать" защищаем блокировкой
        self._lock = threading.RLock()

        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        """Создает директории и файл базы данных если их нет"""
        db_dir = os.path.dirname(self.db_file)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        os.makedirs(self.snapshots_dir, exist_ok=True)

        if not os.path.exists(self.db_file):
            self._save_state(dict(EMPTY_STATE, sites=[]))

    def _load_state(self) -> Dict:
        """
        Загружает состояние базы из файла

        Returns:
            Dict: Состояние вида {'next_id': int, 'sites': [...]}
        """
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return dict(EMPTY_STATE, sites=[])

        # Миграция со старого формата, где файл был плоским списком сайтов
        # и хранил полный текст страницы в поле last_content
        if isinstance(data, list):
            for site in data:
                site.pop('last_content', None)
                site.setdefault('last_error', None)
            next_id = max((site['id'] for site in data), default=0) + 1
            state = {'next_id': next_id, 'sites': data}
            self._save_state(state)
            return state

        return data

    def _save_state(self, state: Dict):
        """
        Сохраняет состояние базы в файл

        Args:
            state (Dict): Состояние для сохранения
        """
        _atomic_write(self.db_file, json.dumps(state, ensure_ascii=False, indent=2))

    def add_site(self, url: str, name: str = None, user_id: int = None) -> bool:
        """
        Добавляет новый сайт в базу данных

        Args:
            url (str): URL сайта для мониторинга
            name (str): Название сайта (опционально)
            user_id (int): ID пользователя, добавившего сайт

        Returns:
            bool: True если сайт добавлен успешно, False если этот
                  пользователь уже добавил такой URL
        """
        with self._lock:
            state = self._load_state()

            # Один и тот же URL могут мониторить разные пользователи,
            # поэтому дубликат ищем в пределах пользователя
            if any(site['url'] == url and site.get('user_id') == user_id
                   for site in state['sites']):
                return False

            site_id = state['next_id']
            state['next_id'] = site_id + 1

            state['sites'].append({
                'id': site_id,
                'url': url,
                'name': name or url,
                'user_id': user_id,
                'added_at': datetime.now().isoformat(),
                'last_check': None,
                'last_status': None,
                'last_content_hash': None,
                'last_error': None,
                'is_active': True,
                'check_count': 0,
                'error_count': 0
            })

            self._save_state(state)
            return True

    def remove_site(self, site_id: int, user_id: int) -> bool:
        """
        Удаляет сайт пользователя из базы данных

        ID оставшихся сайтов не пересчитываются: они должны оставаться
        стабильными, иначе выданный ранее /list начинает врать.

        Args:
            site_id (int): ID сайта для удаления
            user_id (int): ID пользователя-владельца

        Returns:
            bool: True если сайт удален, False если не найден или чужой
        """
        with self._lock:
            state = self._load_state()

            remaining = [site for site in state['sites']
                         if not (site['id'] == site_id and site.get('user_id') == user_id)]

            if len(remaining) == len(state['sites']):
                return False

            state['sites'] = remaining
            self._save_state(state)

        self.delete_snapshot(site_id)
        return True

    def get_all_sites(self) -> List[Dict]:
        """
        Получает список всех сайтов

        Returns:
            List[Dict]: Список всех сайтов
        """
        with self._lock:
            return self._load_state()['sites']

    def get_active_sites(self) -> List[Dict]:
        """
        Получает список только активных сайтов

        Returns:
            List[Dict]: Список активных сайтов
        """
        return [site for site in self.get_all_sites() if site.get('is_active', True)]

    def get_site_by_id(self, site_id: int) -> Optional[Dict]:
        """
        Получает сайт по ID

        Args:
            site_id (int): ID сайта

        Returns:
            Optional[Dict]: Данные сайта или None если не найден
        """
        for site in self.get_all_sites():
            if site['id'] == site_id:
                return site
        return None

    def get_sites_by_user(self, user_id: int) -> List[Dict]:
        """
        Получает список сайтов, добавленных конкретным пользователем

        Args:
            user_id (int): ID пользователя

        Returns:
            List[Dict]: Список сайтов пользователя
        """
        return [site for site in self.get_all_sites() if site.get('user_id') == user_id]

    def update_site_status(self, site_id: int, status: str, content_hash: str = None,
                           error_message: str = None):
        """
        Обновляет статус проверки сайта

        Args:
            site_id (int): ID сайта
            status (str): Статус проверки ('ok', 'error', 'changed', 'minor_change')
            content_hash (str): Хеш содержимого страницы
            error_message (str): Сообщение об ошибке
        """
        with self._lock:
            state = self._load_state()

            for site in state['sites']:
                if site['id'] == site_id:
                    site['last_check'] = datetime.now().isoformat()
                    site['last_status'] = status
                    site['check_count'] = site.get('check_count', 0) + 1
                    site['last_error'] = error_message

                    if content_hash:
                        site['last_content_hash'] = content_hash

                    if status == 'error':
                        site['error_count'] = site.get('error_count', 0) + 1

                    break

            self._save_state(state)

    def _snapshot_path(self, site_id: int) -> str:
        """
        Возвращает путь к файлу снимка контента сайта

        Args:
            site_id (int): ID сайта

        Returns:
            str: Путь к файлу снимка
        """
        return os.path.join(self.snapshots_dir, f'{site_id}.txt')

    def get_snapshot(self, site_id: int) -> str:
        """
        Читает последний сохраненный текст страницы

        Args:
            site_id (int): ID сайта

        Returns:
            str: Текст страницы или пустая строка если снимка нет
        """
        try:
            with open(self._snapshot_path(site_id), 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ''

    def save_snapshot(self, site_id: int, content: str):
        """
        Сохраняет текст страницы для последующего сравнения

        Args:
            site_id (int): ID сайта
            content (str): Очищенный текст страницы
        """
        _atomic_write(self._snapshot_path(site_id), content)

    def delete_snapshot(self, site_id: int):
        """
        Удаляет снимок контента сайта

        Args:
            site_id (int): ID сайта
        """
        try:
            os.remove(self._snapshot_path(site_id))
        except FileNotFoundError:
            pass
