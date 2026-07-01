# Production Setup

1. Create `.env` from `.env.example`.

2. Set production values:

```env
SECRET_KEY=long-random-secret
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
DATABASE_URL=postgres://blog_user:strong_password@db-host:5432/blog_db?sslmode=require
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

3. Run deployment commands:

```bash
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
uv run python manage.py check --deploy
```

4. Serve `staticfiles/` and `media/` with nginx, CDN, or the hosting platform.

Local development can keep `DEBUG=True` and an empty `DATABASE_URL` to use SQLite.
