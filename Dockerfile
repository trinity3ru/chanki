# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# UV берем из официального образа с зафиксированной версией,
# а не скриптом из интернета: сборка воспроизводима и не тянет curl
COPY --from=ghcr.io/astral-sh/uv:0.12.18 /uv /bin/uv

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN uv pip install --system -r requirements.txt

# Копируем исходный код приложения
COPY *.py ./

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 sitebot

# Создаем директории для данных и логов.
# Именованные volume'ы наследуют владельца из образа, поэтому chown здесь
# избавляет от возни с правами на хосте
RUN mkdir -p /app/data/snapshots /app/logs && \
    chown -R sitebot:sitebot /app

USER sitebot

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Порты не открываем: бот работает через long polling, web-интерфейса нет

# Точка входа для запуска приложения
CMD ["python", "main.py"]
