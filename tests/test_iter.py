

from typing import Iterable, List


class TestMyIter:
    def test_empty_iter(self):
        r = range(0, 10)
        assert isinstance(r, Iterable)
        assert isinstance(r, range)
        assert len(r) == 10

        filtered = filter(lambda x: x > 20, r)

        assert filtered  #empty filtered is true.

        assert not list(filtered)

        assert not bool(0)
        assert not bool('')
        assert bool('0')
        assert bool(1)

        assert not bool(())
        assert not bool([])

        assert isinstance((), tuple)

        assert not []
        assert not ()
