# 🐳 Docker развертывание

Полное руководство по развертыванию приложения мониторинга сайтов с Docker на VPS.

## ⚡ Быстрый старт

### 1. Подготовка сервера
```bash
# Скачайте проект на VPS
git clone <ваш-репозиторий>
cd chanki

# Сделайте скрипт исполняемым
chmod +x docker-deploy.sh
```

### 2. Настройка переменных окружения
```bash
# Создайте .env файл из шаблона
cp docker.env.example .env

# Отредактируйте .env и добавьте токен бота
nano .env
```

### 3. Запуск
```bash
# Запустите автоматическое развертывание
./docker-deploy.sh
```

## 📁 Структура Docker файлов

```
📁 Проект
├── 🐳 Dockerfile              # Образ приложения
├── 📋 docker-compose.yml      # Оркестрация контейнеров
├── 🚫 .dockerignore          # Исключения для сборки
├── 🛠️ docker-deploy.sh       # Скрипт автоматического развертывания
└── 📄 docker.env.example     # Шаблон переменных окружения
```

## 🔧 Подробная настройка

### Dockerfile

**Основные особенности:**
- Базовый образ: `python:3.11-slim`
- Установка UV для управления зависимостями
- Создание непривилегированного пользователя
- Оптимизация для производства

### docker-compose.yml

**Включает:**
- Автоматический перезапуск контейнера
- Монтирование volumes для данных и логов
- Ограничения ресурсов (256MB RAM, 0.5 CPU)
- Health check для мониторинга состояния
- Изолированная сеть

### Переменные окружения

**Обязательные:**
```env
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

**Опциональные:**
```env
CHECK_INTERVAL_HOURS=6          # Интервал проверки
REQUEST_TIMEOUT=10              # Таймаут запросов
SIGNIFICANT_CHANGE_THRESHOLD=0.15   # Порог значительных изменений
MIN_CHANGED_CHARS=50            # Мин. количество измененных символов
MAX_LENGTH_CHANGE_RATIO=0.30    # Макс. изменение длины контента
```

## 🚀 Развертывание на VPS

### Системные требования

**Минимальные:**
- CPU: 1 ядро
- RAM: 512 MB
- Диск: 1 GB свободного места
- ОС: Ubuntu 20.04+ / Debian 10+ / CentOS 8+

**Рекомендуемые:**
- CPU: 2 ядра
- RAM: 1 GB
- Диск: 5 GB свободного места

### Пошаговая инструкция

#### 1. Подготовка сервера
```bash
# Обновляем систему
sudo apt update && sudo apt upgrade -y

# Устанавливаем git (если не установлен)
sudo apt install -y git

# Клонируем проект
git clone <ваш-репозиторий>
cd chanki
```

#### 2. Настройка приложения
```bash
# Создаем .env файл
cp docker.env.example .env

# Редактируем настройки
nano .env
```

**Пример .env файла:**
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
CHECK_INTERVAL_HOURS=6
REQUEST_TIMEOUT=10
DEBUG=false
```

#### 3. Запуск развертывания
```bash
# Запускаем автоматическую установку
./docker-deploy.sh
```

Скрипт автоматически:
- ✅ Установит Docker и Docker Compose
- ✅ Создаст необходимые директории
- ✅ Соберет образ приложения
- ✅ Запустит контейнер в фоновом режиме

## 📊 Управление контейнером

### Основные команды

```bash
# Просмотр статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f site-monitor

# Перезапуск
docker-compose restart site-monitor

# Остановка
docker-compose stop

# Полное удаление
docker-compose down

# Обновление образа
docker-compose build --no-cache
docker-compose up -d
```

### Мониторинг

```bash
# Просмотр последних логов
docker-compose logs --tail=50 site-monitor

# Мониторинг ресурсов
docker stats site-monitor-bot

# Проверка health check
docker inspect site-monitor-bot | grep Health -A 10
```

## 📁 Управление данными

### Volumes и монтирование

**Автоматически создаются:**
- `./data/` - данные приложения
- `./logs/` - файлы логов
- `./sites.json` - база данных сайтов
- `./monitor.log` - основной лог

### Резервное копирование

```bash
# Создание резервной копии
tar -czf backup-$(date +%Y%m%d).tar.gz sites.json monitor.log data/ logs/

# Восстановление из резервной копии
tar -xzf backup-20231225.tar.gz
docker-compose restart site-monitor
```

## 🔒 Безопасность

### Рекомендации по безопасности

1. **Ограничение доступа:**
```bash
# Ограничиваем доступ к .env файлу
chmod 600 .env

# Ограничиваем доступ к данным
chmod 750 data logs
```

2. **Обновления:**
```bash
# Регулярно обновляйте образ
docker-compose pull
docker-compose up -d
```

3. **Мониторинг:**
```bash
# Настройте мониторинг логов
tail -f logs/monitor.log | grep ERROR
```

### Firewall настройки

```bash
# Разрешаем только SSH и блокируем остальное
sudo ufw allow ssh
sudo ufw enable

# Docker автоматически настроит необходимые правила
```

## 🚨 Устранение неполадок

### Частые проблемы

#### 1. Контейнер не запускается
```bash
# Проверяем логи
docker-compose logs site-monitor

# Проверяем .env файл
cat .env | grep TELEGRAM_BOT_TOKEN
```

#### 2. Нет доступа к интернету
```bash
# Проверяем сетевые настройки
docker network ls
docker network inspect chanki_site-monitor-network
```

#### 3. Проблемы с разрешениями
```bash
# Исправляем права доступа
sudo chown -R $USER:$USER data logs sites.json monitor.log
chmod 644 sites.json monitor.log
chmod 755 data logs
```

#### 4. Нехватка ресурсов
```bash
# Проверяем использование ресурсов
docker stats site-monitor-bot

# Увеличиваем лимиты в docker-compose.yml
nano docker-compose.yml
```

### Диагностика

```bash
# Полная диагностика
echo "=== Статус контейнера ==="
docker-compose ps

echo "=== Последние логи ==="
docker-compose logs --tail=20 site-monitor

echo "=== Использование ресурсов ==="
docker stats site-monitor-bot --no-stream

echo "=== Размер данных ==="
du -sh data logs sites.json monitor.log
```

## 🔄 Обновление приложения

### Обновление кода

```bash
# Получаем новые изменения
git pull origin main

# Пересобираем образ
docker-compose build --no-cache

# Перезапускаем с новым образом
docker-compose up -d
```

### Обновление конфигурации

```bash
# Редактируем переменные окружения
nano .env

# Перезапускаем контейнер
docker-compose restart site-monitor
```

## 📈 Масштабирование

### Запуск нескольких экземпляров

```bash
# Копируем проект для второго бота
cp -r chanki chanki-bot2
cd chanki-bot2

# Настраиваем другой токен
nano .env

# Запускаем второй экземпляр
./docker-deploy.sh
```

---

**🎯 Docker развертывание обеспечивает:**
- ✅ Изоляцию приложения
- ✅ Простое развертывание
- ✅ Автоматические перезапуски
- ✅ Контроль ресурсов
- ✅ Простое обновление
