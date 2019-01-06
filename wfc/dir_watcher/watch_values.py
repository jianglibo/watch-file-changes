import json
import logging
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from mypy_extensions import TypedDict


class ErrorNames(Enum):
    config_file_not_exists = 1
    un_exist_watch_paths = 2


class WatchPath():
    def __init__(self,
                 path: Path,
                 regexes: List[str] = [],
                 ignore_regexes: List[str] = [],
                 ignore_directories: bool = True,
                 case_sensitive: bool = True,
                 recursive: bool = True):
        self.path = path
        self.recursive = recursive
        self.regexes = regexes
        self.case_sensitive = case_sensitive
        self.ignore_directories = ignore_directories
        self.ignore_regexes = ignore_regexes
        self._has_regexes = len(self.regexes) > 0

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


class FileChange(TypedDict):
    fn: bytes
    ct: int
    cv: Optional[bytes]
    mt: float
    size: int


class WatchConfig():
    def __init__(self, watch_pathes: List[Dict]) -> None:
        for wp in watch_pathes:
            wp['path'] = Path(wp['path']).expanduser()
        self.watch_paths: List[WatchPath] = [
            WatchPath(**p) for p in watch_pathes]
        logging.info('with %s to watch.', self.watch_paths)

    def get_un_exists_paths(self) -> List[WatchPath]:
        return [wp for wp in self.watch_paths if not wp.path.exists()]


def encode_file_change(fc: Union[FileChange, Path]) -> str:
    if isinstance(fc, Path):
        stat = fc.stat()
        fcp: FileChange = FileChange(fn=bytes(fc),
                                     ct=ChangeType.created,
                                     cv=None,
                                     mt=stat.st_mtime,
                                     size=stat.st_size)

        return json.dumps(fcp)
    else:
        return json.dumps(fc)


def decode_file_change(json_str: str) -> FileChange:
    return json.loads(json_str)
