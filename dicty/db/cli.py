import click
import pycountry
from flask.cli import AppGroup
from sqlalchemy_utils import database_exists, create_database, drop_database

from . import db
from . import models

cli = AppGroup('db')


def insert_languages() -> None:
    for i in pycountry.languages:
        db.session.add(models.Language(name=i.name, code=i.alpha_3))
    db.session.commit()


@cli.command('create')
@click.option('--force', is_flag=True, help='Drop existing database.')
def create(force: bool) -> None:
    url = db.engine.url
    is_exists = database_exists(url)
    if is_exists:
        if force:
            drop_database(url)
        else:
            click.echo(click.style(f"cannot create database '{url}': Database exists", fg='red'))
            return None
    create_database(url)
    db.create_all()
    insert_languages()
