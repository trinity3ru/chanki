"""
Модуль для мониторинга сайтов
Проверяет доступность сайтов и детектирует изменения в контенте
"""
import hashlib
import requests
import time
from typing import Dict, Tuple, Optional
from bs4 import BeautifulSoup
import difflib
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
    
    def _decode_response_content(self, response) -> str:
        """
        Правильно декодирует содержимое HTTP ответа с учетом кодировки
        
        Args:
            response: HTTP ответ от requests
            
        Returns:
            str: Декодированное содержимое страницы
        """
        # Получаем сырые байты
        content = response.content
        
        # Определяем кодировку
        encoding = response.encoding
        if not encoding:
            # Если кодировка не указана, пытаемся определить из HTML
            import re
            try:
                # Пробуем декодировать как UTF-8 для поиска charset
                temp_content = content.decode('utf-8', errors='ignore')
                charset_match = re.search(r'charset=([^"\'>\s]+)', temp_content, re.IGNORECASE)
                if charset_match:
                    encoding = charset_match.group(1).lower()
                    # Нормализуем названия кодировок
                    if encoding in ['windows-1251', 'cp1251']:
                        encoding = 'windows-1251'
                    elif encoding in ['utf-8', 'utf8']:
                        encoding = 'utf-8'
                    elif encoding in ['iso-8859-1', 'latin1']:
                        encoding = 'latin-1'
                else:
                    encoding = 'utf-8'  # По умолчанию UTF-8
            except:
                encoding = 'utf-8'
        
        # Декодируем контент с правильной кодировкой
        try:
            return content.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Если не удалось декодировать, пробуем UTF-8
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                # В крайнем случае используем latin-1 (никогда не падает)
                return content.decode('latin-1', errors='replace')
    
    def check_site(self, site: Dict) -> Tuple[str, str, Optional[str]]:
        """
        Проверяет один сайт на доступность и изменения
        Использует механизм повторных попыток для уменьшения ложных ошибок
        
        Args:
            site (Dict): Данные сайта из базы данных
            
        Returns:
            Tuple[str, str, Optional[str]]: (статус, сообщение, хеш_контента)
            Статус может быть: 'ok', 'error', 'changed'
        """
        url = site['url']
        site_id = site['id']
        
        # Механизм повторных попыток для уменьшения ложных срабатываний
        last_exception = None
        response = None
        
        for attempt in range(config.MAX_RETRIES):
            try:
                # Выполняем HTTP запрос с таймаутом
                response = self.session.get(
                    url, 
                    timeout=config.REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                
                # Проверяем HTTP статус код
                # Принимаем успешными коды 2xx и 3xx (редиректы)
                if 200 <= response.status_code < 400:
                    # Успешный ответ - обрабатываем содержимое
                    # Сбрасываем счетчик последовательных ошибок при успешной проверке
                    self._reset_consecutive_errors(site_id)
                    
                    # Получаем содержимое страницы с правильной кодировкой
                    content = self._decode_response_content(response)
            
                    # Проверяем минимальную длину сырого контента (до очистки)
                    if len(content) < config.MIN_CONTENT_LENGTH:
                        # Не считаем это фатальной ошибкой: продолжаем, но пометим предупреждение в сообщении
                        # Основное решение по уведомлениям будет применено на уровне scheduler
                        pass
                    
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
                    is_small_content = len(clean_text) < config.MIN_CONTENT_LENGTH
                    
                    # Вычисляем хеш контента
                    content_hash = hashlib.sha256(clean_text.encode('utf-8')).hexdigest()
                    
                    # Проверяем, изменился ли контент
                    last_hash = site.get('last_content_hash')
                    last_content = site.get('last_content', '')
                    
                    if last_hash is None:
                        # Первая проверка - просто сохраняем хеш и контент
                        self.database.update_site_status(site_id, 'ok', content_hash, clean_text)
                        return 'ok', 'Сайт доступен, контент сохранен', content_hash
                    
                    elif last_hash != content_hash:
                        # Контент изменился - проверяем значительность изменений
                        is_significant, change_description = self._is_significant_change(last_content, clean_text)
                        
                        if is_significant:
                            # Значительные изменения - обновляем хеш и контент, отправляем уведомление
                            self.database.update_site_status(site_id, 'changed', content_hash, clean_text)
                            return 'changed', f'Сайт доступен: {change_description}', content_hash
                        else:
                            # Незначительные изменения - НЕ обновляем хеш, НЕ отправляем уведомление
                            self.database.update_site_status(site_id, 'minor_change', last_hash, last_content)
                            return 'ok', f'Сайт доступен: {change_description}', last_hash
                    
                    else:
                        # Контент не изменился
                        # Если контента мало, но хеш не меняется — считаем "ok" без уведомления
                        self.database.update_site_status(site_id, 'ok', content_hash, clean_text)
                        if is_small_content:
                            return 'ok', f'Сайт доступен, мало контента: {len(clean_text)} символов (хеш без изменений)', content_hash
                        return 'ok', 'Сайт доступен, контент не изменился', content_hash
                    
                    else:
                        # HTTP ошибка (4xx, 5xx) - пробуем повторить (может быть временная проблема)
                        error_msg = f"HTTP ошибка: {response.status_code}"
                        last_exception = requests.exceptions.HTTPError(error_msg)
                        if attempt < config.MAX_RETRIES - 1:
                            time.sleep(config.RETRY_DELAY)
                            continue
                        else:
                            # Все попытки исчерпаны
                            if self._should_report_error(site):
                                self.database.update_site_status(site_id, 'error', error_message=error_msg)
                                return 'error', error_msg, None
                            else:
                                return 'ok', f'Временная проблема: {error_msg}', None
            
            except requests.exceptions.Timeout as e:
                # Таймаут - часто временная проблема, повторяем попытку
                last_exception = e
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY)
                    continue
                else:
                    # Все попытки исчерпаны
                    error_msg = f"Таймаут запроса (>{config.REQUEST_TIMEOUT}с) после {config.MAX_RETRIES} попыток"
                    # Проверяем последовательные ошибки перед установкой статуса error
                    if self._should_report_error(site):
                        self.database.update_site_status(site_id, 'error', error_message=error_msg)
                        return 'error', error_msg, None
                    else:
                        # Временная ошибка, не отправляем уведомление
                        return 'ok', f'Временная проблема: {error_msg}', None
            
            except requests.exceptions.ConnectionError as e:
                # Ошибка подключения - часто временная проблема (DNS, сеть), повторяем попытку
                last_exception = e
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY)
                    continue
                else:
                    # Все попытки исчерпаны
                    error_msg = "Ошибка подключения к сайту"
                    # Проверяем последовательные ошибки перед установкой статуса error
                    if self._should_report_error(site):
                        self.database.update_site_status(site_id, 'error', error_message=error_msg)
                        return 'error', error_msg, None
                    else:
                        # Временная ошибка, не отправляем уведомление
                        return 'ok', f'Временная проблема: {error_msg}', None
            
            except requests.exceptions.RequestException as e:
                # Другие ошибки запроса - повторяем попытку
                last_exception = e
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY)
                    continue
                else:
                    # Все попытки исчерпаны
                    error_msg = f"Ошибка запроса: {str(e)}"
                    if self._should_report_error(site):
                        self.database.update_site_status(site_id, 'error', error_message=error_msg)
                        return 'error', error_msg, None
                    else:
                        return 'ok', f'Временная проблема: {error_msg}', None
            
            except Exception as e:
                # Неожиданные ошибки - не повторяем, сразу сообщаем
                error_msg = f"Неожиданная ошибка: {str(e)}"
                self.database.update_site_status(site_id, 'error', error_message=error_msg)
                return 'error', error_msg, None
        
        # Если все попытки не удались, но мы дошли до этого места - возвращаем последнюю ошибку
        if last_exception:
            error_msg = f"Ошибка после {config.MAX_RETRIES} попыток: {str(last_exception)}"
            if self._should_report_error(site):
                self.database.update_site_status(site_id, 'error', error_message=error_msg)
                return 'error', error_msg, None
            else:
                return 'ok', f'Временная проблема: {error_msg}', None
    
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
    
    def _is_significant_change(self, old_content: str, new_content: str) -> Tuple[bool, str]:
        """
        Определяет, является ли изменение контента значительным
        
        Args:
            old_content (str): Старый контент
            new_content (str): Новый контент
            
        Returns:
            Tuple[bool, str]: (является_ли_значительным, описание_изменений)
        """
        if not old_content or not new_content:
            return True, "Контент полностью изменился"
        
        # 1. Проверяем изменение длины контента
        old_len = len(old_content)
        new_len = len(new_content)
        length_change_ratio = abs(new_len - old_len) / max(old_len, 1)
        
        if length_change_ratio > config.MAX_LENGTH_CHANGE_RATIO:
            percentage = length_change_ratio * 100
            return True, f"Значительное изменение длины контента: {percentage:.1f}%"
        
        # 2. Вычисляем процент различий между текстами
        differ = difflib.SequenceMatcher(None, old_content, new_content)
        similarity_ratio = differ.ratio()
        change_ratio = 1 - similarity_ratio
        
        # 3. Подсчитываем количество измененных символов
        old_words = set(old_content.split())
        new_words = set(new_content.split())
        
        added_words = new_words - old_words
        removed_words = old_words - new_words
        changed_chars = len(' '.join(added_words)) + len(' '.join(removed_words))
        
        # 4. Определяем значительность по нескольким критериям
        is_significant = False
        reasons = []
        
        if change_ratio >= config.SIGNIFICANT_CHANGE_THRESHOLD:
            is_significant = True
            reasons.append(f"изменено {change_ratio*100:.1f}% контента")
        
        if changed_chars >= config.MIN_CHANGED_CHARS:
            is_significant = True
            reasons.append(f"{changed_chars} измененных символов")
        
        if length_change_ratio > config.MAX_LENGTH_CHANGE_RATIO:
            is_significant = True
            reasons.append(f"изменение длины на {length_change_ratio*100:.1f}%")
        
        # Формируем описание изменений
        if is_significant:
            description = "Значительные изменения: " + ", ".join(reasons)
        else:
            description = f"Незначительные изменения: {change_ratio*100:.1f}% контента, {changed_chars} символов"
        
        return is_significant, description
    
    def check_site_availability(self, url: str) -> Tuple[bool, str, str]:
        """
        Проверяет доступность сайта без сохранения в базу данных
        Используется при добавлении нового сайта для валидации
        
        Args:
            url (str): URL сайта для проверки
            
        Returns:
            Tuple[bool, str, str]: (доступен_ли_сайт, сообщение_о_результате, контент_страницы)
        """
        try:
            # Выполняем HTTP запрос с таймаутом
            response = self.session.get(
                url, 
                timeout=config.REQUEST_TIMEOUT,
                allow_redirects=True
            )
            
            # Проверяем HTTP статус код
            if response.status_code != 200:
                return False, f"HTTP ошибка: {response.status_code}", ""
            
            # Получаем содержимое страницы с правильной кодировкой
            content = self._decode_response_content(response)
            
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
                # Сайт доступен, но контент малый - возвращаем предупреждение
                return True, f"⚠️ Мало контента: {len(clean_text)} символов (минимум {config.MIN_CONTENT_LENGTH})", clean_text
            
            # Если все проверки пройдены
            return True, f"✅ Сайт доступен, контент: {len(clean_text)} символов", clean_text
                
        except requests.exceptions.Timeout:
            return False, f"Таймаут запроса (>{config.REQUEST_TIMEOUT}с)", ""
            
        except requests.exceptions.ConnectionError:
            return False, "Ошибка подключения к сайту", ""
            
        except requests.exceptions.RequestException as e:
            return False, f"Ошибка запроса: {str(e)}", ""
            
        except Exception as e:
            return False, f"Неожиданная ошибка: {str(e)}", ""

    def _should_report_error(self, site: Dict) -> bool:
        """
        Определяет, нужно ли отправлять уведомление об ошибке
        Учитывает количество последовательных ошибок
        
        Args:
            site (Dict): Данные сайта
            
        Returns:
            bool: True если нужно отправить уведомление, False если это временная проблема
        """
        # Получаем количество последовательных ошибок из базы данных
        consecutive_errors = site.get('consecutive_errors', 0)
        
        # Если ошибок меньше порога - не отправляем уведомление (считаем временной проблемой)
        if consecutive_errors < config.CONSECUTIVE_ERROR_THRESHOLD:
            # Увеличиваем счетчик последовательных ошибок
            self._increment_consecutive_errors(site['id'])
            return False
        
        # Достигнут порог - сбрасываем счетчик и отправляем уведомление
        self._reset_consecutive_errors(site['id'])
        return True
    
    def _increment_consecutive_errors(self, site_id: int):
        """
        Увеличивает счетчик последовательных ошибок для сайта
        
        Args:
            site_id (int): ID сайта
        """
        sites = self.database._load_sites()
        for s in sites:
            if s['id'] == site_id:
                s['consecutive_errors'] = s.get('consecutive_errors', 0) + 1
                self.database._save_sites(sites)
                break
    
    def _reset_consecutive_errors(self, site_id: int):
        """
        Сбрасывает счетчик последовательных ошибок для сайта (при успешной проверке)
        
        Args:
            site_id (int): ID сайта
        """
        sites = self.database._load_sites()
        for s in sites:
            if s['id'] == site_id:
                s['consecutive_errors'] = 0
                self.database._save_sites(sites)
                break
    
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
