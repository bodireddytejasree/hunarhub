# HunarHub: Digital Marketplace for Local Micro-Entrepreneurs

Django + SQL (SQLite by default; MySQL or PostgreSQL via environment variables).

## Run locally
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo        # optional demo data
python manage.py runserver
```
Open http://127.0.0.1:8000/

Demo logins (after `seed_demo`): `customer / demo12345`, `ramesh / demo12345` (entrepreneur), `admin / admin12345` (admin).
Change or delete these before any real deployment.

To make your own admin instead: `python manage.py createsuperuser`.

## Run the tests
```bash
python manage.py test
```

## What is where
- `accounts/` user model with roles, registration, login, role-based redirect
- `marketplace/` models, views, forms, URLs, tests, `seed_demo` command
- `templates/`, `static/css/style.css` the UI
- `docs/PRD_and_Technical_Overview.md` PRD and technical documentation

## Deploy
Set environment variables: `DEBUG=0`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`,
and for a real database `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
(`DB_ENGINE=django.db.backends.mysql` for MySQL, after `pip install mysqlclient`).
Then:
```bash
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi
```
A `Procfile` is included for platforms such as Render or Railway. Uploaded images go to `media/`;
on hosts with temporary disks, move media to object storage (for example S3) before going live.
