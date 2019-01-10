import time
from typing import List

from .shared_fort import tmppath

import re
from pathlib import Path
from wfc import dir_util
from wfc.dir_util import list_dir_order_by_digits


class TestDir():
    def test_list_file(self, tmppath: Path):  # pylint: disable=W0621
        f0 = tmppath.joinpath('0.txt')
        f1 = tmppath.joinpath('1.txt')
        f2 = tmppath.joinpath('2.txt')
        f3 = tmppath.joinpath('3.txt')
        f10 = tmppath.joinpath('10.txt')
        assert not f1.exists()
        for f in [f1, f3, f2, f0, f10]:
            f.write_text('hello')
            time.sleep(1)

        assert '2.txt' > '10.txt'

        files: List[Path] = list(tmppath.iterdir())
        assert isinstance(files[0], Path)
        #  iterdir default order by file name.
        assert [f.name for f in files] == ['0.txt', '1.txt', '10.txt', '2.txt', '3.txt']
        # but *, ?, and character ranges expressed with [] will be correctly matched
        # g_files: List[Path] = list(tmppath.glob('[0-9].txt'))
        # assert [f.name for f in g_files] == ['0.txt', '1.txt', '10.txt', '2.txt', '3.txt']

        files = list(filter(lambda f: re.match(r'\d+\.txt$', f.name), tmppath.iterdir()))
        assert isinstance(files, list)
        digits_in_name_re = re.compile(r'(\d+)\.txt$')
        def custom_sort(item: Path):
            m = digits_in_name_re.match(item.name)
            if m is not None:
                return int(m.group(1))
            return 0
        files.sort(key=custom_sort)

        assert [f.name for f in files] == ['0.txt', '1.txt', '2.txt', '3.txt', '10.txt']

        files = dir_util.list_dir_order_by_digits(tmppath)
        assert [f.name for f in files] == ['0.txt', '1.txt', '2.txt', '3.txt', '10.txt']

        assert files[0].name == '0.txt'
        assert files[-1].name == '10.txt'
