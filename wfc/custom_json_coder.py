
from typing import NamedTuple

from flask.json import JSONEncoder

import logging
from collections import namedtuple
from wfc.dir_watcher.watch_values import FileChange
from wfc.values import DiskFree, FileHash


class CustomJSONEncoder(JSONEncoder):
    def default(self, o):  # pylint: disable=E0202
        try:
            if isinstance(o, FileChange):
                return o.as_dict()
            if isinstance(o, FileHash):
                return vars(o)
            if isinstance(o, DiskFree):
                return vars(o)
            if isinstance(o, bytes):
                bs: bytes = o
                return bs.decode()
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, o)
