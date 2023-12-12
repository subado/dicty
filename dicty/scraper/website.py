class Selectors:
    def __init__(self, load_persuader: str, search_field: str):
        self.load_persuader = load_persuader
        self.search_field = search_field


class Website:
    def __init__(self, name: str, url: str, timeout: float, language_code: str, selectors: Selectors):
        self.name = name
        self.url = url
        self.timeout = timeout
        # this code should be alpha_3 of one of pycountry.languages
        self.language_code = language_code
        self.selectors = selectors
