from pathlib import Path
from queue import Queue
from typing import Dict, List, Optional

from watchdog.observers import Observer

from .selective_file_event_handler import LoggingSelectiveEventHandler
from .watch_values import WatchConfig


class DirWatchDog():
    def __init__(self, wc: WatchConfig, data_queue: Queue) -> None:
        self.wc = wc
        self.save_me = True
        self.observers: List[Observer] = []
        self.data_queue = data_queue

    def wait_seconds(self, seconds: int) -> None:
        for obs in self.observers:
            obs.join(seconds)

    def watch(self) -> None:
        for ps in self.wc.watch_paths:
            event_handler = LoggingSelectiveEventHandler(
                self.data_queue,
                regexes=ps.regexes,
                ignore_regexes=ps.ignore_regexes,
                ignore_directories=ps.ignore_directories,
                case_sensitive=ps.case_sensitive)
            path_to_observe: str = str(ps.path.resolve())
            assert Path(path_to_observe).exists()
            observer = Observer()
            observer.schedule(event_handler, path_to_observe, recursive=ps.recursive)
            observer.start()
            self.observers.append(observer)

    def stop_watch(self):
        for obs in self.observers:
            obs.stop()


dir_watch_dog: Optional[DirWatchDog] = None


def start_watchdog(watch_pathes: List[Dict], data_queue: Queue) -> DirWatchDog:
    wc: WatchConfig = WatchConfig(watch_pathes)
    d_watch_dog = DirWatchDog(wc, data_queue)
    d_watch_dog.watch()
    return d_watch_dog
