from queue import Queue
import threading
from threading import Thread
from vedis import Vedis  # pylint: disable=E0611

i: int = 0

TABLE_NAME: str = "listtable"

q_to_thread: Queue = Queue()


def set_i(j: int):
    global i
    i = j


def get_i():
    return i


def consume(db_file: str):
    db: Vedis = Vedis(db_file)
    while True:
        item = q_to_thread.get()
        if item is None:
            break
        with db.transaction():
            db.lpush(TABLE_NAME, item)
            db.commit()
        q_to_thread.task_done()


def start_work(db_file: str) -> Thread:
    t = threading.Thread(target=consume, args=(db_file,))
    t.start()
    return t
