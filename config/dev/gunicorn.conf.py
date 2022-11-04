# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html#configuration-file
# https://docs.gunicorn.org/en/stable/settings.html

import multiprocessing

# restart workers after so many requests with some variability
max_requests = 1000
max_requests_jitter = 50


bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1

# Access log - records incoming HTTP requests
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s "%(r)s" %(s)s'

# Error log - records Gunicorn server errors
errorlog = "-"
error_log_format = '%(h)s %(l)s %(u)s "%(r)s" %(s)s'

log_file = "-"

# How verbose the Gunicorn error logs should be
loglevel = "info"

# Whether to send Django output to the error log
capture_output = True

enable_stdio_inheritance = True
