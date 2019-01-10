import threading
import time
from pathlib import Path
from typing import Tuple

import pytest
from filelock import FileLock, Timeout

# very strange thing. If import name contains 'lock', it will failed.
from .shared_fort import file_pair  # pylint: disable=W0611


class TestFileLock():
    def test_acquire(self, file_pair: Tuple[Path, Path]):  # pylint: disable=W0621
        f: Path = file_pair[0]
        f_lock: Path = file_pair[1]
        # lock = FileLock(f_lock, timeout=1)

        def a_thread():
            with FileLock(f_lock, timeout=1):
                time.sleep(4)

        t = threading.Thread(target=a_thread)
        t.start()
        with pytest.raises(Timeout):
            with FileLock(f_lock, timeout=1):
                pass

        t1 = int(time.time())
        with FileLock(f_lock):  # it's blocked.
            t2 = int(time.time())
            assert t2 - t1 > 2
        time.sleep(0.2)
