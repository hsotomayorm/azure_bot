import os
import importlib

# Try to import the user's Flask app instance from app.py
# It should either expose `app = Flask(__name__)` OR a create_app() factory.
module = importlib.import_module("app")
flask_app = getattr(module, "app", None)

if flask_app is None:
    # If there's a factory instead
    if hasattr(module, "create_app"):
        flask_app = module.create_app()
    else:
        # Fallback: create a minimal app so the container doesn't crash
        from flask import Flask
        flask_app = Flask(__name__)

        @flask_app.get("/")
        def _fallback_root():
            return "Flask is running, but no `app` or `create_app` was found in app.py", 200

app = flask_app  # Gunicorn expects a WSGI callable named `app`

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
