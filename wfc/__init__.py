from flask import Flask
from flask import Config
from flask import Response
from .dir_watcher import my_vedis
from .dir_watcher import dir_watcher_entry
import os
from .constants import OUT_CONFIG_FILE
from . import vedis_bp
from typing import Dict

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config.default') # a string or an actual config object.
    # app.config.from_pyfile('config.py') # half function fo from_object.
    # app.config.from_envvar('abc') # app.config.from_pyfile(os.environ['abc'])

    app.config.from_object('config.%s' % app.config['ENV']) # a string or an actual config object.

    if OUT_CONFIG_FILE in os.environ:
        app.config.from_envvar(OUT_CONFIG_FILE) # app.config.from_pyfile(os.environ['abc'])

    @app.route('/')
    def hello_world(): # pylint: disable=W0612
        # keystr: str = ';'.join(app.config.keys())
        r = Response("\n".join(["%s=%s" % (pa[0], pa[1]) for pa in app.config.items()]), mimetype="text/plain")
        return r
    my_vedis.open_vedis(app)
    dir_watcher_entry.start_watchdog(app)
    app.cli.add_command(dir_watcher_entry.stop_watchdog)

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