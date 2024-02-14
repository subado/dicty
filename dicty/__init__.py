import tomllib

import click
from flask import Flask
from sqlalchemy_utils import database_exists

from .scraper import scraper, DictionaryToWebsites
from .scraper.website.collins import Collins
from .db import db
from .db import cli as db_cli
from .db.bakery import get_language
from .db.models import Dictionary
from .json import JsonProvider


@click.pass_context
def create_app(ctx, config_file='config.toml') -> Flask:
    app = Flask(__name__)
    app.config.from_file(config_file, load=tomllib.load, text=False)
    app.config.from_prefixed_env()

    db.init_app(app)
    app.cli.add_command(db_cli.cli)

    app.json = JsonProvider(app)

    with app.app_context():
        if not database_exists(db.engine.url):
            ctx.invoke(db_cli.create)

        scraper.init_app(app, [
            DictionaryToWebsites(Dictionary(name='collins', languages=[get_language(db.session()).params(name='english').scalar()]),
                                 [Collins(timeout=10)])
        ])

    from .blueprints import units
    app.register_blueprint(units.bp)
    from .blueprints import dictionaries
    app.register_blueprint(dictionaries.bp)

    return app
