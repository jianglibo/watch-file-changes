import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple

from py._path.local import LocalPath

import pytest
from wfc.constants import (V_CREATED_SET_TABLE, V_MODIFIED_SET_TABLE,
                           V_STANDARD_HASH_TABLE)
from wfc.dir_watcher.dir_watcher_dog import DirWatchDog
from wfc.my_vedis import DbThread

from .shared_fort import change_folder_path, db_file_path, db_thread  # pylint: disable=W0611


@pytest.fixture(params=[{"tid": 0, "watch_paths": [{
        "regexes": [
            ".*"
        ],
        "ignore_regexes": [
            ".*vedisdb.*"
        ],
        "ignore_directories": True,
        "case_sensitive": False,
        "recursive": True
    }]}])
def dir_watcher(request, db_thread: DbThread, tmpdir: LocalPath):  # pylint: disable=W0621
    watch_paths: List[Dict] = request.param['watch_paths']
    td: LocalPath = tmpdir
    watch_paths[0]['path'] = td.join('dd').mkdir()
    dir_watch_dog = DirWatchDog(watch_paths, db_thread.data_queue)
    yield (db_thread, dir_watch_dog, request.param['tid'], watch_paths)
    dir_watch_dog.stop_watch()


def test_move_from_out_side(dir_watcher: Tuple[DbThread, DirWatchDog, int, List[Dict]]):  # pylint: disable=W0621
    db_thread_1: DbThread = dir_watcher[0]
    db_thread_1.start()

    one_path: Dict = dir_watcher[3][0]
    test_path = Path(one_path['path'])
    dir_watch_dog = dir_watcher[1]
    dir_watch_dog.watch(initialize=True)

    src_path: Path = Path("e:/a_file.txt")
    src_path.write_text("hello")

    shutil.move(src=str(src_path), dst=str(test_path))
    time.sleep(1)  # should wait loop to hit the change.
    db_set = db_thread_1.db.Set(V_MODIFIED_SET_TABLE)
    assert db_set
    changed_list = list(db_set)
    assert len(changed_list) >= 1  # create and change event.
    for file_name in changed_list:
        assert Path(file_name.decode()).exists()
    db_thread_1.data_queue.put(None)
    time.sleep(1)


def test_write_file_multiple(dir_watcher: Tuple[DbThread, DirWatchDog, int, List[Dict]]):  # pylint: disable=W0621
    db_thread_1: DbThread = dir_watcher[0]
    db_thread_1.start()

    one_path: Dict = dir_watcher[3][0]
    test_path = Path(one_path['path'])
    dir_watch_dog = dir_watcher[1]
    dir_watch_dog.watch(initialize=True)

    test_file: Path = test_path.joinpath('he.txt')

    with test_file.open(mode='w') as f: # will not fire multiple change event.
        for _ in range(0, 10):
            f.write('a')
            time.sleep(0.5)
    time.sleep(1)
    changed_list = list(db_thread_1.db.Set(V_MODIFIED_SET_TABLE))
    assert len(changed_list) == 1  # create and change event.

    with test_file.open() as f:
        v = f.read()
        assert len(v) == 10


def test_watch_db(dir_watcher: Tuple[DbThread, DirWatchDog, int, List[Dict]]):  # pylint: disable=W0621
    db_thread_1: DbThread = dir_watcher[0]
    db_thread_1.start()

    one_path: Dict = dir_watcher[3][0]
    test_path = Path(one_path['path'])

    test_path.joinpath('he0.txt').write_text("abc")
    test_path.joinpath('he1.txt').write_text("abc")
    test_path.joinpath('he2.txt').write_text("abc")

    dir_watch_dog = dir_watcher[1]
    dir_watch_dog.watch(initialize=True)

    time.sleep(2)
    d = db_thread_1.db.Hash(V_STANDARD_HASH_TABLE)
    assert len(d) == 3
    test_file = test_path.joinpath('he.txt')
    test_file.write_text("abc")
    time.sleep(1)
    changed_list = list(db_thread_1.db.Set(V_MODIFIED_SET_TABLE))
    for file_name in changed_list:
        assert Path(file_name.decode()).exists()
    assert len(changed_list) == 1

    assert db_thread_1.db.hlen(V_STANDARD_HASH_TABLE) == 4
    assert db_thread_1.db.scard(V_CREATED_SET_TABLE) == 1
    assert db_thread_1.db.scard(V_MODIFIED_SET_TABLE) == 1

    test_file.unlink()
    time.sleep(1)
    assert db_thread_1.db.hlen(V_STANDARD_HASH_TABLE) == 3
    assert db_thread_1.db.scard(V_CREATED_SET_TABLE) == 0
    assert db_thread_1.db.scard(V_MODIFIED_SET_TABLE) == 1
