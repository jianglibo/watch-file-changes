from py._path.local import LocalPath

from vedis import Vedis  # pylint: disable=E0611

from . import module_scope


def test_module():
    assert module_scope.get_i() == 0
    module_scope.set_i(55)
    assert module_scope.get_i() == 55


def test_queue(tmpdir: LocalPath):
    lp: LocalPath = tmpdir.join('xx.vdb')
    db_file = lp.strpath
    t = module_scope.start_work(db_file)
    loops: int = 10
    for _ in range(0, 10):
        module_scope.q_to_thread.put("abc")
    module_scope.q_to_thread.put(None)

    t.join()
    db: Vedis = Vedis(db_file)
    assert db.llen(module_scope.TABLE_NAME) == loops
