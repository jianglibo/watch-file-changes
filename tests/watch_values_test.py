
import pytest
from .shared_fort import tmppath
from vedis import Vedis

import re
from pathlib import Path
from wfc.dir_watcher.watch_values import FileChange, WatchPath, \
    decode_file_change, encode_file_change


class TestWatchValues(object):
    def test_watch_path(self):
        with pytest.raises(TypeError, match='missing 6 required') as te:
            WatchPath("")
            print(te)
        with pytest.raises(TypeError, match='missing 4 required') as te:
            WatchPath("", regexes=[], ignore_regexes=[])

    def test_property(self, tmppath: Path):  # NOQA pylint: disable=W0621
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
        assert wp._regexes == []  # pylint: disable=W0212
        assert not isinstance(wp._ignore_regexes[0], str)  # pylint: disable=W0212

    def test_vedis_value(self):
        db: Vedis = Vedis(':mem:')
        list_name = 'a-list'
        db.lpush(list_name, b'abc\x00bbb')
        values = list(db.List(list_name))
        assert values[0] != b'abc\x00bbb'
        assert values[0] == b'abc'  # truncated


    def test_file_change_eq(self):  # pylint: disable=W0621
        fc = FileChange('abc', 1, 66.66, 55, 33.33)
        fc1 = FileChange('abc', 1, 66.66, 55, 33.33)
        assert fc == fc1
        fc1 = FileChange('abc', 1, 66.66, 55, 33.34)
        assert fc == fc1
        fc1 = FileChange('abc', 1, 66.66, 56, 33.34)
        assert fc != fc1
        fc1 = FileChange('abc', 1, 66.64, 55, 33.34)
        assert fc != fc1


    def test_file_change_to_str(self):
        fc = FileChange('abc', 1, 66.66, 55)
        assert re.match(r'abc\|1\|66.66\|55\|\d+\.\d+', str(fc))
        fc = FileChange(r'abc', 1, 66.66, 55, None)
        assert re.match(r'abc\|1\|66.66\|55\|', str(fc))
        fc = FileChange(r'abc', 1, 66.66, 55, '')
        assert re.match(r'abc\|1\|66.66\|55\|', str(fc))
        fc = FileChange(r'abc', 1, 66.66, 55, 'xx')
        assert re.match(r'abc\|1\|66.66\|55\|xx', str(fc))

        fc = decode_file_change('abc|1|66.66|55|33.33|xx')
        assert fc.fn == 'abc'
        assert fc.ct == 1
        assert fc.mt == 66.66
        assert fc.size == 55
        assert fc.ts == 33.33
        assert fc.cv == 'xx'

        fc = decode_file_change(b'abc|1|66.66|55|33.33|xx')
        assert fc.fn == 'abc'
        assert fc.ct == 1
        assert fc.mt == 66.66
        assert fc.size == 55
        assert fc.ts == 33.33
        assert fc.cv == 'xx'

        fc = decode_file_change('abc|1|66.66|55|33.33|')
        assert fc.fn == 'abc'
        assert fc.ct == 1
        assert fc.mt == 66.66
        assert fc.size == 55
        assert fc.ts == 33.33
        assert fc.cv == ''

        fc = decode_file_change(b'abc|1|66.66|55|33.33|')
        assert fc.fn == 'abc'
        assert fc.ct == 1
        assert fc.mt == 66.66
        assert fc.size == 55
        assert fc.ts == 33.33
        assert fc.cv == ''
