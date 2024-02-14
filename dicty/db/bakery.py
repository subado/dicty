from sqlalchemy import bindparam
from sqlalchemy.ext import baked

from .models import Language

bakery = baked.bakery()

get_language = bakery(lambda session: session.query(Language))
get_language += lambda q: q.filter(Language.name == bindparam('name'))
