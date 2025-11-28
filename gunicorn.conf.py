import os
from gunicorn import glogging
from conecta_senai.logging_conf import LOGGING_CONFIG

wsgi_app = "conecta_senai.main:create_app()"
bind = "0.0.0.0:8080"
workers = 1
threads = int(os.getenv("GTHREADS", "1"))
worker_class = os.getenv("WORKER_CLASS", "sync")
timeout = 30
loglevel = "debug"
keepalive = 2
max_requests = 600
max_requests_jitter = 60
preload_app = False


class RequestIDLogger(glogging.Logger):
    def access(self, resp, req, environ, request_time):
        request_id = None
        headers = getattr(resp, "headers", {})
        if hasattr(headers, "get"):
            request_id = headers.get("X-Request-ID")
        if not request_id:
            request_id = environ.get("HTTP_X_REQUEST_ID", "-")
        environ["o"] = request_id
        super().access(resp, req, environ, request_time)


logger_class = RequestIDLogger
logconfig_dict = LOGGING_CONFIG
accesslog = '-'
ACCESS_LOG_FORMAT = (
    '{"ts":"%(t)s","h":"%(h)s","r":"%(r)s","s":"%(s)s","b":"%(b)s",'
    '"D":"%(D)s","request_id":"%(o)s"}'
)
access_logformat = ACCESS_LOG_FORMAT
