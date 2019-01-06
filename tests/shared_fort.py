import os
import shutil
from pathlib import Path

import pytest
from py._path.local import LocalPath

shared_fort_file = os.path.realpath(__file__)


def get_demo_config_file():
    d = os.path.dirname(shared_fort_file)
    d = os.path.dirname(d)
    d = os.path.join(d, 'borg', 'demo-config.python.1.json')
    return d


@pytest.fixture
def tmppath(tmpdir: LocalPath):
    p = tmpdir.mkdir('apath')
    assert isinstance(p, LocalPath)
    pp: Path = Path(p.strpath)
    yield pp
    if pp.exists():
        shutil.rmtree(pp)
