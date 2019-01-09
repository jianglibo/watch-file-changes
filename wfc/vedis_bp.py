from logging import Logger
from typing import List, Set

from flask import Blueprint, Response, current_app

from vedis import Vedis
from wfc.dir_watcher.watch_values import FileChange, decode_file_change

from . import my_vedis
from .constants import V_MODIFIED_SET_TABLE
from .typed_value import get_current_args
from flask import json

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


def get_set_content(app, table_name: str, length_only: bool = False) -> FileModifiedResponse:
    logger: Logger = app.logger
    db: Vedis = my_vedis.get_db()
    try:
        if length_only:
            d = FileModifiedResponse(length=db.scard(table_name), values=[])
        else:
            set_obj: Set[str] = db.smembers(table_name)
            set_iter: List[FileChange] = list(map(decode_file_change, set_obj))
            d = FileModifiedResponse(length=len(set_iter), values=set_iter)
    except Exception as e:  # pylint: disable=W0703
        logger.error(e, exc_info=True)
        d = FileModifiedResponse(length=0, values=[])
    return d


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
    d: FileModifiedResponse = get_set_content(
        current_app, V_MODIFIED_SET_TABLE, length_only=length_only)
    return json.jsonify(length=d.length,
                        values=d.values)

# @bp.route('/list-modified', methods=['GET'])
# def list_modified():
#     length_only = get_current_args().get('length-only', None, bool)
#     d: ListStrDict = get_set_content(current_app, V_MODIFIED_REALLY_SET_TABLE, length_only)
#     r = Response(json.dumps(d), mimetype="text/plain")
#     return r

# @bp.route('/list-created', methods=['GET'])
# def list_created():
#     length_only = get_current_args().get('length-only', None, bool)
#     d = get_set_content(current_app, V_CREATED_SET_TABLE, length_only)
#     r = Response(json.dumps(d), mimetype="text/plain")
#     return r

# @bp.route('/list-deleted', methods=['GET'])
# def list_deleted():
#     length_only = get_current_args().get('length-only', None, bool)
#     d = get_set_content(current_app, V_DELETED_SET_TABLE, length_only)
#     r = Response(json.dumps(d), mimetype="text/plain")
#     return r

# @bp.route('/list-moved', methods=['GET'])
# def list_moved():
#     length_only = get_current_args().get('length-only', None, bool)
#     d = get_set_content(current_app, V_MOVED_SET_TABLE, length_only=length_only)
#     r = Response(json.dumps(d), mimetype="text/plain")
#     return r

# @bp.route('/list-modified-hash', methods=['GET'])
# def list_modified_hash():
#     length_only = get_current_args().get('length-only', None, bool)
#     d: ListOfTupleDict = get_hash_content(current_app, V_MODIFIED_HASH_TABLE, length_only=length_only)
#     r = Response(json.dumps(d), mimetype="text/plain")
#     return r
