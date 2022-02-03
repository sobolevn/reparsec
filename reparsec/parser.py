from typing import (
    AnyStr, Callable, List, Optional, Sequence, Sized, Tuple, TypeVar, Union
)

from . import core, scannerless, sequence
from .core import ParseFn, ParseObj, RecoveryMode
from .result import Result

T = TypeVar("T", bound=object)
S = TypeVar("S", bound=object)
S_contra = TypeVar("S_contra", contravariant=True)
V = TypeVar("V", bound=object)
V_co = TypeVar("V_co", covariant=True)
U = TypeVar("U", bound=object)
X = TypeVar("X", bound=object)


class Parser(ParseObj[S_contra, V_co]):
    def parse(self, stream: S_contra, recover: bool = False) -> Result[V_co]:
        return self.parse_fn(stream, 0, True if recover else None)

    def fmap(self, fn: Callable[[V_co], U]) -> "Parser[S_contra, U]":
        return FnParser(core.fmap(self.to_fn(), fn))

    def bind(
            self, fn: Callable[[V_co], ParseObj[S_contra, U]]
    ) -> "Parser[S_contra, U]":
        return bind(self, fn)

    def lseq(self, other: ParseObj[S_contra, U]) -> "Parser[S_contra, V_co]":
        return lseq(self, other)

    def rseq(self, other: ParseObj[S_contra, U]) -> "Parser[S_contra, U]":
        return rseq(self, other)

    def __lshift__(
            self, other: ParseObj[S_contra, U]) -> "Parser[S_contra, V_co]":
        return lseq(self, other)

    def __rshift__(
            self, other: ParseObj[S_contra, U]) -> "Parser[S_contra, U]":
        return rseq(self, other)

    def __add__(
            self, other: ParseObj[S_contra, U]
    ) -> "Parser[S_contra, Tuple[V_co, U]]":
        return seq(self, other)

    def __or__(
            self,
            other: ParseObj[S_contra, V_co]) -> "Parser[S_contra, V_co]":
        return FnParser(core.or_(self.to_fn(), other.to_fn()))

    def maybe(self) -> "Parser[S_contra, Optional[V_co]]":
        return maybe(self)

    def many(self) -> "Parser[S_contra, List[V_co]]":
        return many(self)

    def label(self, expected: str) -> "Parser[S_contra, V_co]":
        return label(self, expected)

    def sep_by(
            self,
            sep: "Parser[S_contra, U]") -> "Parser[S_contra, List[V_co]]":
        return sep_by(self, sep)

    def between(
            self, open: "Parser[S_contra, U]",
            close: "Parser[S_contra, X]") -> "Parser[S_contra, V_co]":
        return between(open, close, self)


class FnParser(Parser[S_contra, V_co]):
    def __init__(self, fn: ParseFn[S_contra, V_co]):
        self._fn = fn

    def to_fn(self) -> ParseFn[S_contra, V_co]:
        return self._fn

    def parse_fn(
            self, stream: S_contra, pos: int,
            rm: RecoveryMode) -> Result[V_co]:
        return self._fn(stream, pos, rm)


def bind(
        parser: ParseObj[S, V],
        fn: Callable[[V], ParseObj[S, U]]) -> Parser[S, U]:
    return FnParser(core.bind(parser.to_fn(), fn))


def lseq(parser: ParseObj[S, V], second: ParseObj[S, U]) -> Parser[S, V]:
    return FnParser(core.lseq(parser.to_fn(), second.to_fn()))


def rseq(parser: ParseObj[S, V], second: ParseObj[S, U]) -> Parser[S, U]:
    return FnParser(core.rseq(parser.to_fn(), second.to_fn()))


def seq(
        parser: ParseObj[S, V],
        second: ParseObj[S, U]) -> Parser[S, Tuple[V, U]]:
    return FnParser(core.seq(parser.to_fn(), second.to_fn()))


class Pure(core.Pure[S, V_co], Parser[S, V_co]):
    pass


pure = Pure


class PureFn(core.PureFn[S, V_co], Parser[S, V_co]):
    pass


pure_fn = PureFn


class Eof(sequence.Eof, Parser[Sized, None]):
    pass


eof = Eof


def satisfy(test: Callable[[T], bool]) -> Parser[Sequence[T], T]:
    return FnParser(sequence.satisfy(test))


def sym(s: T) -> Parser[Sequence[T], T]:
    return FnParser(sequence.sym(s))


def maybe(parser: ParseObj[S, V]) -> Parser[S, Optional[V]]:
    return FnParser(core.maybe(parser.to_fn()))


def many(parser: ParseObj[S, V]) -> Parser[S, List[V]]:
    return FnParser(core.many(parser.to_fn()))


def label(parser: ParseObj[S, V], x: str) -> Parser[S, V]:
    return FnParser(core.label(parser.to_fn(), x))


class RecoverValue(core.RecoverValue[S, V_co], Parser[S, V_co]):
    pass


recover_value = RecoverValue


class RecoverFn(core.RecoverFn[S, V_co], Parser[S, V_co]):
    pass


recover_fn = RecoverFn


class Delay(core.Delay[S, V_co], Parser[S, V_co]):
    def define(self, parser: ParseObj[S, V_co]) -> None:
        self.define_fn(parser.to_fn())


def prefix(s: AnyStr) -> Parser[AnyStr, AnyStr]:
    return FnParser(scannerless.prefix(s))


def regexp(pat: AnyStr, group: Union[int, str] = 0) -> Parser[AnyStr, AnyStr]:
    return FnParser(scannerless.regexp(pat, group))


def sep_by(parser: ParseObj[S, V], sep: ParseObj[S, U]) -> Parser[S, List[V]]:
    return maybe(seq(parser, many(rseq(sep, parser)))).fmap(
        lambda v: [] if v is None else [v[0]] + v[1]
    )


def between(
        open: ParseObj[S, U], close: ParseObj[S, X],
        parser: ParseObj[S, V]) -> Parser[S, V]:
    return rseq(open, lseq(parser, close))


letter: Parser[Sequence[str], str] = satisfy(str.isalpha).label("letter")
digit: Parser[Sequence[str], str] = satisfy(str.isdigit).label("digit")