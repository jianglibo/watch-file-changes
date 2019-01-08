import logging
import threading
import time
import traceback
from pathlib import Path
from queue import Queue
from typing import List, Tuple, Optional

import schedule
from flask import current_app, g

from vedis import Vedis
from wfc.dir_watcher.watch_values import ChangeType

from .constants import V_STANDARD_HASH_TABLE, VEDIS_FILE, V_CREATED_SET_TABLE, V_MODIFIED_SET_TABLE, V_DELETED_SET_TABLE
from .dir_watcher.watch_values import FileChange, encode_file_change, decode_file_change

controll_queue: Queue = Queue()

lock = threading.Lock()
cease_db_run = threading.Event()
cease_schedule_run = threading.Event()


class DbThread(threading.Thread):
    def __init__(self, db_file: str, file_change_queue: Queue, batch_file_change_queue: Queue, **kwargs):
        super().__init__(**kwargs)
        self.db = Vedis(db_file)
        self.file_change_queue: Queue = file_change_queue
        self.batch_file_change_queue: Queue = batch_file_change_queue

    def _insert_to_db(self, item: FileChange):
        try:
            with self.db.transaction():
                delete_count: Optional[str] = None
                bb = encode_file_change(item)
                if item.ct == ChangeType.created:
                    self.db.sadd(V_CREATED_SET_TABLE, item.fn)
                    self.db.hset(V_STANDARD_HASH_TABLE, item.fn, bb)
                    self.db.sadd(V_MODIFIED_SET_TABLE, bb)
                elif item.ct == ChangeType.modified:
                    saved_item_str = self.db.hget(V_STANDARD_HASH_TABLE, item.fn)
                    no_saved_or_changed = False
                    if saved_item_str is None:
                        no_saved_or_changed = True
                    else:
                        saved_item = decode_file_change(saved_item_str)
                        if saved_item != item:
                            no_saved_or_changed = True
                    if no_saved_or_changed:
                        self.db.hset(V_STANDARD_HASH_TABLE, item.fn, bb)
                        self.db.sadd(V_MODIFIED_SET_TABLE, bb)
                        self.db.incr(item.fn)
                    else:
                        logging.debug("file wasn't actually changed, %s", item.fn)
                elif item.ct == ChangeType.deleted:
                    self.db.sadd(V_DELETED_SET_TABLE, bb)
                    self.db.hdel(V_STANDARD_HASH_TABLE, item.fn)
                    self.db.srem(V_CREATED_SET_TABLE, item.fn)
                    delete_count = item.fn
                else:  # moved
                    self.db.sadd(V_DELETED_SET_TABLE, bb)
                    if not item.cv:
                        logging.error("move event's cv value is None. %s", item.fn)
                    else:
                        delete_count = item.fn
                        self.db.sadd(V_CREATED_SET_TABLE, item.cv)
                        item.fn = item.cv
                        item.cv = None
                        new_bb = encode_file_change(item)
                        self.db.hset(V_STANDARD_HASH_TABLE, item.fn, new_bb)
                if delete_count:
                    try:
                        self.db.delete(delete_count)
                    except KeyError as ke:
                        logging.error(ke, exc_info=True)
                self.db.commit()
        except Exception as e:  # pylint: disable=W0703
            logging.error(e, exc_info=True)

    def insert_standard(self, item: Path):
        try:
            with self.db.transaction():
                self.db.hset(V_STANDARD_HASH_TABLE, str(item), encode_file_change(item))
                self.db.commit()
        except Exception as e:  # pylint: disable=W0703
            logging.error(e, exc_info=True)

    # def process_file_change(self, number: int):
    #     items: List[str] = []
    #     with self.db.transaction():
    #         item = self.db.lpop(V_CHANGED_LIST_TABLE)
    #         idx: int = 0
    #         while item is not None:
    #             items.append(item)
    #             idx += 1
    #             if idx >= number > 0:
    #                 break
    #             item = self.db.lpop(V_CHANGED_LIST_TABLE)
    #         self.db.commit()
    #     self.batch_file_change_queue.put(items)

    def run(self):
        while True:
            try:
                item = self.file_change_queue.get()
                if item is None:
                    self.db.close()
                    break
                elif isinstance(item, FileChange):
                    self._insert_to_db(item)
                # elif isinstance(item, int):
                #     self.process_file_change(item)
                elif isinstance(item, Path):
                    self.insert_standard(item)
                else:
                    logging.error("unknown data: %s receive in db_thread.", type(item))
                    traceback.print_stack()
                self.file_change_queue.task_done()
            except Exception as e:  # pylint: disable=W0703
                logging.error(e, exc_info=True)
            finally:
                pass
        else:
            self.db.close()


class ScheduleThread(threading.Thread):
    def job(self):
        print("I'm working...%s" % time.asctime())

    def __init__(self, cease_event: threading.Event, **kwargs):
        super().__init__(**kwargs)
        self.cease_event = cease_event

    def run(self):
        schedule.every(10).seconds.do(self.job)
        while not self.cease_event.is_set():
            schedule.run_pending()
            time.sleep(1)


class BatchProcessThread(threading.Thread):
    def __init__(self, batch_file_change_queue: Queue, **kwargs):
        super().__init__(**kwargs)
        self.batch_file_change_queue: Queue = batch_file_change_queue

    def run(self):
        while True:
            try:
                item: List[bytes] = self.batch_file_change_queue.get()
                if item is None:
                    break
                assert isinstance(item, list)
                self.batch_file_change_queue.task_done()
            except Exception as e:  # pylint: disable=W0703
                logging.error(e, exc_info=True)
            finally:
                pass
            time.sleep(1)


def init_app(app, data_queue: Queue) -> Tuple[DbThread]:
    app.teardown_appcontext(close_db)
    batch_file_change_queue: Queue = Queue()
    db_thread = DbThread(app.config[VEDIS_FILE], data_queue, batch_file_change_queue)
    db_thread.start()
    ScheduleThread(cease_schedule_run).start()
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

# def get_read_only_db():
#     global __ro_db
#     if __ro_db is None:
#         if __db_file is None:
#             return None
#         __ro_db = Vedis(__db_file)
#     return __ro_db

# def open_vedis(app):
#     if VEDIS_FILE not in app.config:
#         logging.fatal("%s configuration is missing.", VEDIS_FILE)
#         return

#     if VEDIS_DB not in app.config:
#         vedis_file: str = app.config[VEDIS_FILE]
#         vedis_path: Path = Path(vedis_file).resolve()
#         # assert vedis_path.exists()
#         app.config[VEDIS_DB] = Vedis(str(vedis_path))


# def _db_thread(db_file: str):
#     retring: Optional[str] = None
#     while True:
#         db: Optional[Vedis] = None
#         from_queue = False
#         try:
#             if retring is not None:
#                 time.sleep(0.2)
#                 item = retring
#                 retring = None
#                 cc = cc + 1
#             else:
#                 item = data_queque.get()
#                 from_queue = True
#                 cc = 0
#             db = Vedis(db_file)
#             if item is None:
#                 db.close()
#                 break
#             try:
#                 with db.transaction():
#                     db.lpush(V_CHANGED_LIST_TABLE, item)
#                     db.commit()
#                 retring = None
#             except:
#                 logging.error('insert item %s failed. retring %s', item, cc)
#                 retring = item

#             if from_queue:
#                 data_queque.task_done()
#         except Exception as e:
#             logging.error(e, exc_info=True)
#         finally:
#             if db is not None:
#                 db.close()

# def _insert_to_db(db: Vedis, item: str):
#     cc: int = 0
#     while True:
#         cc = cc + 1
#         if cc > 6:
#             logging.error('insert item %s failed, after trying 6 times, giving up.', item)
#             break
#         try:
#             with db.transaction():
#                 db.lpush(V_CHANGED_LIST_TABLE, item)
#                 db.commit()
#             break
#         except:
#             time.sleep(0.2)

# def _db_thread_long_connect(db_file: str):
#     db = Vedis(db_file)
#     while True:
#         try:
#             item = data_queque.get()
#             if item is None:
#                 db.close()
#                 break
#             elif isinstance(item, str):
#                 _insert_to_db(db, item)
#             else:
#                 pass
#             data_queque.task_done()
#         except Exception as e:
#             logging.error(e, exc_info=True)
#         finally:
#             pass
# def _start_scheduler():
#     schedule.every(10).seconds.do(job)
#     # schedule.every().hour.do(job)
#     # schedule.every().day.at("10:30").do(job)
#     # schedule.every(5).to(10).minutes.do(job)
#     # schedule.every().monday.do(job)
#     # schedule.every().wednesday.at("13:15").do(job)
#     while True:
#         schedule.run_pending()
#         time.sleep(1)

# def _start_scheduler_worker() -> Thread:
#     t = threading.Thread(target=_start_scheduler)
#     t.start()
#     return t

# def _start_db_work(app) -> Thread:
#     cease_event = threading.Event()
#     db_file = app.config[VEDIS_FILE]
#     logging.info('with vedis file: %s', db_file)
#     t = threading.Thread(target=_db_thread_long_connect, args=(db_file,))
#     t.start()
#     return cease_event
