"""
Модуль для мониторинга сайтов
Проверяет доступность сайтов и детектирует изменения в контенте
"""
import hashlib
import requests
import threading
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

        # Проверки могут прийти одновременно из планировщика и из /check.
        # requests.Session не потокобезопасна, поэтому проверки сериализуем
        self._check_lock = threading.RLock()

        # Сайты проверяем всегда напрямую с сервера, даже если для Telegram
        # заданы HTTPS_PROXY/ALL_PROXY: мониторинг должен видеть сайт так же,
        # как его видит сервер, а не прокси
        self.session.trust_env = False

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

        with self._check_lock:
            try:
                # Выполняем HTTP запрос с таймаутом
                response = self.session.get(
                    url,
                    timeout=config.REQUEST_TIMEOUT,
                    allow_redirects=True
                )

                # Проверяем HTTP статус код
                if response.status_code != 200:
                    return self._fail(site_id, f"HTTP ошибка: {response.status_code}")

                # Получаем содержимое страницы
                content = response.text

                # Проверяем минимальную длину контента
                if len(content) < config.MIN_CONTENT_LENGTH:
                    return self._fail(site_id, f"Слишком короткий контент: {len(content)} символов")

                # Извлекаем основной контент (убираем HTML теги)
                soup = BeautifulSoup(content, 'html.parser')

                # Запоминаем до удаления скриптов: нужно, чтобы распознать JS-сайт
                has_scripts = soup.find('script') is not None

                # Убираем скрипты, стили и другие технические элементы
                for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    script.decompose()

                # Получаем чистый текст
                clean_text = soup.get_text()

                # Убираем лишние пробелы и переносы строк
                clean_text = ' '.join(clean_text.split())

                # Проверяем минимальную длину очищенного текста
                if len(clean_text) < config.MIN_CONTENT_LENGTH:
                    # SPA (React, Vue и т.п.) рисует текст в браузере, а в HTML
                    # отдает только скрипты. Сайт доступен, но сравнивать нечего -
                    # проверяем только доступность, хеш и снимок не трогаем
                    if has_scripts:
                        self.database.update_site_status(site_id, 'ok')
                        return 'ok', 'Сайт доступен (JS-сайт: изменения контента не отслеживаются)', None

                    return self._fail(site_id, f"Слишком мало текстового контента: {len(clean_text)} символов")

                # Вычисляем хеш контента
                content_hash = hashlib.sha256(clean_text.encode('utf-8')).hexdigest()

                # Проверяем, изменился ли контент
                last_hash = site.get('last_content_hash')

                if last_hash is None:
                    # Первая проверка - просто сохраняем хеш и контент
                    self.database.save_snapshot(site_id, clean_text)
                    self.database.update_site_status(site_id, 'ok', content_hash)
                    return 'ok', 'Сайт доступен, контент сохранен', content_hash

                elif last_hash != content_hash:
                    # Контент изменился - проверяем значительность изменений
                    last_content = self.database.get_snapshot(site_id)
                    is_significant, change_description = self._is_significant_change(last_content, clean_text)

                    if is_significant:
                        # Значительные изменения - обновляем хеш и контент, отправляем уведомление
                        self.database.save_snapshot(site_id, clean_text)
                        self.database.update_site_status(site_id, 'changed', content_hash)
                        return 'changed', f'Сайт доступен: {change_description}', content_hash
                    else:
                        # Незначительные изменения - НЕ обновляем хеш и снимок,
                        # чтобы мелкие правки не накапливались незамеченными
                        self.database.update_site_status(site_id, 'minor_change', last_hash)
                        return 'ok', f'Сайт доступен: {change_description}', last_hash

                else:
                    # Контент не изменился
                    self.database.update_site_status(site_id, 'ok', content_hash)
                    return 'ok', 'Сайт доступен, контент не изменился', content_hash

            except requests.exceptions.Timeout:
                return self._fail(site_id, f"Таймаут запроса (>{config.REQUEST_TIMEOUT}с)")

            except requests.exceptions.ConnectionError:
                return self._fail(site_id, "Ошибка подключения к сайту")

            except requests.exceptions.RequestException as e:
                return self._fail(site_id, f"Ошибка запроса: {str(e)}")

            except Exception as e:
                return self._fail(site_id, f"Неожиданная ошибка: {str(e)}")

    def _fail(self, site_id: int, error_message: str) -> Tuple[str, str, None]:
        """
        Записывает ошибку проверки и формирует результат

        Args:
            site_id (int): ID сайта
            error_message (str): Описание ошибки

        Returns:
            Tuple[str, str, None]: Результат проверки со статусом 'error'
        """
        self.database.update_site_status(site_id, 'error', error_message=error_message)
        return 'error', error_message, None

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
        last_error = site.get('last_error')
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
                'changed': '🔄',
                'minor_change': '➖'
            }
            summary += f"📈 Статус: {status_emoji.get(last_status, '❓')} {last_status}\n"

        if last_error:
            summary += f"⚠️ Причина: {last_error}\n"

        return summary
