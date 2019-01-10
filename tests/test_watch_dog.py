import time
from typing import Dict, List, Tuple

import pytest
from .shared_fort import change_folder_path, db_file_path, db_thread  # pylint: disable=W0611
from py._path.local import LocalPath

import shutil
from pathlib import Path
from wfc.constants import V_CREATED_SET_TABLE, V_MODIFIED_SET_TABLE, \
    V_STANDARD_HASH_TABLE
from wfc.dir_watcher.dir_watcher_dog import DirWatchDog
from wfc.dir_watcher.watch_values import FileChange, decode_file_change
from wfc.my_vedis import DbThread


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
    dir_watch_dog = DirWatchDog(watch_paths, db_thread.que)
    yield (db_thread, dir_watch_dog, request.param['tid'], watch_paths)
    dir_watch_dog.stop_watch()


class TestWatchDog():
    def test_move_from_out_side(self, dir_watcher: Tuple[DbThread, DirWatchDog, int, List[Dict]]):  # pylint: disable=W0621
        """When move file from outside into monitored folder what happen?
        Should got 1 V_MODIFIED_SET_TABLE, 1 V_CREATED_SET_TABLE
        """
        db_thread_1: DbThread = dir_watcher[0]
        db_thread_1.start()

        one_path: Dict = dir_watcher[3][0]
        test_path = Path(one_path['path'])

        dir_watch_dog = dir_watcher[1]
        dir_watch_dog.watch(initialize=True)

        # create a file out of monitored folder and move into folder.
        src_path: Path = Path("e:/a_file.txt")
        src_path.write_text("hello")
        shutil.move(src=str(src_path), dst=str(test_path))

        time.sleep(0.5)  # should wait loop to hit the change.
        changed_db_set = db_thread_1.db.Set(V_MODIFIED_SET_TABLE)
        assert len(changed_db_set) == 1

        for file_name in changed_db_set:
            assert Path(file_name.decode()).exists()

        created_db_set = db_thread_1.db.Set(V_CREATED_SET_TABLE)
        assert len(created_db_set) == 1

        for file_name in created_db_set:
            assert Path(file_name.decode()).exists()

        db_thread_1.que.put(None)
        time.sleep(1)


    def test_write_file_multiple(self, dir_watcher: Tuple[DbThread, DirWatchDog, int, List[Dict]]):  # pylint: disable=W0621
        """When does the file change event fired?
        when it's be closed.
        """
        db_thread_1: DbThread = dir_watcher[0]
        db_thread_1.start()

        one_path: Dict = dir_watcher[3][0]
        test_path = Path(one_path['path'])
        dir_watch_dog = dir_watcher[1]
        dir_watch_dog.watch(initialize=True)

        test_file_path: Path = test_path.joinpath('he.txt')

        with test_file_path.open(mode='w') as f: # will not fire multiple change event.
            for _ in range(0, 10):
                f.write('a')
                time.sleep(0.2)
        now = int(time.time())
        time.sleep(0.5)
        standard_file = db_thread_1.db.hget(V_STANDARD_HASH_TABLE, str(test_file_path))
        fc: FileChange = decode_file_change(standard_file)
        assert int(fc.ts) == now  # change happened at file's closing point.
        time.sleep(0.5)
        count = int(db_thread_1.db.get(str(test_file_path)))
        assert count == 1  # only change once.
        changed_list = list(db_thread_1.db.Set(V_MODIFIED_SET_TABLE))
        assert len(changed_list) == 1  # create and change event.

        with test_file_path.open() as f:
            v = f.read()
            assert len(v) == 10


    def test_watch_db(self, dir_watcher: Tuple[DbThread, DirWatchDog, int, List[Dict]]):  # pylint: disable=W0621
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
        assert len(d) == 3  # should stat existed files.

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

        test_file.unlink()  # delete file.
        time.sleep(1)
        assert db_thread_1.db.hlen(V_STANDARD_HASH_TABLE) == 3
        assert db_thread_1.db.scard(V_CREATED_SET_TABLE) == 0
        assert db_thread_1.db.scard(V_MODIFIED_SET_TABLE) == 1
