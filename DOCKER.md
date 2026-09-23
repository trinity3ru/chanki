# 🐳 Развертывание в Docker

Бот работает через long polling и **не имеет web-интерфейса**, поэтому порты
наружу не публикуются вообще. Это важно на общем сервере, где 80/443 уже заняты
Nginx Proxy Manager.

## 📋 Требования

- Docker
- Docker Compose **v2** (команда `docker compose`, не `docker-compose`)
- Токен бота от [@BotFather](https://t.me/botfather)

Скрипты в этом репозитории ничего не устанавливают в систему — Docker должен
быть уже настроен.

## 🚀 Развертывание

```bash
# 1. Скопируйте проект на сервер
git clone <your-repo> chanki
cd chanki

# 2. Создайте .env
cp docker.env.example .env
nano .env          # вставьте реальный TELEGRAM_BOT_TOKEN
chmod 600 .env

# 3. Запустите
./deploy.sh
```

`deploy.sh` проверит наличие Docker и Compose v2, заполненность `.env`,
свободно ли имя контейнера, соберёт образ и поднимет сервис. Он не выполняет
`docker compose down`, ничего не удаляет и не трогает чужие контейнеры.

Ручной эквивалент:

```bash
docker compose build
docker compose up -d
```

## 🔒 Изоляция на общем сервере

Проект спроектирован так, чтобы не пересекаться с соседями:

| Ресурс | Значение | Почему так |
|--------|----------|------------|
| Порты | не публикуются | long polling, web-интерфейса нет; 80/443 заняты NPM |
| Контейнер | `chanki-site-monitor` | уникальное имя, `deploy.sh` проверяет занятость |
| Проект Compose | `chanki` (`name:` в compose) | имена не зависят от каталога клонирования |
| Сеть | `chanki_chanki-net` (своя bridge) | к существующим сетям не подключаемся |
| Volume'ы | `chanki_chanki-data`, `chanki_chanki-logs` | свои именованные, чужие не монтируем |
| Каталог проекта | в контейнер **не** пробрасывается | `.env` и `.git` остаются на хосте |
| Логи Docker | ротация 10 МБ × 3 | чтобы не съесть диск общего сервера |

Proxy Host в Nginx Proxy Manager для этого сервиса **не нужен**.

## 📁 Где лежат данные

Внутри контейнера:

| Путь | Volume | Содержимое |
|------|--------|-----------|
| `/app/data/sites.json` | `chanki-data` | список сайтов и статусы проверок |
| `/app/data/snapshots/` | `chanki-data` | снимки текста страниц для сравнения |
| `/app/logs/monitor.log` | `chanki-logs` | логи приложения |

Права выставляются в образе: приложение работает от пользователя `sitebot`
(UID 1000), именованные volume'ы наследуют владельца. Возиться с `chown` и
`chmod` на хосте не нужно.

## ⚙️ Настройки

Переменные читаются из `.env` рядом с `docker-compose.yml`:

| Переменная | По умолчанию | Описание |
|-----------|:------------:|----------|
| `TELEGRAM_BOT_TOKEN` | — | **обязательно**, токен бота |
| `TELEGRAM_PROXY_URL` | пусто | прокси для Telegram, если API недоступен напрямую |
| `CONNECT_TIMEOUT` | 20 | таймаут соединения с Telegram в секундах |
| `READ_TIMEOUT` | 20 | таймаут чтения ответа Telegram в секундах |
| `CHECK_INTERVAL_HOURS` | 6 | интервал проверки в часах |
| `REQUEST_TIMEOUT` | 10 | таймаут HTTP запроса к проверяемым сайтам |
| `MIN_CONTENT_LENGTH` | 100 | минимальная длина контента |
| `ERROR_RETRY_DELAY_SECONDS` | 30 | пауза перед перепроверкой упавшего сайта |

Если `TELEGRAM_BOT_TOKEN` не задан, `docker compose` откажется стартовать с
понятной ошибкой, а не поднимет нерабочий контейнер.

Ресурсы ограничены: 256 МБ памяти и 0.5 CPU (резерв 128 МБ / 0.2 CPU).

## 🔧 Управление

```bash
docker compose ps                         # статус
docker compose logs -f site-monitor       # логи в реальном времени
docker compose logs --tail=50 site-monitor
docker compose restart site-monitor       # перезапуск
docker compose stop site-monitor          # остановка
```

Диагностика одной командой (только чтение, ничего не меняет):

```bash
./diagnose.sh
```

## 🔄 Обновление

```bash
git pull
docker compose build
docker compose up -d
```

Данные в volume'ах переживают пересборку. Формат базы мигрирует автоматически:
при первом чтении старого `sites.json` (плоский список со встроенным
`last_content`) он будет переписан в новый формат.

## 💾 Восстановление из бэкапа

Бэкап — архив содержимого `/app/data` (`sites.json` и `snapshots/`).
Восстанавливать до первого запуска бота, иначе он успеет создать пустую базу:

```bash
# 1. Собрать образ (.env с токеном уже должен лежать рядом)
docker compose build

# 2. Распаковать архив в volume данных и отдать файлы пользователю приложения.
#    Volume chanki_chanki-data создается автоматически
docker compose run --rm --no-deps -u 0 \
  -v "$PWD/chanki-data.tar.gz:/backup.tar.gz:ro" \
  site-monitor sh -c 'tar -xzf /backup.tar.gz -C /app/data && chown -R sitebot:sitebot /app/data'

# 3. Запустить
docker compose up -d
```

Снять бэкап с работающего бота:

```bash
docker compose exec -T site-monitor tar -czf - -C /app/data . > chanki-data.tar.gz
```

## 🗑️ Удаление

```bash
docker compose down          # остановить и удалить контейнер и сеть проекта
```

Volume'ы при этом сохраняются. Чтобы удалить и данные:

```bash
docker compose down -v       # ⚠️ удалит список сайтов и снимки безвозвратно
```

> `docker compose down` затрагивает только этот проект. Не запускайте
> `docker system prune` или `docker network prune` на общем сервере — они
> заденут соседние проекты.

## 🚨 Устранение неполадок

**Контейнер перезапускается по кругу.** Смотрите `docker compose logs
site-monitor`. Чаще всего — неверный токен: `telegram.error.InvalidToken`.

**`Не удалось связаться с Telegram (TimedOut)` при каждом старте.** Токен ни
при чём: при неверном токене Telegram отвечает `Unauthorized` мгновенно, а
таймаут означает, что соединение не устанавливается. Проверьте с хоста:

```bash
curl -sS -o /dev/null -w '%{http_code} за %{time_total}s\n' --max-time 20 https://api.telegram.org
curl -sS -o /dev/null -w '%{http_code} за %{time_total}s\n' --max-time 20 https://www.google.com
```

Если google отвечает `200`, а Telegram — нет, значит трафик на сети Telegram
блокируется провайдером или страной размещения. Настройками Docker это не
лечится, нужен прокси:

```bash
echo 'TELEGRAM_PROXY_URL=http://login:password@1.2.3.4:8000' >> .env
docker compose up -d
```

В логах при успехе появится `Связь с Telegram настроена через прокси
http://***:***@1.2.3.4:8000` — учётные данные в логи не пишутся.

**Формат обязателен со схемой.** Продавцы прокси обычно выдают строку вида
`ip:port:login:password` — её нужно переписать в URL:

```
161.0.6.18:8000:user:pass   ->   http://user:pass@161.0.6.18:8000
```

Если схему не указать, приложение остановится с подсказкой, а не с невнятной
ошибкой клиента. Спецсимволы в пароле кодируются процентами (`@` = `%40`).

**Какой у вас тип прокси**, HTTP или SOCKS5, проще проверить curl'ом — тот,
что ответит быстро и не отвалится по таймауту:

```bash
curl -sS -o /dev/null -w 'HTTP:   %{http_code} за %{time_total}s\n' --max-time 20 \
  -x 'http://login:password@1.2.3.4:8000' https://api.telegram.org
curl -sS -o /dev/null -w 'SOCKS5: %{http_code} за %{time_total}s\n' --max-time 20 \
  -x 'socks5h://login:password@1.2.3.4:8000' https://api.telegram.org
```

Ответ `302` — это норма для корня `api.telegram.org`, соединение работает.

Проверки сайтов через прокси не идут: монитор всегда обращается к сайтам
напрямую с сервера, чтобы видеть их так же, как их видит сам сервер.

**`Bad Request: chat not found` в логах.** Пользователь не начинал диалог с
ботом или заблокировал его. Уведомления такому пользователю не дойдут,
остальные обрабатываются штатно.

**Имя контейнера занято.** Значит, `chanki-site-monitor` уже используется
другим проектом. Измените `container_name` в `docker-compose.yml`.

**Healthcheck показывает unhealthy.** Проверяется доступность
`api.telegram.org` из контейнера. Если сеть в порядке, а статус красный —
смотрите логи, проблема в приложении.
