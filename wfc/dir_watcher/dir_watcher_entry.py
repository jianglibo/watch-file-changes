import os, json, sys, re
import time
from pathlib import Path
import logging
from watchdog.observers import Observer
from watchdog.events import RegexMatchingEventHandler, FileSystemEventHandler, FileSystemEvent
from typing import NamedTuple, List, Optional, Dict, Any, Iterator, Pattern, Match, Union, ClassVar, Tuple
import getopt
from vedis import Vedis # pylint: disable=E0611
from collections import namedtuple
from typing_extensions import Final
from enum import Enum
from ..constants import WATCH_PATHES, V_MODIFIED_HASH_TABLE, V_MODIFIED_REALLY_SET_TABLE, V_MOVED_SET_TABLE, V_CREATED_SET_TABLE, V_DELETED_SET_TABLE, WATCH_DOG, V_CHANGED_LIST_TABLE
import click
from flask.cli import with_appcontext
from flask import current_app
from os import stat_result
from threading import Lock
import threading
from .. import my_vedis

class ErrorNames(Enum):
    config_file_not_exists = 1
    un_exist_watch_paths = 2

class WatchPath(NamedTuple):
    regexes: List[str]
    ignore_regexes: List[str]
    ignore_directories: bool
    case_sensitive: bool
    path: Path
    recursive: bool

class ChangeType(Enum):
    created = 1
    modified = 2
    moved = 3
    deleted= 4

class FileChange(NamedTuple):
    fn: bytes
    ct: ChangeType
    cv: Optional[bytes]
    stat: Optional[stat_result]

    def to_dict(self) -> Dict[str, Any]:
        return dict(fn=self.fn, ct=self.ct.value, cv=self.cv, stat=self.stat)

class WatchConfig():
    def __init__(self, watch_pathes: List[Dict]) -> None:
        for wp in watch_pathes:
            wp['path'] = Path(wp['path']).expanduser()
        self.watch_paths: List[WatchPath] = [WatchPath(**p) for p in watch_pathes]
        logging.info('with %s to watch.', self.watch_paths)

    def get_un_exists_paths(self) -> List[WatchPath]:
        return [wp for wp in self.watch_paths if not wp.path.exists()]


class DirWatchDog():
    def __init__(self, wc: WatchConfig) -> None:
        self.wc = wc
        self.save_me = True
        self.observers : List[Observer] = []

    def wait_seconds(self, seconds: int) -> None:
        for obs in self.observers:
            obs.join(seconds)

    def watch(self) -> None:
        for ps in self.wc.watch_paths:
            event_handler = LoggingSelectiveEventHandler(
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

class LoggingSelectiveEventHandler(FileSystemEventHandler):
    """
    Logs all the events captured.
    """

    def __init__(self, regexes: List[str]=[r".*"], ignore_regexes: List[str]=[],
                 ignore_directories: bool =False, case_sensitive: bool=False):
        super(LoggingSelectiveEventHandler, self).__init__()
        self._regexes: List[Pattern]
        self._ignore_regexes: List[Pattern]

        if case_sensitive:
            self._regexes = [re.compile(r) for r in regexes]
            self._ignore_regexes = [re.compile(r) for r in ignore_regexes]
        else:
            self._regexes = [re.compile(r, re.I) for r in regexes]
            self._ignore_regexes = [re.compile(r, re.I) for r in ignore_regexes]
        self._ignore_directories = ignore_directories
        self._case_sensitive = case_sensitive
        self._has_regexes = len(self._regexes) > 0
        logging.debug("create regexes: %s, ignore_regexes: %s", regexes, ignore_regexes)


    def dispatch(self, event: FileSystemEvent):
        """Dispatches events to the appropriate methods.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`FileSystemEvent`
        """
        src_path: str = event.src_path
        if event.is_directory and self._ignore_directories:
            logging.debug("directory %s ignored.", src_path)
            return

        for r in self._ignore_regexes:
            if r.match(src_path):
                logging.debug("%s hit ignore_regexes %s, skipping...", src_path, r.pattern)
                return
            
        if self._has_regexes and (not any([r.match(src_path) for r in self._regexes])):
            logging.debug("%s not in regexes, skipping...", src_path)
            return
        super().dispatch(event)
    
    def stat_tostring(self, a_path):
        try:
            stat = os.stat(a_path)
            return "%s,%s" % (stat.st_size, stat.st_mtime)
        except:
            return None
    
    def get_stat(self, p: str) -> Optional[stat_result]:
        try:
            return os.stat(p)
        except:
            return None
        

    def on_moved(self, event):
        what = 'directory' if event.is_directory else 'file'
        try:
            cf: FileChange = FileChange(fn=event.src_path, ct=ChangeType.moved, cv=event.dest_path, stat=self.get_stat(event.dest_path))
            my_vedis.data_queque.put(json.dumps(cf.to_dict()))
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Moved %s: from %s to %s failed.", what, event.src_path, event.dest_path)
        finally:
            pass


    def on_created(self, event):
        what = 'directory' if event.is_directory else 'file'
        try:
            cf: FileChange = FileChange(fn=event.src_path ,ct=ChangeType.created, cv=None, stat=self.get_stat(event.src_path))
            my_vedis.data_queque.put(json.dumps(cf.to_dict()))
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Created %s: %s failed.", what, event.src_path)
        finally:
            pass


    def on_deleted(self, event):
        what = 'directory' if event.is_directory else 'file'
        try:
            cf: FileChange = FileChange(fn=event.src_path, ct=ChangeType.deleted, cv=None, stat=None)
            my_vedis.data_queque.put(json.dumps(cf.to_dict()))
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Deleted %s: %s failed.", what, event.src_path)
        finally:
            pass

    def on_modified(self, event):
        src_path = event.src_path
        what = 'directory' if event.is_directory else 'file'
        try:  
            cf: FileChange = FileChange(fn= src_path, ct=ChangeType.modified, cv=None, stat=self.get_stat(src_path))
            my_vedis.data_queque.put(json.dumps(cf.to_dict()))
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Modify %s: %s failed.", what, event.src_path)
        finally:
            pass

dir_watch_dog: Optional[DirWatchDog] = None

def start_watchdog(app):
    global dir_watch_dog
    wc: WatchConfig = WatchConfig(app.config[WATCH_PATHES])
    dir_watch_dog = DirWatchDog(wc)
    dir_watch_dog.watch()
    # app.config[WATCH_DOG] = wd

# @click.command('stop-watchdog')
# @with_appcontext
# def stop_watchdog():
#     wd: DirWatchDog = current_app.config[WATCH_DOG]
#     wd.stop_watch()