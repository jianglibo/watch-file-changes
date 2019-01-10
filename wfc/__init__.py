import sys
import os
from typing import List
import logging
import threading
from queue import Queue

from . import my_vedis, vedis_bp
from .constants import OUT_CONFIG_FILE, WATCH_PATHES
from .dir_watcher import dir_watcher_dog
from flask import Flask, Response
from flask.json import JSONEncoder
from logging.config import dictConfig

from .dir_watcher.watch_values import FileChange


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


def find_data_file(filename):
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)
    return os.path.join(datadir, filename)


class CustomJSONEncoder(JSONEncoder):

    def default(self, o):  # pylint: disable=E0202
        try:
            if isinstance(o, FileChange):
                return o.as_dict()
            if isinstance(o, bytes):
                bs: bytes = o
                return bs.decode()
            iterable = iter(o)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, o)


def create_app(init_vedis=True, init_watch_dog=True, register_vedis=True):
    app = Flask(__name__, instance_relative_config=True)
    app.json_encoder = CustomJSONEncoder
    # try:
    # a string or an actual config object.
    app.config.from_object('config.default')
    # app.config.from_pyfile('config.py') # half function fo from_object.
    # app.config.from_envvar('abc') # app.config.from_pyfile(os.environ['abc'])
    # a string or an actual config object.
    app.config.from_object('config.%s' % app.config['ENV'])
    # except Exception as e:
    # logging.error(e, exc_info=True)

    if OUT_CONFIG_FILE in os.environ:
        # app.config.from_pyfile(os.environ['abc'])
        app.config.from_envvar(OUT_CONFIG_FILE)

    @app.route('/')
    def hello_world():  # pylint: disable=W0612
        info_pairs: List[str] = ["%s=%s" %
                                 (pa[0], pa[1]) for pa in app.config.items()]
        info_pairs.append('thread_identity=%s' % threading.get_ident())
        info_pairs.append('main_thread_identity=%s' % threading.main_thread())
        r = Response("\n".join(info_pairs), mimetype="text/plain")
        return r

    que = Queue()

    if init_vedis:
        my_vedis.init_app(app, que)
    if init_watch_dog:
        dir_watcher_dog.DirWatchDog(
            app.config[WATCH_PATHES], que).watch(initialize=True)
    if register_vedis:
        app.register_blueprint(vedis_bp.bp)
    return app


# app = Flask(__name__, instance_relative_config=True)

# # Load the default configuration
# app.config.from_object('config.default')

# # Load the configuration from the instance folder
# app.config.from_pyfile('config.py')

# # Load the file specified by the APP_CONFIG_FILE environment variable
# # Variables defined here will override those in the default configuration
# app.config.from_envvar('APP_CONFIG_FILE')
