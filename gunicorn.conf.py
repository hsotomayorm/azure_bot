import os

# Bind to the port provided by Code Engine (or 8080 by default)
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"

# Sensible defaults for small Flask apps
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("WEB_THREADS", "1"))
timeout = int(os.getenv("WEB_TIMEOUT", "120"))
preload_app = True

# Access log to stdout (Code Engine captures logs)
accesslog = "-"
errorlog = "-"
