from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flask import current_app
from .constants import VEDIS_DB
from vedis import Vedis # pylint: disable=E0611
import os

bp = Blueprint('vedis', __name__, url_prefix="/vedis")

@bp.route('/list-modified', methods=['GET'])
def register():
    # db: Vedis = current_app.config[VEDIS_DB]
    # return os.environ['PYTHONPATH']
    # return "abc"
    db: Vedis = current_app.config[VEDIS_DB]
    i: int
    i = 's'
    return i
    # return render_template('vedis/list-modified.html')