FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY . .
RUN uv sync --locked --no-dev

RUN SECRET_KEY=build-only DEBUG=False ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput --ignore='src/*'

RUN addgroup --system app \
    && adduser --system --ingroup app app \
    && mkdir -p /app/media \
    && chown -R app:app /app/media

EXPOSE 8000

USER app

ENTRYPOINT ["/app/docker/entrypoint.sh"]

CMD ["gunicorn", "django_blog_site.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--no-control-socket", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
