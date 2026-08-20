# Coolify deployment

The production stack is defined in `docker-compose.coolify.yml`:

- a separate Coolify PostgreSQL resource, connected through `DATABASE_URL`;
- Django served by Gunicorn;
- WhiteNoise for versioned static assets;
- a dedicated Nginx image with the proxy configuration built in for reverse
  proxying and serving user-uploaded files;
- a persistent media volume;
- database migrations on web container startup;
- health checks for every service.

No custom domain or external object storage is required. Coolify can generate a
free `sslip.io` URL for the Nginx service.

## Branch workflow

- `main` is the development branch;
- `deployment` is the deployment branch connected to Coolify;
- develop and test changes in `main`, then merge `main` into `deployment`;
- deploy only after the checks on `deployment` pass.

Do not commit production secrets to either branch. Coolify stores them as
environment variables.

## 1. Security cleanup

`.env` and `db.sqlite3` must not be tracked by Git. Rotate any secret that has
already been committed and reset passwords for real users from the published
SQLite database. Rewriting Git history is recommended for a public repository.

## 2. Create the Coolify resource

1. Push the `deployment` branch to the Git provider.
2. In Coolify, create a new resource from the repository.
3. Select the Docker Compose build pack.
4. Set the compose location to `/docker-compose.coolify.yml`.
5. Keep the base directory as `/`.
6. Select `deployment` as the branch to deploy.
7. In the environment variables, generate a new `SECRET_KEY`.
8. Create a PostgreSQL resource in the same Coolify project. Copy its private
   connection URL into the application resource as `DATABASE_URL`.
9. Generate an HTTPS domain for the `nginx` service. Without a wildcard domain,
   Coolify generates an `sslip.io` address.
10. Deploy the stack.

The generated `SERVICE_URL_NGINX` and `SERVICE_FQDN_NGINX` values are passed to
Django automatically, so `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` do not need
the generated hostname to be hard-coded.

## 3. Required variables

```env
SECRET_KEY=<new-long-random-value>
DATABASE_URL=postgresql://<user>:<password>@<private-host>:5432/<database>
```

The compose file supplies production-safe defaults for the other settings. Do
not enable HSTS until HTTPS has been verified. Coolify already redirects the
public endpoint to HTTPS, so `SECURE_SSL_REDIRECT` stays disabled in Django to
keep internal health checks working.

## 4. First deployment

Migrations run automatically before Gunicorn starts. After the stack is healthy,
open the `web` container terminal in Coolify and run:

```bash
python manage.py createsuperuser
python manage.py seed_news_sources
```

The seed command is optional.

## 5. Persistent data and backups

The following named volumes must be included in backups:

- `media_data` — uploaded post covers.

Configure backups on the PostgreSQL resource and back up `media_data` off the
server. A redeploy preserves data, but loss of the server does not.

## 6. Verification

Check the following URLs after deployment:

```text
/healthz/  -> 200 ok
/static/css/portal.css -> 200
/admin/ -> Django admin login
```

Upload a cover image through the admin and confirm its `/media/post_covers/...`
URL remains available after a redeploy.

## Local development

Local development keeps using `.env`, SQLite, and the existing
`docker-compose.yml` Redis service:

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py runserver
```
