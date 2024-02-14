from typing import Any
from .db import db
from flask.json.provider import DefaultJSONProvider


class JsonProvider(DefaultJSONProvider):
    ensure_ascii = False

    @staticmethod
    def default(obj: Any):
        if isinstance(obj, db.Model):
            # go through each field in this SQLalchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and
                          x not in ('metadata', 'query', 'query_class', 'registry') and
                          not x.endswith('_id') and not x.endswith('_code')]:

                val = obj.__getattribute__(field)
                if not callable(val):
                    fields[field] = val

            return fields

        return DefaultJSONProvider.default(obj)
