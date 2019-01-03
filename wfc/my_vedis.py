from vedis import Vedis # pylint: disable=E0611
from flask import current_app, g
from flask.cli import with_appcontext
import logging
from .constants import VEDIS_FILE, V_CHANGED_LIST_TABLE
import click
from pathlib import Path
from queue import Queue
import threading, time
from threading import Thread, Lock
from typing import Optional, List
import schedule

data_queque: Queue = Queue()
controll_queue: Queue = Queue()

vedis_thread: Optional[Thread] = None

lock: Lock = Lock()

def init_app(app):
    app.teardown_appcontext(close_db)
    global vedis_thread
    vedis_thread = _start_db_work(app)

def _insert_to_db(db: Vedis, item: str):
    cc: int = 0
    while True:
        cc = cc + 1
        try:
            with db.transaction():
                db.lpush(V_CHANGED_LIST_TABLE, item)
                db.commit()
            break
        except:
            time.sleep(0.2)
            logging.error('insert item %s failed. retring %s', item, cc)


def _db_thread_long_connect(db_file: str):
    db = Vedis(db_file)
    while True:
        try:
            item = data_queque.get()
            if item is None:
                db.close()
                break
            elif isinstance(item, str):
                _insert_to_db(db, item)
            else:
                pass
            data_queque.task_done()
        except Exception as e:
            logging.error(e, exc_info=True)
        finally:
            pass

def job():
    print("I'm working...")

def _start_scheduler():
    schedule.every(10).minutes.do(job)
    schedule.every().hour.do(job)
    schedule.every().day.at("10:30").do(job)
    schedule.every(5).to(10).minutes.do(job)
    schedule.every().monday.do(job)
    schedule.every().wednesday.at("13:15").do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

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

def _start_db_work(app) -> Thread:
    db_file = app.config[VEDIS_FILE]
    logging.info('with vedis file: %s', db_file)
    t = threading.Thread(target=_db_thread_long_connect, args=(db_file,))
    t.start()
    return t

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
