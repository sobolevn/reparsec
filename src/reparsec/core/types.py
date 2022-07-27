from typing import Callable, Generic, NamedTuple, Tuple, TypeVar, Union

from typing_extensions import Literal

S = TypeVar("S")
S_contra = TypeVar("S_contra", contravariant=True)
V = TypeVar("V")
V_co = TypeVar("V_co", covariant=True)


class Loc(NamedTuple):
    pos: int
    line: int
    col: int


class Ctx(Generic[S_contra]):
    __slots__ = "anchor", "loc", "rs", "_get_loc"

    def __init__(
            self, anchor: int, loc: Loc, rs: Tuple[int],
            get_loc: Callable[[Loc, S_contra, int], Loc]):
        self.anchor = anchor
        self.loc = loc
        self.rs = rs
        self._get_loc = get_loc

    def get_loc(self, stream: S_contra, pos: int) -> Loc:
        return self._get_loc(self.loc, stream, pos)

    def update_loc(self, stream: S_contra, pos: int) -> "Ctx[S_contra]":
        if pos == self.loc.pos:
            return self
        return Ctx(
            self.anchor, self._get_loc(self.loc, stream, pos), self.rs,
            self._get_loc
        )

    def set_anchor(self, anchor: int) -> "Ctx[S_contra]":
        return Ctx(anchor, self.loc, self.rs, self._get_loc)


RecoveryState = Union[Literal[None, False], Tuple[int]]


def disallow_recovery(rs: RecoveryState) -> RecoveryState:
    if rs is None:
        return None
    return False


def maybe_allow_recovery(
        ctx: Ctx[S], rs: RecoveryState, consumed: bool) -> RecoveryState:
    if rs is False and consumed:
        return ctx.rs
    return rs
