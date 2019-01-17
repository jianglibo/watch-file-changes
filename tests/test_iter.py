

from typing import Iterable, List


class TestMyIter:
    def test_empty_iter(self):
        r = range(0, 10)
        assert isinstance(r, Iterable)
        print(type(r))
        assert isinstance(r, List)
        assert len(r)


