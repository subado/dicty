from typing import Callable, TypeVar, ParamSpec, Optional


def clean_str(s: str, rubbish: str = '[],()') -> str:
    for i in rubbish:
        s = s.translate({ord(i): None})
    return s.strip()


def normalize_str(s: str) -> str:
    return clean_str(s).lower()


P = ParamSpec('P')
R = TypeVar('R')
E = TypeVar('E', bound=BaseException)
T = TypeVar('T')


def catch(*e: type[E]) -> Callable[[Callable[P, R]], Callable[P, R | E]]:
    def wrapper(f: Callable[P, R]) -> Callable[P, R | E]:
        def inner(*args: P.args, **kwargs: P.kwargs) -> R | E:
            try:
                return f(*args, **kwargs)
            except e as exception:
                return exception
        return inner
    return wrapper


def ignore_exception(*e: type[E]) -> Callable[[Callable[P, R]], Callable[P, Optional[R]]]:
    def wrapper(f: Callable[P, R]) -> Callable[P, Optional[R]]:
        def inner(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
            try:
                return f(*args, **kwargs)
            except e:
                return None
        return inner
    return wrapper
