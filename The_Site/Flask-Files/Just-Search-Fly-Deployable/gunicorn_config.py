import os

workers = int(os.environ.get('GUNICORN_PROCESSES', '1'))
threads = int(os.environ.get('GUNICORN_THREADS', '2'))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '120'))
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8080')

certfile = os.environ.get('GUNICORN_CERTFILE', '/etc/letsencrypt/live/search-engine-api.fly.dev/fullchain.pem')
keyfile = os.environ.get('GUNICORN_KEYFILE', '/etc/letsencrypt/live/search-engine-api.fly.dev/privkey.pem')

forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'https'}