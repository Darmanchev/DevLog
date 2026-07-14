# DevLog

DevLog is a student project that combines a developer blog with a Bulgarian news reader. I built it to practice a complete Django application: authentication, content management, search, comments, background infrastructure and importing data that I do not control.

## Features

- registration, login and author profiles;
- create, edit and delete posts;
- Markdown rendering with HTML sanitization;
- categories, tags, cover images and likes;
- nested comments with edit and soft delete;
- search by title, text, author, category and tag;
- sorting by date, likes, comments or relevance;
- RSS source management and article import;
- SQLite for a quick local start or PostgreSQL in production.

## Why Django

I chose **Django** because the ORM, authentication, forms, migrations and admin panel let me focus on the product instead of rebuilding standard backend features. Server-rendered templates were enough for this project and kept the frontend simpler than a separate SPA.

The most difficult part was the news importer. RSS feeds provide different fields and the linked pages contain navigation, donation banners and other unrelated HTML. The importer combines `feedparser`, `readability` and Beautiful Soup, then sanitizes the extracted content. Another challenge was avoiding duplicate counts when search, tags, comments and likes are joined in one queryset.

## Stack

- Python 3.13, Django 6
- Django templates, Tailwind-generated CSS
- SQLite or PostgreSQL
- feedparser, Beautiful Soup, readability-lxml, bleach
- Celery and Redis infrastructure
- uv

## Run locally

```bash
git clone https://github.com/Darmanchev/DevLog.git
cd DevLog
cp .env.example .env
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

To add the default Bulgarian news sources and import their latest articles:

```bash
uv run python manage.py seed_news_sources
uv run python manage.py import_bg_news
```

Run the test suite with:

```bash
uv run python manage.py test
```

Redis and a Celery worker can be started separately:

```bash
docker compose up -d
uv run celery -A django_blog_site worker --loglevel=info
```

The current `docker-compose.yml` starts Redis only; the Django application itself still runs locally with `uv`.

## Project structure

```text
blog/       posts, comments, profiles, search and tests
news/       RSS sources, imported articles and importer
templates/  server-rendered pages
static/     project styles
django_blog_site/ settings, URLs and Celery configuration
```

## Current status and next steps

The blog and manual RSS import are implemented. Celery is configured, but the importer is not yet connected to a periodic task; the existing task is only a connectivity check. The next steps are scheduled imports, a complete Docker setup for web/worker/database, pagination for large news collections, better source-specific parsing and deployment monitoring.
