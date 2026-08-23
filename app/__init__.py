import os
from datetime import date

import resend
from flask import Flask, render_template
from flask_compress import Compress

from app.data.loader import load_all
from config import config

compress = Compress()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    compress.init_app(app)
    app.config["SITE_DATA"] = load_all()

    resend.api_key = app.config["RESEND_API_KEY"]

    from app.routes import asset_exists, main
    app.register_blueprint(main)
    app.jinja_env.globals["asset_exists"] = asset_exists

    @app.url_defaults
    def stamp_static_url(endpoint, values):
        """Append ?v=<mtime> to static URLs.

        Static files are cached for a year, so without this a returning visitor
        keeps the old CSS after a deploy. Changing a file changes its URL.
        """
        if endpoint != "static" or "filename" not in values:
            return
        path = os.path.join(app.static_folder, values["filename"])
        if os.path.isfile(path):
            values["v"] = int(os.path.getmtime(path))

    @app.context_processor
    def inject_globals():
        # Footer copyright — computed per render so it never goes stale.
        return {"current_year": date.today().year}

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html", **app.config["SITE_DATA"]), 404

    return app
