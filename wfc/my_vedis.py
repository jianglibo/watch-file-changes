from vedis import Vedis # pylint: disable=E0611
from flask import current_app, g
from flask.cli import with_appcontext
import logging
from .constants import VEDIS_FILE, V_CHANGED_LIST_TABLE
import click
from pathlib import Path
from queue import Queue
import threading, time
from threading import Thread, Lock, Event
from typing import Optional, List
import schedule

data_queque: Queue = Queue()
controll_queue: Queue = Queue()

lock: Lock = Lock()
cease_db_run: Event = threading.Event()
cease_schedule_run: Event = threading.Event()

def init_app(app):
    app.teardown_appcontext(close_db)
    DbThread(app.config[VEDIS_FILE]).start()
    ScheduleThread().start()

class DbThread(threading.Thread):

    def _insert_to_db(self, item: str):
        cc: int = 0
        while True:
            cc = cc + 1
            if cc > 6:
                logging.error('insert item %s failed, after tring 6 times, giving up.', item)
                break
            try:
                with self.db.transaction():
                    self.db.lpush(V_CHANGED_LIST_TABLE, item)
                    self.db.commit()
                break
            except:
                time.sleep(0.2)

    def __init__(self, db_file:str, **kwargs):
        super().__init__(**kwargs)
        self.db = Vedis(db_file)

    def run(self):
        while not cease_db_run.is_set():
            try:
                item = data_queque.get()
                if item is None:
                    self.db.close()
                    break
                elif isinstance(item, str):
                    self._insert_to_db(item)
                else:
                    pass
                data_queque.task_done()
            except Exception as e:
                logging.error(e, exc_info=True)
            finally:
                pass

class ScheduleThread(threading.Thread):
    def job(self):
        print("I'm working...%s" % time.asctime())

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def run(self):
        schedule.every(10).seconds.do(self.job)
        while not cease_schedule_run.is_set():
            schedule.run_pending()
            time.sleep(1)

def get_db():
    if 'db' not in g:
        g.db = Vedis(current_app.config[VEDIS_FILE])
    return g.db


def close_db(e=None):
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
#             logging.error('insert item %s failed, after tring 6 times, giving up.', item)
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
