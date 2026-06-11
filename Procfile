release: python manage.py collectstatic --no-input && python manage.py migrate --no-input
web: gunicorn macnf.wsgi --log-file -