# import signal, os, sys
# from . import my_vedis, dir_watcher_entry


def signal_handler(sig, frame):  # pylint: disable=W0613
    print('You pressed Ctrl+C!')
    # dir_watcher_entry.dir_watch_dog.stop_watch()
    # data_queque.put(None)
    # vedis_thread.join()

# signal.signal(signal.SIGINT, signal_handler)
