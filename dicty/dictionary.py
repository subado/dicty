from .database import Database


class Dictionary:
    def __init__(self) -> None:
        self.db = Database('dictionary')
