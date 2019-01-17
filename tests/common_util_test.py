import os

import pytest
from . import shared_fort
from wfc.custom_json_coder import CustomJSONEncoder

import json
import subprocess
import xml.etree.ElementTree as ET
from functools import partial
from wfc.global_static import BorgConfiguration, PyGlobal
from pathlib import Path
from wfc import common_util
from wfc.values import FileHash


def two_add(a, b, c=6):
    return a + int(b) + c


class TestCommonUtil():

    def test_split_url(self):
        assert common_util.split_url("http://abc/cc", True) == 'http://abc/'
        assert common_util.split_url("http://abc/cc", False) == 'cc'

    def test_static(self):
        PyGlobal.configuration = 10
        assert PyGlobal.configuration == 10

    def test_load_configfile(self):
        cf = shared_fort.get_demo_config_file()
        j = common_util.get_configration(cf)
        assert j['UserName'] == 'root'
        softwares = j['SwitchByOs'][j['OsType']]['Softwares']
        assert isinstance(softwares, list)

    def test_os_walk(self):
        pd: Path = PyGlobal.python_dir
        assert pd.name == 'python'

        checked: bool = False

        for current_dir, dirs_under_current_dir, files_under_current_dir in \
                os.walk(PyGlobal.python_dir, topdown=False):
            assert isinstance(current_dir, str)
            assert isinstance(dirs_under_current_dir, list)
            assert isinstance(files_under_current_dir, list)

            cd: Path = Path(current_dir)

            if cd.name == 'python':
                checked = True
                py_files = [
                    f for f in files_under_current_dir if f.endswith('.py')]
                assert isinstance(py_files[0], str)
                assert len(py_files) == 5
                assert len(dirs_under_current_dir) == 1
        assert checked

    def test_file_hash(self):
        f_path = Path(__file__).parent.joinpath('__init__.py')
        ha = common_util.get_one_filehash(f_path, "SHA256")
        assert ha.Hash == '0EFFBF25E5B6C5E9C821225AC4E6AB77F0ADED9D0C6AA4597E09193EA882BE04'
        s1 = CustomJSONEncoder().encode(ha)
        s = json.dumps(ha, cls=CustomJSONEncoder)
        assert s == s1
        jo = json.loads(s)
        assert isinstance(jo, dict)
        fh: FileHash = FileHash(**jo)

        assert fh.Hash == '0EFFBF25E5B6C5E9C821225AC4E6AB77F0ADED9D0C6AA4597E09193EA882BE04'


    def test_config_wrapper(self):
        cf = shared_fort.get_demo_config_file()
        j = common_util.get_configration(cf)
        wp = BorgConfiguration(j)
        assert wp.borg_repo_path(None) == "/opt/repo"

    def test_subprocess_call(self):
        with pytest.raises(WindowsError) as we:
            subprocess.check_output('exit 1')
        assert 'FileNotFoundError' in str(we)

    def test_partial(self):
        v = partial(two_add, 1)('2')
        assert v == 9
        v = partial(two_add, 1, c=1)('2')
        assert v == 4
        v = partial(two_add, 1)('2', 1)
        assert v == 4

    def test_filehashes(self):
        _ = common_util.get_dir_filehashes(PyGlobal.python_dir)
        assert _

    def test_diskfree(self):
        dfs = common_util.get_diskfree()
        df = list(dfs)[0]
        assert df.Used
        assert df.Free
        assert df.UsedMegabyte

    def test_memoryfree(self):
        mf = common_util.get_memoryfree()
        assert mf

    def test_xml(self):
        f = Path(__file__).joinpath('..', '..', 'mysql', 'fixtures', 'abc.xml')
        s = common_util.get_filecontent_str(f)
        rows = [(x[0].text, x[1].text) for x in ET.fromstring(s)]
        assert rows
