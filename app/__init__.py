import os
from flask import Flask
from flask_compress import Compress
from config import config

compress = Compress()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    compress.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    return app
