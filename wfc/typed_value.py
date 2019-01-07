from flask import current_app, request, Request, Flask
from werkzeug.datastructures import ImmutableMultiDict


def get_current_app() -> Flask:
    return current_app


def get_current_request() -> Request:
    return request


def get_current_args() -> ImmutableMultiDict:
    return request.args
