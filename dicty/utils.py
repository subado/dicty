from typing import Callable, TypeVar, ParamSpec, Optional


def clean_str(s: str, rubbish: str = '[],()') -> str:
    for i in rubbish:
        s = s.translate({ord(i): None})
    return s.strip()


def normalize_str(s: str) -> str:
    return clean_str(s).lower()


def add_tabs(s: str, n: int = 1, sep: str = '\n') -> str:
    lines = s.split(sep=sep)
    for i in range(len(lines)):
        lines[i] = '\t' + lines[i]
    return sep.join(lines)


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


def convert(converter: Callable[[R], T]) -> Callable[[Callable[P, R]], Callable[P, T]]:
    def wrapper(f: Callable[P, R]) -> Callable[P, T]:
        def inner(*args: P.args, **kwargs: P.kwargs) -> T:
            return converter(f(*args, **kwargs))
        return inner
    return wrapper


def not_none(x: Optional[T]) -> T:
    assert x is not None
    return x
