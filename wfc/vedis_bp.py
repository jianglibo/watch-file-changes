from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flask import current_app, Response, request
from .constants import VEDIS_DB, V_CREATED_SET_TABLE, V_DELETED_SET_TABLE, V_MODIFIED_HASH_TABLE, V_MODIFIED_REALLY_SET_TABLE, V_MOVED_SET_TABLE
from vedis import Vedis # pylint: disable=E0611
import os
from typing import Set, Optional, AnyStr, Iterable, Dict, Tuple, List
from logging import Logger
import json

bp = Blueprint('vedis', __name__, url_prefix="/vedis")

def get_hash_content(app, table_name: str) -> Iterable[Tuple[str, str]]:
    logger: Logger = app.logger
    db: Vedis = app.config[VEDIS_DB]
    try:
        hash_obj: Dict[bytes, bytes] = db.hgetall(table_name)
        hash_iter: Iterable[Tuple[str, str]] = map(lambda itm: (itm[0].decode(), itm[1].decode()), hash_obj.items())
    except Exception as e:
        logger.error(e, exc_info=True)
        hash_iter = []
    return hash_iter

def get_set_content(app, table_name: str) -> Iterable[str]:
    logger: Logger = app.logger
    db: Vedis = app.config[VEDIS_DB]
    try:
        set_obj: Set[bytes] = db.smembers(table_name)
        set_iter: Iterable[str] = map(lambda bts: bts.decode(), set_obj)
    except Exception as e:
        logger.error(e, exc_info=True)
        set_iter = []
    return set_iter

@bp.route('/list-modified', methods=['GET'])
def list_modified():
    content: List[str] = list(get_set_content(current_app, V_MODIFIED_REALLY_SET_TABLE))
    d = {"length": len(content), "values": content}
    r = Response(json.dumps(d), mimetype="text/plain")
    return r

@bp.route('/list-created', methods=['GET'])
def list_created():
    content: List[str] = list(get_set_content(current_app, V_CREATED_SET_TABLE))
    d = {"length": len(content), "values": content}
    r = Response(json.dumps(d), mimetype="text/plain")
    return r

@bp.route('/list-deleted', methods=['GET'])
def list_deleted():
    content: List[str] = list(get_set_content(current_app, V_DELETED_SET_TABLE))
    d = {"length": len(content), "values": content}
    r = Response(json.dumps(d), mimetype="text/plain")
    return r

@bp.route('/list-moved', methods=['GET'])
def list_moved():
    content: List[str] = get_set_content(current_app, V_MOVED_SET_TABLE)
    c1 = [s.split('|') for s in content]
    d = {"length": len(c1), "values": c1}
    r = Response(json.dumps(d), mimetype="text/plain")
    return r

@bp.route('/list-modified-hash', methods=['GET'])
def list_modified_hash():
    content: List[Tuple[str, str]] = list(get_hash_content(current_app, V_MODIFIED_HASH_TABLE))
    d = {"length": len(content), "values": content}
    r = Response(json.dumps(d), mimetype="text/plain")
    return r