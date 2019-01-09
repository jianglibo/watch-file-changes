import time
from os import stat_result
from pathlib import Path
from typing import Dict

from flask import Response, json


import pytest
from vedis import Vedis
from .shared_fort import vdb, db_file_path  # pylint: disable=W0611


def test_open_vedis(vdb: Vedis):  # pylint: disable=W0621
    with vdb.transaction():
        h: Dict = vdb.Hash('a-hash')
        h['abc'] = 55
        vdb.commit()
    v: str = vdb.hget('a-hash', 'abc')
    assert int(v) == 55

def test_pop_set(vdb: Vedis):  # pylint: disable=W0621
    empty_set = vdb.Set('not-exists-set-name')
    empty_set.add('a')
    empty_set.pop()
    assert empty_set.pop() is None
    empty_set.add('a')
    empty_set.add('b')

    while True:
        item = empty_set.pop()
        if item is None:
            break
    assert not empty_set

def test_counter(vdb: Vedis):  # pylint: disable=W0621
    i: int = vdb.incr('k')
    assert i == 1
    i = vdb.incr('k')
    assert i == 2
    b = vdb.get('k')
    assert int(b) == 2

def test_hash_get(vdb: Vedis):  # pylint: disable=W0621
    s = vdb.hget("a-hash-table", 'abc')
    assert s is None
    b = vdb.hexists('a-hash-table', 'abc')
    assert not b

    n = vdb.hdel('a-hash-table', 'abc')
    assert n == 0

def test_db_key(vdb: Vedis):  # pylint: disable=W0621
    with pytest.raises(KeyError):
        vdb.delete('not-exist-key')

def test_db_set(vdb: Vedis):  # pylint: disable=W0621
    vdb.srem('a-set', 'k')

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


def test_get_modified(client):  # pylint: disable=W0621
    rv: Response = client.get('/vedis/list-created')
    r = json.loads(rv.get_data(as_text=True))
    assert r['values'] == []
