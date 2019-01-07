import json
import time
from os import stat_result
from pathlib import Path
from queue import Queue
from typing import Dict, List, Tuple

from flask import Response
from py._path.local import LocalPath

import pytest
import wfc
from vedis import Vedis
from wfc.constants import V_CHANGED_LIST_TABLE
from wfc.dir_watcher.dir_watcher_dog import DirWatchDog
from wfc.dir_watcher.watch_values import FileChange, decode_file_change
from wfc.my_vedis import V_STANDARD_HASH_TABLE, BatchProcessThread, DbThread


@pytest.fixture
def client():
    app = wfc.create_app()
    app.config['TESTING'] = True
    c = app.test_client()
    yield c


@pytest.fixture
def vdb(db_file_path: Path):  # pylint: disable=W0621
    db: Vedis = Vedis(str(db_file_path))
    yield db
    db.close()


@pytest.fixture
def db_file_path(tmpdir: LocalPath):
    db_file: Path = Path(str(tmpdir.join('x1.vdb')))
    yield db_file
    if db_file.exists():
        db_file.unlink()


@pytest.fixture
def db_thread(db_file_path: Path):  # pylint: disable=W0621
    data_queue: Queue = Queue()
    batch_queue: Queue = Queue()
    dbt: DbThread = DbThread(str(db_file_path), data_queue, batch_queue)
    yield dbt
    dbt.file_change_queue.put(None)


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
    dir_watch_dog = DirWatchDog(watch_paths, db_thread.file_change_queue)
    bpt: BatchProcessThread = BatchProcessThread(db_thread.batch_file_change_queue)
    yield (db_thread, dir_watch_dog, request.param['tid'], watch_paths, bpt)
    dir_watch_dog.stop_watch()
    bpt.batch_file_change_queue.put(None)


def test_open_vedis(vdb: Vedis):  # pylint: disable=W0621
    with vdb.transaction():
        h: Dict = vdb.Hash('a-hash')
        h['abc'] = 55
        vdb.commit()
    v: str = vdb.hget('a-hash', 'abc')
    assert int(v) == 55


def test_queue_db(db_thread: DbThread):  # pylint: disable=W0621
    data_queue = db_thread.file_change_queue
    db_thread.start()
    for i in range(0, 10):
        data_queue.put('abc%s' % i)
    data_queue.join()
    data_queue.put(None)
    assert db_thread.db.llen(V_CHANGED_LIST_TABLE) == 10


def test_watch_db(dir_watcher: Tuple[DbThread, DirWatchDog, int, List[Dict], BatchProcessThread]):  # pylint: disable=W0621
    db_thread_1: DbThread = dir_watcher[0]
    db_thread_1.start()

    one_path: Dict = dir_watcher[3][0]
    test_path = Path(one_path['path'])

    test_path.joinpath('he0.txt').write_text("abc")
    test_path.joinpath('he1.txt').write_text("abc")
    test_path.joinpath('he2.txt').write_text("abc")

    dir_watch_dog = dir_watcher[1]
    dir_watch_dog.watch(initialize=True)

    d = db_thread_1.db.Hash(V_STANDARD_HASH_TABLE)
    assert len(d) == 3
    batch_process_thread = dir_watcher[4]
    batch_process_thread.start()
    test_path.joinpath('he.txt').write_text("abc")
    time.sleep(1)
    changed_list = list(db_thread_1.db.List(V_CHANGED_LIST_TABLE))
    for item in changed_list:
        fc: FileChange = decode_file_change(item)
        assert fc.size == 3
    assert len(changed_list) == 2  # create and change event.

    db_thread_1.file_change_queue.put(1)
    time.sleep(0.5)
    changed_list = db_thread_1.db.List(V_CHANGED_LIST_TABLE)
    assert len(changed_list) == 1  # create and change event.

    db_thread_1.file_change_queue.put(1)
    time.sleep(0.5)
    changed_list = db_thread_1.db.List(V_CHANGED_LIST_TABLE)
    assert not changed_list  # create and change event.


def test_file_change_equal(db_file_path: Path):  # pylint: disable=W0621
    db_file_path.write_text('hello')
    stat1: stat_result = db_file_path.stat()
    stat2 = Path(str(db_file_path)).stat()
    assert stat1 == stat2
    db_file_path.read_text()
    time.sleep(0.5)
    stat3 = Path(str(db_file_path)).stat()
    assert stat1 == stat3

    time.sleep(0.5)
    with db_file_path.open(mode='r') as f:
        line = f.read()
        print(line)

    time.sleep(0.5)
    stat4: stat_result = Path(str(db_file_path)).stat()
    assert stat1.st_atime != stat4.st_atime
    assert stat1.st_ctime == stat4.st_ctime
    assert stat1.st_mtime == stat4.st_mtime

    with db_file_path.open(mode='w') as f:
        f.write('hello')

    time.sleep(0.5)
    stat5: stat_result = Path(str(db_file_path)).stat()
    assert stat1.st_atime != stat5.st_atime
    assert stat1.st_ctime == stat5.st_ctime
    assert stat1.st_mtime != stat5.st_mtime
    # st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime


def test_get_modified(client):  # pylint: disable=W0621
    rv: Response = client.get('/vedis/list-created')
    r = json.loads(rv.get_data(as_text=True))
    assert r['values'] == []
