from flask import Flask
from flask import Config
from flask import Response

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config') # a string or an actual config object.
app.config.from_pyfile('config.py') # half function fo from_object.
# app.config.from_envvar('abc') # app.config.from_pyfile(os.environ['abc'])

app.config.from_object('config.%s' % app.config['ENV']) # a string or an actual config object.

@app.route('/')
def hello_world():
    keystr: str = ';'.join(app.config.keys())
    r = Response("\n".join(["%s=%s" % (pa[0], pa[1]) for pa in app.config.items()]), mimetype="text/plain")
    return r


# app = Flask(__name__, instance_relative_config=True)

# # Load the default configuration
# app.config.from_object('config.default')

# # Load the configuration from the instance folder
# app.config.from_pyfile('config.py')

# # Load the file specified by the APP_CONFIG_FILE environment variable
# # Variables defined here will override those in the default configuration
# app.config.from_envvar('APP_CONFIG_FILE')