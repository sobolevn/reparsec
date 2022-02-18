from typing import Callable, Sequence, Sized, TypeVar

from ..core import ParseFn, RecoveryMode
from ..result import Error, Insert, Ok, Recovered, Repair, Result, Skip
from ..state import Ctx

T = TypeVar("T")
C = TypeVar("C", bound=object)


def eof() -> ParseFn[Sized, None]:
    def eof(
            stream: Sized, pos: int, ctx: Ctx[Sized],
            rm: RecoveryMode) -> Result[None, Sized]:
        if pos == len(stream):
            return Ok(None, pos, ctx)
        loc = ctx.get_loc(stream, pos)
        if rm:
            skip = len(stream) - pos
            return Recovered(
                {
                    len(stream): Repair(
                        skip, None, ctx, Skip(skip, loc), ["end of file"]
                    )
                },
                pos, loc, ["end of file"]
            )
        return Error(pos, loc, ["end of file"])

    return eof


def satisfy(test: Callable[[T], bool]) -> ParseFn[Sequence[T], T]:
    def satisfy(
            stream: Sequence[T], pos: int, ctx: Ctx[Sequence[T]],
            rm: RecoveryMode) -> Result[T, Sequence[T]]:
        if pos < len(stream):
            t = stream[pos]
            if test(t):
                return Ok(t, pos + 1, ctx, consumed=True)
        loc = ctx.get_loc(stream, pos)
        if rm:
            cur = pos + 1
            while cur < len(stream):
                t = stream[cur]
                if test(t):
                    skip = cur - pos
                    return Recovered(
                        {
                            cur + 1: Repair(
                                skip, t, ctx.update_loc(stream, cur+1),
                                Skip(skip, loc)
                            )
                        },
                        pos, loc
                    )
                cur += 1
        return Error(pos, loc)

    return satisfy


def sym(s: T) -> ParseFn[Sequence[T], T]:
    rs = repr(s)
    expected = [rs]

    def sym(
            stream: Sequence[T], pos: int, ctx: Ctx[Sequence[T]],
            rm: RecoveryMode) -> Result[T, Sequence[T]]:
        if pos < len(stream):
            t = stream[pos]
            if t == s:
                return Ok(t, pos + 1, ctx, consumed=True)
        loc = ctx.get_loc(stream, pos)
        if rm:
            reps = {pos: Repair(1, s, ctx, Insert(rs, loc), expected)}
            cur = pos + 1
            while cur < len(stream):
                t = stream[cur]
                if t == s:
                    skip = cur - pos
                    reps[cur + 1] = Repair(
                        skip, t, ctx.update_loc(stream, cur + 1),
                        Skip(skip, loc), expected
                    )
                    return Recovered(reps, pos, loc, expected)
                cur += 1
            return Recovered(reps, pos, loc, expected)
        return Error(pos, loc, expected)

    return sym
