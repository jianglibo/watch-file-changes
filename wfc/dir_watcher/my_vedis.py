from vedis import Vedis # pylint: disable=E0611
from flask.cli import with_appcontext
import logging

from typing_extensions import Final

VEDIS_FILE: Final = 'VEDIS_FILE'
VEDIS_DB: Final = 'VEDIS_DB'

def open_vedis(app):
    if VEDIS_FILE not in app.config:
        logging.fatal("%s configuration is missing.", VEDIS_FILE)
        return

    if VEDIS_DB not in app.config:
        vedis_file: str = app.config[VEDIS_FILE]
        app.config[VEDIS_DB] = Vedis(vedis_file)

def close_vedis(app):
    db: Vedis = app.config[VEDIS_DB]

    if db is not None:
        db.close()