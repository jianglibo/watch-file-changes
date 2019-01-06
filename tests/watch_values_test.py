
from pathlib import Path

import pytest

from wfc.dir_watcher.watch_values import WatchPath

from .shared_fort import tmppath  # NOQA


class TestWatchValues(object):
    def test_watch_path(self):
        with pytest.raises(TypeError, match='missing 6 required') as te:
            WatchPath("")
            print(te)
        with pytest.raises(TypeError, match='missing 4 required') as te:
            WatchPath("", regexes=[], ignore_regexes=[])

    def test_property(self, tmppath: Path):  # NOQA
        tmppath.joinpath('a.txt').write_text('abc')
        tmppath.joinpath('b.txt').write_text('abc')
        wp: WatchPath = WatchPath(regexes=[],
                                  ignore_regexes=['.*'],
                                  case_sensitive=False,
                                  path=tmppath,
                                  recursive=True,
                                  ignore_directories=True)
        assert wp
        assert len(list(tmppath.iterdir())) == 2
        wp.compile_re()
        assert wp.regexes == []
        assert wp.ignore_regexes == ['.*']
        assert wp._regexes == []
        assert type(wp._ignore_regexes[0]) != str
