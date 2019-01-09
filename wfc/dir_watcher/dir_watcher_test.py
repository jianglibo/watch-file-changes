# from .dir_watcher_entry import get_watch_config, WatchConfig, WatchPath, DirWatchDog, load_watch_config
import threading
import time
from pathlib import Path
from threading import Lock

from py._path.local import LocalPath
from typing_extensions import Final

import pytest
from vedis import Vedis  # pylint: disable=E0611

LIST_NAME: Final = 'one-list'

lock_ob: Lock = threading.Lock()


@pytest.fixture
def vdb(tmpdir: LocalPath):
    db_file = Path(tmpdir.strpath).joinpath('db')
    db: Vedis = Vedis(str(db_file.resolve()))
    yield (db)  # provide the fixture value
    print("teardown watchdog")
    db.close()
    tmpdir.remove()


class TestDirWatcher(object):
    def test_true(self, vdb: Vedis):  # pylint: disable=W0621
        assert isinstance(vdb, Vedis)

        def to_run():
            for _ in range(0, 10):
                # list_ob: List = db.List(LIST_NAME)
                with vdb.transaction():
                    # lock_ob.acquire(True)
                    # list_ob.append('hello')
                    vdb.lpush(LIST_NAME, 'hello')
                    # lock_ob.release()
                time.sleep(0.1)

        ts = []

        t = threading.Thread(target=to_run, args=())
        t.start()
        assert t.is_alive()
        ts.append(t.ident)
        t = threading.Thread(target=to_run, args=())
        t.start()

        ts.append(t.ident)
        # len_list: List[int] = []
        # list_ob: List = db.List(LIST_NAME)
        for _ in range(0, 10):
            # list_ob.append('hello')
            vdb.lpush(LIST_NAME, 'hello')
            # lock_ob.acquire(True)
            # len_list.append(db.llen(LIST_NAME))
            # lock_ob.release()
            # time.sleep(0.2)
        time.sleep(3)
        assert vdb.llen(LIST_NAME) == 30

        assert ts[0] != ts[1]

    def test_open_close(self, tmpdir: LocalPath):
        db_file = Path(tmpdir.strpath).joinpath('db1')
        db_file_str = str(db_file.resolve())
        tt: int = 1000
        start_time = time.time()
        for _ in range(0, tt):
            with Vedis(db_file_str) as db:
                db.lpush(LIST_NAME, 'hello')
        db = Vedis(db_file_str)
        assert db.llen(LIST_NAME) == tt
        elapsed_time = time.time() - start_time

        assert elapsed_time > 20

    def test_open(self, tmpdir: LocalPath):
        db_file = Path(tmpdir.strpath).joinpath('db2')
        db_file_str = str(db_file.resolve())
        start_time = time.time()
        db: Vedis = Vedis(db_file_str)
        tt: int = 1000
        for _ in range(0, tt):
            with db.transaction():
                db.lpush(LIST_NAME, 'hello')
        assert db.llen(LIST_NAME) == tt
        db.close()
        elapsed_time = time.time() - start_time

        assert elapsed_time > 10

#     def test_create_file(self, tmp_path):
#         d = tmp_path / "sub"
#         d.mkdir()
#         p = d / "hello.txt"
#         p.write_text(CONTENT)
#         assert p.read_text() == CONTENT
#         assert len(list(tmp_path.iterdir())) == 1

#     def test_create_file_1(self, tmpdir):
#         p = tmpdir.mkdir("sub").join("hello.txt")
#         p.write("content")
#         assert p.read() == "content"
#         assert len(tmpdir.listdir()) == 1

#     def test_configfile(self):
#         wc: WatchConfig = get_watch_config(get_configfile())
#         wp0: WatchPath  = wc.watch_paths[0]
#         assert wp0.regexes[0] == '.*'

#         ign: List[str] = wc.watch_paths[0].ignore_regexes
#         assert ign[0] == r'.*\.txt'
#         assert ign[1] == r'c:\\Users\admin'

#         assert not (wc.watch_paths[0].regexes is None)

#         with pytest.raises(AttributeError):
#                 _ = wc.watch_paths[0].regexes1

#     def test_watcher(self, tp: Tuple[LocalPath, DirWatchDog, int], caplog: LogCaptureFixture):
#         tmpdir = tp[0]
#         wd = tp[1]
#         tid = tp[2]
#         caplog.set_level(logging.DEBUG)

#         assert re.match(r"\w:\\.*", tmpdir.strpath)
#         def to_run(number):
#                 wd.watch()

#         t = threading.Thread(target=to_run, args=(10000,))
#         t.start()
#         assert t.is_alive()
#         time.sleep(2)
#         if tid == 0:
#             p: LocalPath = tmpdir.join('abc.txt')
#             p.write_text('Hello.', encoding="utf-8")
#             time.sleep(1)
#             p.write_text('1Hello.', encoding="utf-8")
#             time.sleep(1)
#             p.write_text('1Hello.', encoding="utf-8")
#             time.sleep(1)
#             target_file = tmpdir.join('abc1.txt')
#             p.move(target_file)
#             time.sleep(1)
#             target_file.remove()
#             time.sleep(1)
#             assert wd.get_created_number() == 1
#             assert wd.get_deleted_number() == 1
#             assert wd.get_modified_number() == 1
#             assert wd.get_moved_number() == 1

#             for r in caplog.records:
#                 print(r)
#         elif tid == 1:
#             p = tmpdir.join('abc.txt')
#             p.write_text('Hello.', encoding="utf-8")

#             time.sleep(2)

#             assert wd.get_created_number() == 0
#             assert wd.get_deleted_number() == 0
#             assert wd.get_modified_number() == 0
#         elif tid == 2:
#             p = tmpdir.join('abc.txt')
#             p.write_text('Hello.', encoding="utf-8")

#             time.sleep(2)

#             assert wd.get_created_number() == 0
#             assert wd.get_deleted_number() == 0
#             assert wd.get_modified_number() == 0
