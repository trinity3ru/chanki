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
