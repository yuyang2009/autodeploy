web: gunicorn config.wsgi:application
worker: celery worker --app=autodeploy.taskapp --loglevel=info
