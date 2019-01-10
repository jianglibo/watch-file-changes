import os
from pathlib import Path
from queue import Queue
from typing import Dict, List, Union

from watchdog.observers import Observer

from .selective_file_event_handler import LoggingSelectiveEventHandler
from .watch_values import WatchConfig, WatchPath


class DirWatchDog():
    def __init__(self, wc_or_paths: Union[WatchConfig, List[Dict]], que: Queue) -> None:
        if isinstance(wc_or_paths, WatchConfig):
            self.wc = wc_or_paths
        else:
            self.wc = WatchConfig(wc_or_paths)
        self.save_me = True
        self.observers: List[Observer] = []
        self.que = que

    def wait_seconds(self, seconds: int) -> None:
        for obs in self.observers:
            obs.join(seconds)

    def watch(self, initialize=False) -> None:
        if initialize:
            for item in self.wc.watch_paths:
                wp: WatchPath = item
                for current_dir, \
                        __dirs_under_current_dir, \
                        files_under_current_dir in os.walk(wp.path, topdown=False):

                    paths_under_current_dir: List[Path] = [
                        Path(current_dir, f) for f in files_under_current_dir]
                    for p in paths_under_current_dir:
                        if not wp.ignored(str(p), p.is_dir()):
                            self.que.put(p)

        for wp in self.wc.watch_paths:
            event_handler = LoggingSelectiveEventHandler(
                self.que, wp)
            path_to_observe: str = str(wp.path.resolve())
            assert Path(path_to_observe).exists()
            observer = Observer()
            observer.schedule(event_handler, path_to_observe,
                              recursive=wp.recursive)
            observer.start()
            self.observers.append(observer)

    def stop_watch(self):
        for obs in self.observers:
            obs.stop()


# dir_watch_dog: Optional[DirWatchDog] = None
# def start_watchdog(watch_pathes: List[Dict], data_queue: Queue) -> DirWatchDog:
#     wc: WatchConfig = WatchConfig(watch_pathes)
#     d_watch_dog = DirWatchDog(wc, data_queue)
#     d_watch_dog.watch()
#     return d_watch_dog
