import os
import re
import threading
from pathlib import Path
from queue import Queue
from typing import List, Optional, Pattern

from .watch_values import WatchConfig, WatchPath


class DirInitThread(threading.Thread):
    def __init__(self, data_queue: Queue, wc: WatchConfig, regexes: Optional[List[str]] = None,
                 ignore_regexes: Optional[List[str]] = None,
                 case_sensitive: bool = False, **kwargs):
        super().__init__(**kwargs)
        self._regexes: List[Pattern]
        self._ignore_regexes: List[Pattern]
        self.data_queue = data_queue
        self.wc = wc
        if regexes is None:
            regexes = []
        if ignore_regexes is None:
            ignore_regexes = []

        if case_sensitive:
            self._regexes = [re.compile(r) for r in regexes]
            self._ignore_regexes = [re.compile(r) for r in ignore_regexes]
        else:
            self._regexes = [re.compile(r, re.I) for r in regexes]
            self._ignore_regexes = [re.compile(
                r, re.I) for r in ignore_regexes]
        self._case_sensitive = case_sensitive
        self._has_regexes = len(self._regexes) > 0

    def run(self):
        for item in self.wc.watch_paths:
            wp: WatchPath = item
            for current_dir, __dirs_under_current_dir, files_under_current_dir in os.walk(wp.path, topdown=False):

                paths_under_current_dir: List[Path] = [Path(current_dir, f) for f in files_under_current_dir]
                for p in paths_under_current_dir:
                    print(p)
                    self.data_queue.put(p)

            # assert isinstance(current_dir, str)
            # assert isinstance(dirs_under_current_dir, list)
            # assert isinstance(files_under_current_dir, list)
