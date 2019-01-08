import time
from typing import Dict, List, Optional, Union

import logging
import re
from enum import Enum
from pathlib import Path


class ErrorNames(Enum):
    config_file_not_exists = 1
    un_exist_watch_paths = 2


class WatchPath():
    def __init__(self,
                 path: Path,
                 regexes: List[str] = None,
                 ignore_regexes: List[str] = None,
                 ignore_directories: bool = True,
                 case_sensitive: bool = True,
                 recursive: bool = True):
        self.path = path
        self.recursive = recursive
        self.regexes = regexes if regexes else []
        self.case_sensitive = case_sensitive
        self.ignore_directories = ignore_directories
        self.ignore_regexes = ignore_regexes if ignore_regexes else []
        self._has_regexes = len(self.regexes) > 0
        self._regexes: List = []
        self._ignore_regexes: List = []

    def compile_re(self):
        if self.regexes is None:
            self.regexes = []
        if self.ignore_regexes is None:
            self.ignore_regexes = []

        if self.case_sensitive:
            self._regexes = [re.compile(r) for r in self.regexes]
            self._ignore_regexes = [re.compile(r) for r in self.ignore_regexes]
        else:
            self._regexes = [re.compile(r, re.I) for r in self.regexes]
            self._ignore_regexes = [re.compile(
                r, re.I) for r in self.ignore_regexes]
        return self

    def ignored(self, strpath: str, is_dir=False):
        if is_dir and self.ignore_directories:
            return True
        for r in self._ignore_regexes:
            if r.match(strpath):
                logging.debug(
                    "%s hit ignore_regexes %s, skipping...", strpath, r.pattern)
                return True

        if self._has_regexes and (not any([r.match(strpath) for r in self._regexes])):
            logging.debug("%s not in regexes, skipping...", strpath)
            return True

        return False


class ChangeType():
    created = 1
    modified = 2
    moved = 3
    deleted = 4


class FileChange():
    """
      we get file name from file system event handler which is a string. But vedis value is always bytes.
      Because vedis list will truncate 00 byte, so we use str instead.
    """
    fn: str
    ct: int
    cv: Optional[str]
    mt: float
    size: int
    ts: float

    def __init__(self, fn: str,
                 ct: int,
                 mt: float,
                 size: int,
                 ts: Optional[float] = None,
                 cv: Optional[str] = None):
        self.fn = fn
        self.ct = ct
        self.mt = mt
        self.size = size
        self.cv = cv
        self.ts = time.time() if ts is None else ts

    def __str__(self) -> str:
        return '|'.join([
            self.fn,
            str(self.ct),
            str(self.mt),
            str(self.size),
            str(self.ts),
            self.cv if self.cv else ''
        ])

    def __eq__(self, other) -> bool:
        if self.fn != other.fn:
            return False
        if self.mt != other.mt:
            return False
        if self.size != other.size:
            return False
        return True

    def deep_equal(self, other) -> bool:
        pass

    # def to_bytes(self) -> bytes:
    #     return b'%b\x00%b\x00%b\x00%b\x00%b' % (
    #         self.fn.encode(),
    #         str(self.ct).encode(),
    #         str(self.mt).encode(),
    #         str(self.size).encode(),
    #         self.cv.encode() if self.cv else b'')


class WatchConfig():
    def __init__(self, watch_pathes: List[Dict]) -> None:
        for wp in watch_pathes:
            wp['path'] = Path(wp['path']).expanduser()
        self.watch_paths: List[WatchPath] = [
            WatchPath(**p).compile_re() for p in watch_pathes]
        logging.info('with %s to watch.', self.watch_paths)

    def get_un_exists_paths(self) -> List[WatchPath]:
        return [wp for wp in self.watch_paths if not wp.path.exists()]


def encode_file_change(fc: Union[FileChange, Path]) -> str:
    file_change: FileChange
    if isinstance(fc, Path):
        stat = fc.stat()
        file_change = FileChange(fn=str(fc),
                                 ct=ChangeType.created,
                                 mt=stat.st_mtime,
                                 size=stat.st_size)
    else:
        file_change = fc
    return str(file_change)


def decode_file_change(bytes_repr: Union[str, bytes]) -> FileChange:
    """We actually got bytes when from vedis.
    """
    fields: Union[List[str], List[bytes]]
    fn: str
    if isinstance(bytes_repr, bytes):
        fields = bytes_repr.split(b'|')
        fn = fields[0].decode()
        cv = fields[5].decode()
    else:
        fields = bytes_repr.split('|')
        fn = fields[0]
        cv = fields[5]

    return FileChange(fn=fn,
                      ct=int(fields[1]),
                      mt=float(fields[2]),
                      size=int(fields[3]),
                      ts=float(fields[4]),
                      cv=cv)
