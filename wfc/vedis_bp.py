import json
from logging import Logger
from typing import Dict, List, Set, Tuple

from flask import (Blueprint, Response, current_app)
from mypy_extensions import TypedDict

from vedis import Vedis  # pylint: disable=E0611

from . import my_vedis
from .constants import (V_CHANGED_LIST_TABLE)
from .typed_value import get_current_args

bp = Blueprint('vedis', __name__, url_prefix="/vedis")


class ListOfTupleDict(TypedDict):
    length: int
    values: List[Tuple[str, str]]


class ListStrDict(TypedDict):
    length: int
    values: List[str]


def get_hash_content(app, table_name: str, length_only: bool = False) -> ListOfTupleDict:
    logger: Logger = app.logger
    db: Vedis = my_vedis.get_db()
    try:
        if length_only:
            d = ListOfTupleDict(length=db.hlen(table_name), values=[])
        else:
            hash_obj: Dict[bytes, bytes] = db.hgetall(table_name)
            hash_list: List[Tuple[str, str]] = list(map(lambda itm: (itm[0].decode(), itm[1].decode()),
                                                        hash_obj.items()))
            d = ListOfTupleDict(length=len(hash_list), values=hash_list)
    except Exception as e:
        logger.error(e, exc_info=True)
        d = ListOfTupleDict(length=0, values=[])
    return d


def get_set_content(app, table_name: str, length_only: bool = False) -> ListStrDict:
    logger: Logger = app.logger
    db: Vedis = my_vedis.get_db()
    try:
        if length_only:
            d = ListStrDict(length=db.scard(table_name), values=[])
        else:
            set_obj: Set[bytes] = db.smembers(table_name)
            set_iter: List[str] = list(map(lambda bts: bts.decode(), set_obj))
            d = ListStrDict(length=len(set_iter), values=set_iter)
    except Exception as e:
        logger.error(e, exc_info=True)
        d = ListStrDict(length=0, values=[])
    return d


def get_list_content(app, table_name: str, length_only: bool = False) -> ListStrDict:
    logger: Logger = app.logger
    db: Vedis = my_vedis.get_db()
    try:
        if length_only:
            d = ListStrDict(length=db.llen(table_name), values=[])
        else:
            set_obj: List[bytes] = db.List(table_name)
            set_iter: List[str] = list(map(lambda bts: bts.decode(), set_obj))
            d = ListStrDict(length=len(set_iter), values=set_iter)
    except Exception as e:
        logger.error(e, exc_info=True)
        d = ListStrDict(length=0, values=[])
    return d


@bp.route('/list', methods=['GET'])
def list_list():
    length_only = get_current_args().get('length-only', None, bool)
    d: ListOfTupleDict = get_list_content(
        current_app, V_CHANGED_LIST_TABLE, length_only=length_only)
    r = Response(json.dumps(d), mimetype="text/plain")
    return r

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
