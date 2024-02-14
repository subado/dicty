from uuid import UUID

from flask import Blueprint, jsonify

from ..db import db
from ..scraper import scraper
from ..db.models import Dictionary, Unit, Language
from ..db.bakery import get_language

bp = Blueprint('units', __name__, url_prefix='/units')


@bp.route('/<dictionary_name>/<language_code>/<text>', methods=['GET'])
def unit(dictionary_name: str, language_code: str, text: str) -> str:
    unit = db.session.execute(
        db.select(Unit)
        .where(Unit.language.has(Language.code == language_code))
        .where(Unit.text == text)
        .where(Unit.dictionary.has(Dictionary.name == dictionary_name))
    ).scalar()
    if unit is None:
        unit = scraper.get_unit(db.session.execute(db.select(Dictionary).where(Dictionary.name == dictionary_name)).scalar(),
                                text,
                                get_language(db.session()).params(name='english').scalar())
        if unit is not None:
            db.session.add(unit)
            db.session.commit()
    return jsonify(unit)


@bp.route('/<uuid:uuid>', methods=['GET'])
def unit_by_id(uuid: UUID) -> str:
    unit = db.get_or_404(Unit, uuid)
    return jsonify(unit)
