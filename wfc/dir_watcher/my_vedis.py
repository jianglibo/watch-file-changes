from vedis import Vedis # pylint: disable=E0611
from flask.cli import with_appcontext
import logging
from ..constants import VEDIS_DB, VEDIS_FILE
import click


def open_vedis(app):
    if VEDIS_FILE not in app.config:
        logging.fatal("%s configuration is missing.", VEDIS_FILE)
        return

    if VEDIS_DB not in app.config:
        vedis_file: str = app.config[VEDIS_FILE]
        app.config[VEDIS_DB] = Vedis(vedis_file)

# @click.command('close-vedis')
# @with_appcontext
def close_vedis(app):
    db: Vedis = app.config[VEDIS_DB]
    if db is not None:
        db.close()