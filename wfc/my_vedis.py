from typing import Set, Tuple, Union, List

from .constants import VEDIS_FILE, V_CREATED_SET_TABLE, V_DELETED_SET_TABLE, \
    V_INCREMENT_KEY, V_MODIFIED_SET_TABLE, V_STANDARD_HASH_TABLE, \
    Z_CHANGED_FOLDER, LOCK_FILE_NAME, PENDING_FOLDER_NAME
from .dir_watcher.watch_values import FileChange, decode_file_change, \
    encode_file_change
from filelock import FileLock
from flask import current_app, g
from .my_scheduler import ControllAction
from vedis import Vedis

import logging
import threading
import traceback
from pathlib import Path
from queue import Queue
from wfc import dir_util
from wfc.dir_watcher.watch_values import ChangeType
from zipfile import ZipFile


lock = threading.Lock()
cease_db_run = threading.Event()
cease_schedule_run = threading.Event()


class DbThread(threading.Thread):
    """Why choose only one queue? Because we want block query.

    """

    def __init__(self, db_file: str,
                 que: Queue,
                 change_folder: Union[Path, str],
                 **kwargs):
        super().__init__(**kwargs)
        self.db = Vedis(db_file)
        self.que: Queue = que
        self.change_folder_path: Path
        if isinstance(change_folder, str):
            self.change_folder_path = Path(change_folder)
        else:
            self.change_folder_path = change_folder

        if not self.change_folder_path.exists():
            self.change_folder_path.mkdir()
        self.lock_file_path = self.change_folder_path.joinpath(LOCK_FILE_NAME)
        self.pending_folder_path = self.change_folder_path.joinpath(PENDING_FOLDER_NAME)

        if not self.pending_folder_path.exists():
            self.pending_folder_path.mkdir()

        if self.lock_file_path.exists():
            self.lock_file_path.unlink()

    def delete_count_key(self, count_key: str):
        try:
            self.db.delete(count_key)
        except KeyError as ke:
            logging.error(ke, exc_info=True)

    def when_data_modified(self, item: FileChange, encoded_item: str):
        saved_item_str = self.db.hget(V_STANDARD_HASH_TABLE, item.fn)
        no_saved_or_changed = False
        if saved_item_str is None:
            no_saved_or_changed = True
        else:
            saved_item = decode_file_change(saved_item_str)
            if saved_item != item:
                no_saved_or_changed = True
        if no_saved_or_changed:
            self.db.hset(V_STANDARD_HASH_TABLE, item.fn, encoded_item)
            self.db.sadd(V_MODIFIED_SET_TABLE, item.fn)
            self.db.incr(item.fn)
        else:
            logging.debug("file wasn't actually changed, %s", item.fn)

    def _insert_to_db(self, item: FileChange):
        try:
            with self.db.transaction():
                bb = encode_file_change(item)
                if item.ct == ChangeType.created:
                    self.db.sadd(V_CREATED_SET_TABLE, item.fn)
                    self.db.hset(V_STANDARD_HASH_TABLE, item.fn, bb)
                    self.db.sadd(V_MODIFIED_SET_TABLE, item.fn)
                elif item.ct == ChangeType.modified:
                    self.when_data_modified(item, bb)
                elif item.ct == ChangeType.deleted:
                    self.db.sadd(V_DELETED_SET_TABLE, bb)
                    self.db.hdel(V_STANDARD_HASH_TABLE, item.fn)
                    self.db.srem(V_CREATED_SET_TABLE, item.fn)
                    self.delete_count_key(item.fn)
                else:  # moved
                    self.db.sadd(V_DELETED_SET_TABLE, bb)
                    if not item.cv:
                        logging.error(
                            "move event's cv value is None. %s", item.fn)
                    else:
                        self.delete_count_key(item.fn)
                        self.db.sadd(V_CREATED_SET_TABLE, item.cv)
                        item.fn = item.cv
                        item.cv = None
                        new_bb = encode_file_change(item)
                        self.db.hset(V_STANDARD_HASH_TABLE, item.fn, new_bb)
                self.db.commit()
        except Exception as e:  # pylint: disable=W0703
            logging.error(e, exc_info=True)

    def insert_standard(self, item: Path):
        try:
            with self.db.transaction():
                self.db.hset(V_STANDARD_HASH_TABLE, str(
                    item), encode_file_change(item))
                self.db.commit()
        except Exception as e:  # pylint: disable=W0703
            logging.error(e, exc_info=True)

    def get_archives(self) -> List[Path]:
        return dir_util.list_dir_order_by_digits(self.change_folder_path)

    def get_pending_archives(self) -> List[Path]:
        return list(self.pending_folder_path.iterdir())

    def process_pending_move(self):
        with FileLock(self.lock_file_path):
            for fp in self.get_archives():
                target_path = self.pending_folder_path.joinpath(fp.name)
                fp.rename(target_path)

    def process_archive_action(self):
        """We do archive job in specified intervals.
        Does it necessary to create a new zip file on every trigger?
        We get the max file name under the folder, check it's length,
        if larger then specified value, create a new zip file.
        If we archive at 10 seconds interval, at what interval can we
        move the file to other place?
        The archive interval should small than move interval, the min of two
        if the data protect window.
        """
        with FileLock(self.lock_file_path):
            with self.db.transaction():
                all_changed_file_names: Set[str] = self.db.Set(
                    V_MODIFIED_SET_TABLE)
                if all_changed_file_names:
                    files: List[Path] = self.get_archives()
                    if files:
                        zip_file_path = files[-1]
                    else:
                        zip_file_path = self.change_folder_path.joinpath(
                            "%s.zip" % self.db.incr(V_INCREMENT_KEY))
                    while True:
                        file_name = all_changed_file_names.pop()
                        if file_name is None:
                            break
                        if isinstance(file_name, bytes):
                            file_name_str = file_name.decode()
                        with ZipFile(zip_file_path, mode='a') as zip_file:
                            try:
                                zip_file.write(file_name_str)
                            except TypeError as te:
                                logging.error(te, exc_info=True)
                            except OSError as oe:
                                logging.error(oe, exc_info=True)
                self.db.commit()

    def run(self):
        """Entry point.
        Query queue blockingly until None is received.
        There is no necessary to time sleep, it' blocked.
        """
        while True:
            item: Union[FileChange, Path, ControllAction] = self.que.get()
            if item is None:
                self.db.close()
                break
            if isinstance(item, FileChange):
                self._insert_to_db(item)
            elif isinstance(item, Path):
                self.insert_standard(item)
            elif isinstance(item, ControllAction):
                if item == ControllAction.ArchiveChange:
                    self.process_archive_action()
                elif item == ControllAction.PendingMove:
                    self.process_pending_move()
                else:
                    logging.error("unknown action: %s receive in db_thread.", item)
                    traceback.print_stack()
            else:
                logging.error(
                    "unknown data: %s receive in db_thread.", type(item))
                traceback.print_stack()
            self.que.task_done()


def init_app(app, que: Queue) -> Tuple[DbThread]:
    app.teardown_appcontext(close_db)
    db_thread = DbThread(
        app.config[VEDIS_FILE], que, app.config[Z_CHANGED_FOLDER])
    db_thread.start()
    return (db_thread,)


def get_db():
    if 'db' not in g:
        g.db = Vedis(current_app.config[VEDIS_FILE])
    return g.db


def close_db(e=None):
    if e:
        logging.error(e, exc_info=True)
    db = g.pop('db', None)
    if db is not None:
        db.close()
