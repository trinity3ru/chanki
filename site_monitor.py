"""
Модуль для мониторинга сайтов
Проверяет доступность сайтов и детектирует изменения в контенте
"""
import hashlib
import requests
import time
from typing import Dict, Tuple, Optional
from bs4 import BeautifulSoup
import config
from database import SitesDatabase

class SiteMonitor:
    """
    Класс для мониторинга сайтов
    Проверяет доступность и детектирует изменения в контенте
    """
    
    def __init__(self, database: SitesDatabase):
        """
        Инициализация монитора сайтов
        
        Args:
            database (SitesDatabase): Экземпляр базы данных сайтов
        """
        self.database = database
        self.session = requests.Session()
        
        # Настройка User-Agent для более надежных запросов
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def check_site(self, site: Dict) -> Tuple[str, str, Optional[str]]:
        """
        Проверяет один сайт на доступность и изменения
        
        Args:
            site (Dict): Данные сайта из базы данных
            
        Returns:
            Tuple[str, str, Optional[str]]: (статус, сообщение, хеш_контента)
            Статус может быть: 'ok', 'error', 'changed'
        """
        url = site['url']
        site_id = site['id']
        
        try:
            # Выполняем HTTP запрос с таймаутом
            response = self.session.get(
                url, 
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            
            # Проверяем HTTP статус код
            if response.status_code != 200:
                error_msg = f"HTTP ошибка: {response.status_code}"
                self.database.update_site_status(site_id, 'error', error_message=error_msg)
                return 'error', error_msg, None
            
            # Получаем содержимое страницы
            content = response.text
            
            # Проверяем минимальную длину контента
            if len(content) < config.MIN_CONTENT_LENGTH:
                error_msg = f"Слишком короткий контент: {len(content)} символов"
                self.database.update_site_status(site_id, 'error', error_message=error_msg)
                return 'error', error_msg, None
            
            # Извлекаем основной контент (убираем HTML теги)
            soup = BeautifulSoup(content, 'html.parser')
            
            # Убираем скрипты, стили и другие технические элементы
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Получаем чистый текст
            clean_text = soup.get_text()
            
            # Убираем лишние пробелы и переносы строк
            clean_text = ' '.join(clean_text.split())
            
            # Проверяем минимальную длину очищенного текста
            if len(clean_text) < config.MIN_CONTENT_LENGTH:
                error_msg = f"Слишком мало текстового контента: {len(clean_text)} символов"
                self.database.update_site_status(site_id, 'error', error_message=error_msg)
                return 'error', error_msg, None
            
            # Вычисляем хеш контента
            content_hash = hashlib.sha256(clean_text.encode('utf-8')).hexdigest()
            
            # Проверяем, изменился ли контент
            last_hash = site.get('last_content_hash')
            
            if last_hash is None:
                # Первая проверка - просто сохраняем хеш
                self.database.update_site_status(site_id, 'ok', content_hash)
                return 'ok', 'Сайт доступен, контент сохранен', content_hash
            
            elif last_hash != content_hash:
                # Контент изменился
                self.database.update_site_status(site_id, 'changed', content_hash)
                return 'changed', 'Сайт доступен, но контент изменился', content_hash
            
            else:
                # Контент не изменился
                self.database.update_site_status(site_id, 'ok', content_hash)
                return 'ok', 'Сайт доступен, контент не изменился', content_hash
                
        except requests.exceptions.Timeout:
            error_msg = f"Таймаут запроса (>{config.REQUEST_TIMEOUT}с)"
            self.database.update_site_status(site_id, 'error', error_message=error_msg)
            return 'error', error_msg, None
            
        except requests.exceptions.ConnectionError:
            error_msg = "Ошибка подключения к сайту"
            self.database.update_site_status(site_id, 'error', error_message=error_msg)
            return 'error', error_msg, None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Ошибка запроса: {str(e)}"
            self.database.update_site_status(site_id, 'error', error_message=error_msg)
            return 'error', error_msg, None
            
        except Exception as e:
            error_msg = f"Неожиданная ошибка: {str(e)}"
            self.database.update_site_status(site_id, 'error', error_message=error_msg)
            return 'error', error_msg, None
    
    def check_all_sites(self) -> Dict[str, list]:
        """
        Проверяет все активные сайты
        
        Returns:
            Dict[str, list]: Результаты проверки по категориям
        """
        active_sites = self.database.get_active_sites()
        results = {
            'ok': [],
            'error': [],
            'changed': []
        }
        
        print(f"Начинаю проверку {len(active_sites)} сайтов...")
        
        for site in active_sites:
            print(f"Проверяю {site['name']} ({site['url']})...")
            
            status, message, content_hash = self.check_site(site)
            results[status].append({
                'site': site,
                'message': message,
                'content_hash': content_hash
            })
            
            # Небольшая пауза между запросами чтобы не перегружать серверы
            time.sleep(1)
        
        print(f"Проверка завершена. Результаты: OK={len(results['ok'])}, Errors={len(results['error'])}, Changed={len(results['changed'])}")
        
        return results
    
    def get_site_summary(self, site: Dict) -> str:
        """
        Формирует краткую сводку по сайту для уведомлений
        
        Args:
            site (Dict): Данные сайта
            
        Returns:
            str: Текст сводки
        """
        name = site['name']
        url = site['url']
        last_check = site.get('last_check')
        last_status = site.get('last_status')
        check_count = site.get('check_count', 0)
        error_count = site.get('error_count', 0)
        
        summary = f"🌐 {name}\n"
        summary += f"🔗 {url}\n"
        summary += f"📊 Проверок: {check_count}\n"
        summary += f"❌ Ошибок: {error_count}\n"
        
        if last_check:
            summary += f"🕐 Последняя проверка: {last_check[:19]}\n"
        
        if last_status:
            status_emoji = {
                'ok': '✅',
                'error': '❌',
                'changed': '🔄'
            }
            summary += f"📈 Статус: {status_emoji.get(last_status, '❓')} {last_status}\n"
        
        return summary
