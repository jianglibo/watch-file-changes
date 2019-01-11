import time

import schedule

import logging
import threading
from enum import Enum
from queue import Queue
from typing import Dict


ARCHIVE_INTERVAL = "ARCHIVE_INTERVAL"
PENDING_MOVE_INTERVAL = "PENDING_MOVE_INTERVAL"


class ControllAction(Enum):
    ArchiveChange = 1
    PendingMove = 2


class ScheduleThread(threading.Thread):
    def archive_job(self):
        logging.info("start archive job ...")
        self.controll_queue.put(ControllAction.ArchiveChange)

    def pending_move_job(self):
        logging.info("start pending move job ...")
        self.controll_queue.put(ControllAction.PendingMove)

    def __init__(self,
                 cease_event: threading.Event,
                 controll_queue: Queue,
                 schedule_dict: Dict,
                 **kwargs):
        super().__init__(**kwargs)
        self.cease_event = cease_event
        self.controll_queue = controll_queue
        self.archive_interval = int(schedule_dict.get(ARCHIVE_INTERVAL, 60))
        self.pending_move_interval = int(
            schedule_dict.get(PENDING_MOVE_INTERVAL, 60))

    def run(self):
        schedule.every(self.archive_interval).seconds.do(self.archive_job)
        schedule.every(self.pending_move_interval).seconds.do(
            self.pending_move_job)
        while not self.cease_event.is_set():
            schedule.run_pending()
            time.sleep(1)


def init_app(app, que: Queue) -> threading.Event:
    ev = threading.Event()
    ScheduleThread(ev, que, app.config).start()
    return ev
