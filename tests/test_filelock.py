import time
from typing import Tuple

from filelock import FileLock, Timeout

import threading
from pathlib import Path
# very strange thing. If import name contains 'lock', it will failed.
from .shared_fort import file_pair  # pylint: disable=W0611
import pytest



class TestFileLock():
    def test_acquire(self, file_pair: Tuple[Path, Path]):  # pylint: disable=W0621
        f: Path = file_pair[0]
        f_lock: Path = file_pair[1]
        # lock = FileLock(f_lock, timeout=1)

        def a_thread():
            with FileLock(f_lock, timeout=1):
                time.sleep(3)

        t = threading.Thread(target=a_thread)
        t.start()
        with pytest.raises(Timeout):
            with FileLock(f_lock, timeout=1):
                pass
        t.stop()
