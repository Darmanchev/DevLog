# 📝 DevLog

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=green)
![Celery](https://img.shields.io/badge/celery-%23a9cc54.svg?style=for-the-badge&logo=celery&logoColor=f9f9f9)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

A comprehensive blogging and news platform built on **Django**. The project combines user-driven blog functionality with an automated news aggregator.

## 💡 About the Project

DevLog is designed as a portal for developers and tech enthusiasts. 
It consists of two main modules:
1. **Blog:** Users can register, create posts, use Markdown for formatting, leave comments, and like posts.
2. **News:** An automated news aggregator system. It utilizes Celery for background tasks to parse external sources and import news articles.

## 🚀 Core Stack and Development Stages

### Technologies
- **Backend:** Python, Django.
- **Background Tasks:** Celery + Redis (for asynchronous news importing).
- **Frontend:** Django HTML templates styled with modern **Tailwind CSS**.
- **Package Management:** Managed via `uv` for fast dependency resolution (`pyproject.toml` / `uv.lock`).

### Development Stages
- **Core Blog Engine:** Setting up models like `Post`, `Comment`, `Category`, and `Tag`. Implementing user CRUD operations.
- **Markdown Integration:** Adding Markdown support (`markdown_utils.py`) for a rich writing experience.
- **News Aggregator:** Creating the `news` app, configuring parsers, and scheduling periodic tasks using Celery.
- **UI/UX:** Styling all portal pages meticulously using Tailwind CSS.

## ⚙️ Deployment and Setup

The project is fully Dockerized for a smooth local launch.

1. Clone the repository:
   ```bash
   git clone https://github.com/Darmanchev/DevLog.git
   cd DevLog
   ```
2. Copy the environment configuration file:
   ```bash
   cp .env.example .env
   ```
3. Start the project via Docker Compose (spins up Django, PostgreSQL/SQLite, Redis, and Celery workers):
   ```bash
   docker-compose up -d
   ```
4. Run migrations and create a superuser:
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

---
*DevLog is more than just a blog. It is a feature-rich portal with background processing and a modern design.* 🌐
