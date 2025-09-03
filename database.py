"""
Модуль для работы с файловой базой данных сайтов
Обеспечивает CRUD операции для управления списком сайтов
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import config

class SitesDatabase:
    """
    Класс для работы с файловой базой данных сайтов
    Хранит информацию о сайтах в JSON файле
    """
    
    def __init__(self, db_file: str = None):
        """
        Инициализация базы данных
        
        Args:
            db_file (str): Путь к файлу базы данных
        """
        self.db_file = db_file or config.SITES_DATABASE_FILE
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Создает файл базы данных если он не существует"""
        if not os.path.exists(self.db_file):
            self._save_sites([])
    
    def _load_sites(self) -> List[Dict]:
        """
        Загружает список сайтов из файла
        
        Returns:
            List[Dict]: Список сайтов
        """
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_sites(self, sites: List[Dict]):
        """
        Сохраняет список сайтов в файл
        
        Args:
            sites (List[Dict]): Список сайтов для сохранения
        """
        with open(self.db_file, 'w', encoding='utf-8') as f:
            json.dump(sites, f, ensure_ascii=False, indent=2)
    
    def add_site(self, url: str, name: str = None, user_id: int = None) -> bool:
        """
        Добавляет новый сайт в базу данных
        
        Args:
            url (str): URL сайта для мониторинга
            name (str): Название сайта (опционально)
            user_id (int): ID пользователя, добавившего сайт
            
        Returns:
            bool: True если сайт добавлен успешно, False если уже существует
        """
        sites = self._load_sites()
        
        # Проверяем, не существует ли уже такой URL
        if any(site['url'] == url for site in sites):
            return False
        
        # Создаем новый сайт
        new_site = {
            'id': len(sites) + 1,
            'url': url,
            'name': name or url,
            'user_id': user_id,
            'added_at': datetime.now().isoformat(),
            'last_check': None,
            'last_status': None,
            'last_content_hash': None,
            'last_content': None,  # Сохраняем последний контент для сравнения
            'is_active': True,
            'check_count': 0,
            'error_count': 0
        }
        
        sites.append(new_site)
        self._save_sites(sites)
        return True
    
    def remove_site(self, site_id: int) -> bool:
        """
        Удаляет сайт из базы данных
        
        Args:
            site_id (int): ID сайта для удаления
            
        Returns:
            bool: True если сайт удален успешно, False если не найден
        """
        sites = self._load_sites()
        original_count = len(sites)
        
        # Удаляем сайт по ID
        sites = [site for site in sites if site['id'] != site_id]
        
        if len(sites) < original_count:
            # Пересчитываем ID для оставшихся сайтов
            for i, site in enumerate(sites):
                site['id'] = i + 1
            
            self._save_sites(sites)
            return True
        
        return False
    
    def get_all_sites(self) -> List[Dict]:
        """
        Получает список всех сайтов
        
        Returns:
            List[Dict]: Список всех сайтов
        """
        return self._load_sites()
    
    def get_active_sites(self) -> List[Dict]:
        """
        Получает список только активных сайтов
        
        Returns:
            List[Dict]: Список активных сайтов
        """
        sites = self._load_sites()
        return [site for site in sites if site.get('is_active', True)]
    
    def get_site_by_id(self, site_id: int) -> Optional[Dict]:
        """
        Получает сайт по ID
        
        Args:
            site_id (int): ID сайта
            
        Returns:
            Optional[Dict]: Данные сайта или None если не найден
        """
        sites = self._load_sites()
        for site in sites:
            if site['id'] == site_id:
                return site
        return None
    
    def update_site_status(self, site_id: int, status: str, content_hash: str = None, content: str = None, error_message: str = None):
        """
        Обновляет статус проверки сайта
        
        Args:
            site_id (int): ID сайта
            status (str): Статус проверки ('ok', 'error', 'changed')
            content_hash (str): Хеш содержимого страницы
            content (str): Содержимое страницы для сравнения
            error_message (str): Сообщение об ошибке
        """
        sites = self._load_sites()
        
        for site in sites:
            if site['id'] == site_id:
                site['last_check'] = datetime.now().isoformat()
                site['last_status'] = status
                site['check_count'] += 1
                
                if content_hash:
                    site['last_content_hash'] = content_hash
                
                if content:
                    site['last_content'] = content
                
                if status == 'error':
                    site['error_count'] += 1
                
                break
        
        self._save_sites(sites)
    
    def get_sites_by_user(self, user_id: int) -> List[Dict]:
        """
        Получает список сайтов, добавленных конкретным пользователем
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            List[Dict]: Список сайтов пользователя
        """
        sites = self._load_sites()
        return [site for site in sites if site.get('user_id') == user_id]
    
    def toggle_site_status(self, site_id: int) -> bool:
        """
        Переключает статус активности сайта
        
        Args:
            site_id (int): ID сайта
            
        Returns:
            bool: Новый статус активности
        """
        sites = self._load_sites()
        
        for site in sites:
            if site['id'] == site_id:
                site['is_active'] = not site.get('is_active', True)
                self._save_sites(sites)
                return site['is_active']
        
        return False
