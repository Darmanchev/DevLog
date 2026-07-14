# 📝 DevLog

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![Celery](https://img.shields.io/badge/celery-%23a9cc54.svg?style=for-the-badge&logo=celery&logoColor=f9f9f9)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

Полноценная платформа для блогов и новостей, разработанная на базе **Django**. Проект объединяет в себе функционал пользовательских блогов и автоматического агрегатора новостей.

## 💡 О проекте

DevLog задуман как портал для разработчиков и энтузиастов. 
В нем есть два основных модуля:
1. **Blog (Блог):** Пользователи могут регистрироваться, создавать посты, использовать Markdown для форматирования, оставлять комментарии и ставить лайки.
2. **News (Новости):** Автоматизированная система сбора новостей. Использует Celery для фоновых задач по парсингу внешних источников и импорту новостных статей.

## 🚀 Основной стек и этапы создания

### Технологии
- **Backend:** Python, Django.
- **Background Tasks:** Celery + Redis (для асинхронного импорта новостей).
- **Frontend:** HTML-шаблоны Django с использованием современного **Tailwind CSS**.
- **Package Management:** Использование `uv` для быстрого управления зависимостями (`pyproject.toml` / `uv.lock`).

### Этапы разработки
- **Базовый блог:** Настройка моделей `Post`, `Comment`, `Category`, `Tag`. Реализация CRUD операций для пользователей.
- **Интеграция Markdown:** Добавление поддержки Markdown (`markdown_utils.py`) для удобного написания статей.
- **Новостной агрегатор:** Создание приложения `news`, настройка парсеров и периодических задач через Celery.
- **UI/UX:** Стилизация всех страниц портала с помощью Tailwind CSS.

## ⚙️ Развертывание и запуск

Проект готов к локальному запуску с помощью Docker.

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/Darmanchev/DevLog.git
   cd DevLog
   ```
2. Скопируйте файл конфигурации окружения:
   ```bash
   cp .env.example .env
   ```
3. Запустите проект через Docker Compose (поднимет Django, PostgreSQL/SQLite, Redis и Celery-воркеры):
   ```bash
   docker-compose up -d
   ```
4. Выполните миграции и создайте суперпользователя:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

---
*DevLog — это больше, чем просто блог. Это функциональный портал с фоновыми задачами и современным дизайном.* 🌐
