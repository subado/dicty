from uuid import UUID

from flask import Blueprint, jsonify

from ..db import db
from ..db.models import Dictionary

bp = Blueprint('dictionaries', __name__, url_prefix='/dictionaries')


@bp.route('/<uuid:uuid>', methods=['GET'])
def dictionary_by_id(uuid: UUID) -> str:
    dictionary = db.get_or_404(Dictionary, uuid)
    return jsonify(dictionary)


@bp.route('/<name>', methods=['GET'])
def dictionary(name: str):
    dictionary = db.one_or_404(
        db.select(Dictionary)
        .where(Dictionary.name == name)
    )
    return jsonify(dictionary)


@bp.route('/', methods=['GET'])
def dictionaries():
    dictionaries = db.session.execute(
        db.select(Dictionary)
        .order_by(Dictionary.name)
    ).scalars().all()
    return jsonify(dictionaries)
