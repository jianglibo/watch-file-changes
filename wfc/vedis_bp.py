from logging import Logger
from typing import List, Union

from flask import Blueprint, current_app, json

from vedis import Vedis
from wfc.dir_watcher.watch_values import FileChange, decode_file_change

from . import my_vedis
from .constants import V_MODIFIED_SET_TABLE, V_STANDARD_HASH_TABLE
from .typed_value import get_current_args

bp = Blueprint('vedis', __name__, url_prefix="/vedis")


class FileModifiedResponse():
    def __init__(self, length: int, values: List[FileChange]):
        self.length = length
        self.values = values


def get_hash_content(app, table_name: str, length_only: bool = False) -> FileModifiedResponse:
    logger: Logger = app.logger
    db: Vedis = my_vedis.get_db()
    try:
        if length_only:
            d = FileModifiedResponse(length=db.hlen(table_name), values=[])
        else:
            hash_obj: List[str] = list(db.hgetall(table_name).values())
            hash_list: List[FileChange] = list(
                map(decode_file_change, hash_obj))
            d = FileModifiedResponse(length=len(hash_list), values=hash_list)
    except Exception as e:  # pylint: disable=W0703
        logger.error(e, exc_info=True)
        d = FileModifiedResponse(length=0, values=[])
    return d


def get_set_content(table_name: str, length_only: bool = False) -> Union[List[str], int]:
    db: Vedis = my_vedis.get_db()
    if length_only:
        return db.scard(table_name)
    else:
        return list(db.smembers(table_name))


def get_list_content(app, table_name: str, length_only: bool = False) -> FileModifiedResponse:
    logger: Logger = app.logger
    db: Vedis = my_vedis.get_db()
    try:
        if length_only:
            d = FileModifiedResponse(length=db.llen(table_name), values=[])
        else:
            set_obj: List[str] = db.List(table_name)
            set_iter: List[FileChange] = list(map(decode_file_change, set_obj))
            d = FileModifiedResponse(length=len(set_iter), values=set_iter)
    except Exception as e:  # pylint: disable=W0703
        logger.error(e, exc_info=True)
        d = FileModifiedResponse(length=0, values=[])
    return d


@bp.route('/list', methods=['GET'])
def list_list():
    length_only = get_current_args().get('length-only', None, bool)
    r = get_set_content(V_MODIFIED_SET_TABLE,
                        length_only=length_only)
    if isinstance(r, int):
        return json.jsonify(length=r)
    else:
        return json.jsonify(length=len(r), values=r)


@bp.route('/list-base', methods=['GET'])
def list_list_base():
    length_only = get_current_args().get('length-only', None, bool)
    r = get_hash_content(current_app, V_STANDARD_HASH_TABLE,
                         length_only=length_only)
    return json.jsonify(length=r.length, values=r.values)
