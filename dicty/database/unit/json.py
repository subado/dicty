from json import JSONEncoder
from typing import Any

from . import Unit, Definition, Pronunciation, Meaning, Style, GrammaticalFeature, Form, Language


class Encoder(JSONEncoder):
    def default(self, obj: Any):
        if isinstance(obj, Unit) or isinstance(obj, Pronunciation) or \
                isinstance(obj, Form) or isinstance(obj, Definition) or isinstance(obj, Meaning):
            return obj.__dict__
        elif isinstance(obj, Language):
            return obj.code
        elif isinstance(obj, GrammaticalFeature) or isinstance(obj, Style):
            return obj.text

        return super().default(self, obj)
