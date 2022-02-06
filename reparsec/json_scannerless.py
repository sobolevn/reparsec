import re
from typing import Match

from .parser import Delay, Parser, eof, insert, prefix, regexp, run

escape = re.compile(r"""
\\(?:(?P<simple>["\\/bfnrt])|u(?P<unicode>[0-9a-fA-F]{4}))
""", re.VERBOSE)

simple = {
    '"': '"', "\\": "\\", "/": "/",
    "b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t"
}


def unescape(s: str) -> str:
    def sub(m: Match[str]) -> str:
        if m.lastgroup == "unicode":
            return chr(int(m.group("unicode"), 16))
        return simple[m.group("simple")]

    return escape.sub(sub, s)


ows = regexp(r"[ \n\r\t]*")


def token(pat: str) -> Parser[str, int, str]:
    return regexp(r"[ \n\r\t]*" + pat, 1)


def punct(p: str) -> Parser[str, int, str]:
    return (ows >> prefix(p)).attempt()


JsonParser = Parser[str, int, object]

value: Delay[str, int, object] = Delay()

string: JsonParser = token(
    r'"(?P<string>(?:[\x20\x21\x23-\x5B\x5D-\U0010FFFF]|'
    r'\\(?:["\\/bfnrt]|u[0-9a-fA-F]{4}))+)"'
).label("string").fmap(unescape)
integer: JsonParser = token(
    r"(-?(?:0|[1-9][0-9]*))").label("integer").fmap(int)
number: JsonParser = token(
    r"(-?(?:0|[1-9][0-9]*)(?:(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)|(?:\.[0-9]+)))"
).label("number").fmap(float)
boolean: JsonParser = token(r"(true|false)").label("bool").fmap(
    lambda s: s == "true")
null: JsonParser = token(r"(null)").label("null").fmap(lambda _: None)
json_dict: JsonParser = (
    ((string | insert("a")) << punct(":")) + value
).sep_by(punct(",")).fmap(lambda v: dict(v)).between(
    punct("{"), punct("}")
).label("object")
json_list: JsonParser = value.sep_by(punct(",")).between(
    punct("["), punct("]")
).label("list")

value.define(
    (
        number | integer | boolean | null | string | insert(1)
        | json_dict | json_list
    ).label("value")
)

json = value << ows << eof()


def parse(src: str) -> object:
    return run(json, src).unwrap()
