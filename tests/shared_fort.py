import os
import shutil
import time
from pathlib import Path
from queue import Queue

from py._path.local import LocalPath

import pytest
import wfc
from vedis import Vedis
from wfc.my_vedis import DbThread

shared_fort_file = os.path.realpath(__file__)


def get_demo_config_file():
    d = os.path.dirname(shared_fort_file)
    d = os.path.dirname(d)
    d = os.path.join(d, 'borg', 'demo-config.python.1.json')
    return d


@pytest.fixture
def tmppath(tmpdir: LocalPath):
    p = tmpdir.mkdir('a_path')
    assert isinstance(p, LocalPath)
    pp: Path = Path(p.strpath)
    yield pp
    if pp.exists():
        shutil.rmtree(pp)

@pytest.fixture
def file_pair(tmpdir: LocalPath):
    p = tmpdir.mkdir('a_path_with_lock')
    pp: Path = Path(p.strpath)
    if pp.exists():
        shutil.rmtree(pp)
    pp.mkdir()

    a_file = pp.joinpath('a_file.txt')
    a_lock_file = pp.joinpath('a_file.txt.lck')
    yield (a_file, a_lock_file)
    if pp.exists():
        shutil.rmtree(pp)

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
def change_folder_path(tmpdir: LocalPath):
    changed_file: Path = Path(str(tmpdir.join('changed_files')))
    changed_file.mkdir()
    yield changed_file
    if changed_file.exists():
        shutil.rmtree(changed_file)


@pytest.fixture
def db_thread(db_file_path: Path, change_folder_path: Path):  # pylint: disable=W0621
    que: Queue = Queue()
    db_thread_in: DbThread = DbThread(
        str(db_file_path), que, change_folder_path)
    yield db_thread_in
    db_thread_in.que.put(None)
    time.sleep(0.2)
