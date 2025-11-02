# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем UV для управления зависимостями
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем Python зависимости
# Увеличиваем таймаут для загрузки больших пакетов (например, lxml)
ENV UV_HTTP_TIMEOUT=120
RUN uv pip install --system -r requirements.txt

# Копируем исходный код приложения
COPY *.py ./
COPY *.md ./
COPY *.txt ./
COPY *.sh ./

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 sitebot

# Создаем директории для данных и логов
RUN mkdir -p /app/data /app/logs /app/host_data && \
    chown -R sitebot:sitebot /app

USER sitebot

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Открываем порт (если в будущем добавим веб-интерфейс)
EXPOSE 8000

# Точка входа для запуска приложения
CMD ["python", "main.py"]
