from pathlib import Path
from yaml import load, dump
from yaml import Loader, Dumper
import io

class TestYaml():
    def test_object_type(self):
        y_file = Path(__file__).parent.joinpath('borg_configuration.yml')
        with io.open(y_file, mode='r', encoding="utf-8") as y_stream:
            data = load(y_stream, Loader=Loader)

        assert isinstance(data, dict)
        assert isinstance(data.get('ServerSideFileList'), list)
        assert isinstance(data.get('taskcmd'), dict)
        assert isinstance(data.get('coreNumber'), int)
        assert isinstance(data.get('mem'), str)
