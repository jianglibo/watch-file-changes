import logging
import os
import time
from os import stat_result
from queue import Queue
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler

from .watch_values import ChangeType, FileChange, WatchPath


class LoggingSelectiveEventHandler(FileSystemEventHandler):
    """
    Logs all the events captured.
    """

    def __init__(self, data_queue: Queue, wc: WatchPath):
        super().__init__()
        self.data_queue = data_queue
        self.wc = wc

    def dispatch(self, event: FileSystemEvent):
        """Dispatches events to the appropriate methods.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`FileSystemEvent`
        """
        if self.wc.ignored(event.src_path, event.is_directory):
            return
        super().dispatch(event)

    def stat_tostring(self, a_path):
        try:
            stat = os.stat(a_path)
            return "%s,%s" % (stat.st_size, stat.st_mtime)
        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    def get_stat(self, p: str) -> Optional[stat_result]:
        try:
            return os.stat(p)
        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    def on_moved(self, event):
        what = 'directory' if event.is_directory else 'file'
        try:
            stat: stat_result = self.get_stat(event.dest_path)
            cf: FileChange = FileChange(fn=event.src_path,
                                        ct=ChangeType.moved,
                                        cv=event.dest_path,
                                        mt=stat.st_mtime,
                                        size=stat.st_size)
            self.data_queue.put(cf)
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Moved %s: from %s to %s failed.",
                          what, event.src_path, event.dest_path)
        finally:
            pass

    def on_created(self, event):
        what = 'directory' if event.is_directory else 'file'
        try:
            stat: stat_result = self.get_stat(event.src_path)
            cf: FileChange = FileChange(fn=event.src_path,
                                        ct=ChangeType.created,
                                        cv=None, mt=stat.st_mtime,
                                        size=stat.st_size)
            self.data_queue.put(cf)
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Created %s: %s failed.", what, event.src_path)
        finally:
            pass

    def on_deleted(self, event):
        what = 'directory' if event.is_directory else 'file'
        try:
            cf: FileChange = FileChange(fn=event.src_path,
                                        ct=ChangeType.deleted,
                                        cv=None,
                                        mt=time.time(),
                                        size=0)
            self.data_queue.put(cf)
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Deleted %s: %s failed.", what, event.src_path)
        finally:
            pass

    def on_modified(self, event):
        src_path = event.src_path
        what = 'directory' if event.is_directory else 'file'
        try:
            stat: stat_result = self.get_stat(event.src_path)
            cf: FileChange = FileChange(fn=src_path,
                                        ct=ChangeType.modified,
                                        cv=None,
                                        mt=stat.st_mtime,
                                        size=stat.st_size)
            self.data_queue.put(cf)
        except Exception as e:
            logging.error(e, exc_info=True)
            logging.error("Modify %s: %s failed.", what, event.src_path)
        finally:
            pass
