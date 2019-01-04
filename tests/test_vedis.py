import time
from os import stat_result
from typing import Dict, List, Tuple

import pytest
from flask import Response
from py._path.local import LocalPath
from vedis import Vedis

import json
import wfc
from pathlib import Path
from queue import Queue
from threading import Event
from wfc.constants import V_CHANGED_LIST_TABLE
from wfc.dir_watcher import dir_watcher_entry
from wfc.dir_watcher.dir_watcher_entry import FileChange
from wfc.my_vedis import DbThread


@pytest.fixture
def client():
    app = wfc.create_app()
    app.config['TESTING'] = True
    c = app.test_client()
    yield c


@pytest.fixture
def vdb(db_file_path: Path):
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
def db_thread(db_file_path: Path):
    cease_event: Event = Event()
    data_queue: Queue = Queue()
    dbt: DbThread = DbThread(str(db_file_path), data_queue, cease_event)
    yield dbt
    dbt.data_queue.put(None)
    dbt.cease_event.set()


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
def dir_watcher(request, db_thread: DbThread, tmpdir: LocalPath):
    watch_paths: List[Dict] = request.param['watch_paths']
    td: LocalPath = tmpdir
    watch_paths[0]['path'] = td.join('dd').mkdir()
    dwd = dir_watcher_entry.start_watchdog(watch_paths, db_thread.data_queue)
    yield (db_thread, dwd, request.param['tid'], watch_paths)
    dwd.stop_watch()


def test_open_vedis(vdb: Vedis):
    with vdb.transaction():
        h: Dict = vdb.Hash('a-hash')
        h['abc'] = 55
        vdb.commit()
    v: bytes = vdb.hget('a-hash', 'abc')
    assert int(v) == 55


def test_queue_db(db_thread: DbThread):
    data_queue = db_thread.data_queue
    db_thread.start()
    for i in range(0, 10):
        data_queue.put('abc%s' % i)
    data_queue.join()
    data_queue.put(None)
    assert db_thread.db.llen(V_CHANGED_LIST_TABLE) == 10


def test_watch_db(dir_watcher: Tuple[DbThread, dir_watcher_entry.DirWatchDog, int, List[Dict]]):
    db_thread: DbThread = dir_watcher[0]
    db_thread.start()
    dir_watch_dog: dir_watcher_entry.DirWatchDog = dir_watcher[1]
    tid: int = dir_watcher[2]
    one_path: Dict = dir_watcher[3][0]
    test_path = Path(one_path['path'])

    t: Path = test_path.joinpath('he.txt')
    t.write_text("abc")
    assert test_path.exists()
    assert t.exists()
    time.sleep(1)
    changed_list = db_thread.db.List(V_CHANGED_LIST_TABLE)
    for item in changed_list:
        fc: FileChange = FileChange.from_json_str(item)
        print(fc)
    assert len(changed_list) == 2  # create and change event.

def test_file_change_equal(db_file_path: Path):
    db_file_path.write_text('hello')
    stat1: stat_result = db_file_path.stat()
    stat2 = Path(str(db_file_path)).stat()
    assert stat1 == stat2
    _ = db_file_path.read_text()
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


def test_get_modified(client):
    rv: Response = client.get('/vedis/list-created')
    r = json.loads(rv.get_data(as_text=True))
    assert r['values'] == []
