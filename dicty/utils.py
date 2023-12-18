def clean_str(s: str, rubbish: str = '[],()'):
    for i in rubbish:
        s = s.translate(str.maketrans({i: None}))
    return s.strip()


def normalize_str(s: str):
    return clean_str(s).lower()
