from typing import Callable, Sequence, Sized, TypeVar

from ..core import ParseFn, RecoveryMode
from ..result import Error, Insert, Ok, Recovered, Repair, Result, Skip

T = TypeVar("T")


def eof() -> ParseFn[Sized, int, None]:
    def eof(stream: Sized, pos: int, rm: RecoveryMode) -> Result[int, None]:
        if pos == len(stream):
            return Ok(None, pos)
        if rm:
            skip = len(stream) - pos
            return Recovered(
                {
                    len(stream): Repair(
                        skip, None, Skip(skip, pos), ["end of file"]
                    )
                },
                pos, ["end of file"]
            )
        return Error(pos, ["end of file"])

    return eof


def satisfy(test: Callable[[T], bool]) -> ParseFn[Sequence[T], int, T]:
    def satisfy(
            stream: Sequence[T], pos: int, rm: RecoveryMode) -> Result[int, T]:
        if pos < len(stream):
            t = stream[pos]
            if test(t):
                return Ok(t, pos + 1, consumed=True)
        if rm:
            cur = pos + 1
            while cur < len(stream):
                t = stream[cur]
                if test(t):
                    skip = cur - pos
                    return Recovered(
                        {cur + 1: Repair(skip, t, Skip(skip, pos))}, pos
                    )
                cur += 1
        return Error(pos)

    return satisfy


def sym(s: T) -> ParseFn[Sequence[T], int, T]:
    rs = repr(s)
    expected = [rs]

    def sym(stream: Sequence[T], pos: int, rm: RecoveryMode) -> Result[int, T]:
        if pos < len(stream):
            t = stream[pos]
            if t == s:
                return Ok(t, pos + 1, consumed=True)
        if rm:
            reps = {pos: Repair(1, s, Insert(rs, pos), expected)}
            cur = pos + 1
            while cur < len(stream):
                t = stream[cur]
                if t == s:
                    skip = cur - pos
                    reps[cur + 1] = Repair(skip, t, Skip(skip, pos), expected)
                    return Recovered(reps, pos, expected)
                cur += 1
            return Recovered(reps, pos, expected)
        return Error(pos, expected)

    return sym