from mypy_extensions import TypedDict
from typing import List, Tuple, NamedTuple
import pytest


class Aclass():
    a: int
    b: str

    def __init__(self, a, b):
        self.a = a
        self.b = b


class AbDict(TypedDict):
    a: int
    values: List[Tuple[str, str]]


def add1(a: int, b: int):
    return a + b


class AbTuple(NamedTuple):
    a: int
    values: List[Tuple[str, str]]

    @property
    def ab(self):
        return self.a


class TestTypedDict(object):

    def test_typed_dict(self):
        ab: AbDict = AbDict(a=5, values=[])
        assert ab
        assert add1('a', 'b') == 'ab'

    def test_named_tuple(self):
        with pytest.raises(TypeError):
            AbTuple(b=5)

    def test_property(self):
        ab = AbTuple(a=1, values=[])
        assert ab.ab == 1

    def test_a_class(self):
        a1 = Aclass(a=1, b=2)
        a2 = Aclass(a=2, b=3)
        a3 = Aclass(3, 4)

        assert a1.a == 1
        assert a2.a == 2
        assert a3.a == 3

        a1.ab = 55
        assert a1.ab == 55
