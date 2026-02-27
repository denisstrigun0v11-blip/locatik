
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Создаём файл для базы данных (если нужно)
RUN touch webtech_concepts.db

# Запускаем бота
CMD ["python3", "bot.py"]