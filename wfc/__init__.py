from flask import Flask
from flask import Config
from flask import Response
from . import my_vedis
from .dir_watcher import dir_watcher_entry
import os, sys
from .constants import OUT_CONFIG_FILE, VEDIS_FILE
from . import vedis_bp
from typing import Dict, List
from logging.config import dictConfig
from . import my_signal
import threading

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
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    try:
        app.config.from_object('config.default') # a string or an actual config object.
        # app.config.from_pyfile('config.py') # half function fo from_object.
        # app.config.from_envvar('abc') # app.config.from_pyfile(os.environ['abc'])
        app.config.from_object('config.%s' % app.config['ENV']) # a string or an actual config object.
    except Exception as e:
        print(e)

    if OUT_CONFIG_FILE in os.environ:
        app.config.from_envvar(OUT_CONFIG_FILE) # app.config.from_pyfile(os.environ['abc'])

    @app.route('/')
    def hello_world(): # pylint: disable=W0612
        info_pairs: List[str] = ["%s=%s" % (pa[0], pa[1]) for pa in app.config.items()]
        info_pairs.append('thread_identity=%s' % threading.get_ident())
        info_pairs.append('main_thread_identity=%s' % threading.main_thread())
        r = Response("\n".join(info_pairs), mimetype="text/plain")
        return r
    my_vedis.init_app(app)

    dir_watcher_entry.start_watchdog(app)
    # app.cli.add_command(dir_watcher_entry.stop_watchdog)

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