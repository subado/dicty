from typing import Callable, TypeVar, ParamSpec, Optional


def clean_str(s: str, rubbish: str = '[],()'):
    for i in rubbish:
        s = s.translate({ord(i): None})
    return s.strip()


def normalize_str(s: str):
    return clean_str(s).lower()


P = ParamSpec('P')
R = TypeVar('R')
E = TypeVar('E', bound=BaseException)


def handle_exception(e: type[E], handler: Optional[Callable[[E], Optional[R]]] = None) -> Callable[
        [Callable[P, R]], Callable[P, Optional[R]]]:
    def wrapper(f: Callable[P, R]) -> Callable[P, Optional[R]]:
        def inner(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
            try:
                return f(*args, **kwargs)
            except e as exception:
                return handler(exception) if handler is not None else None
        return inner
    return wrapper
