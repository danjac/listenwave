release: ./release.sh
web: gunicorn -c ./gunicorn.conf.py radiofeed.wsgi --access-logfile -
worker: ./manage.py rqworker
