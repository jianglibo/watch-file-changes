import signal, os, sys
from . import my_vedis, dir_watcher_entry


def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    dir_watcher_entry.dir_watch_dog.stop_watch()
    my_vedis.data_queque.put(None)
    my_vedis.vedis_thread.join()

# signal.signal(signal.SIGINT, signal_handler)


