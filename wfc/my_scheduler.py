import time

import schedule

import logging
import threading
from enum import Enum
from queue import Queue


class ControllAction(Enum):
    ArchiveChange = 1


class ScheduleThread(threading.Thread):
    def archive_job(self):
        logging.info("start archive job ...")
        self.controll_queue.put(ControllAction.ArchiveChange)

    def __init__(self, cease_event: threading.Event, controll_queue: Queue, **kwargs):
        super().__init__(**kwargs)
        self.cease_event = cease_event
        self.controll_queue = controll_queue

    def run(self):
        schedule.every(60).seconds.do(self.archive_job)
        while not self.cease_event.is_set():
            schedule.run_pending()
            time.sleep(1)

def init_app(app, que: Queue) -> threading.Event:
    ev = threading.Event()
    ScheduleThread(ev, que).start()
    return ev
