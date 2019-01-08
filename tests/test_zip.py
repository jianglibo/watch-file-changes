import re
from pathlib import Path
from zipfile import ZipFile, ZipInfo

from .shared_fort import tmppath  # pylint: disable=W0611


class TestZipFile(object):
    def test_item_name(self, tmppath: Path):  # pylint: disable=W0621
        zf_path = tmppath.joinpath("t.zip")
        str_file = tmppath.joinpath('str.txt')
        str_file_slash = str(str_file).replace('\\', '/')
        with ZipFile(zf_path, mode='a') as zip_file:
            zip_file.writestr(str(str_file), b'hello')

        with ZipFile(zf_path) as zip_file:
            il = zip_file.infolist()
            assert len(il) == 1
            ils = zip_file.namelist()
            assert re.match('^[A-Za-z]{1}:.*str.txt$', ils[0])

        #  file name separator is slash.
        with ZipFile(zf_path) as zip_file:
            ils = zip_file.namelist()
            assert ils[0] == str_file_slash
            bb = zip_file.read(str_file_slash)
            assert bb == b'hello'

        with ZipFile(zf_path) as zip_file:
            il = zip_file.infolist()
            il_one: ZipInfo = il[0]
            assert il_one.filename == str_file_slash
            extracted = zip_file.extract(il_one, tmppath)
            str_file_slash_no_root = re.sub(
                r'^[a-zA-Z]{1}:.{1}', '', str_file_slash)
            full_path = str(tmppath.joinpath(str_file_slash_no_root).resolve())
            assert extracted == full_path
