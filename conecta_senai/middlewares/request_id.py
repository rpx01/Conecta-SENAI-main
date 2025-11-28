import uuid
from flask import Blueprint, g, request

request_id_bp = Blueprint('request_id', __name__)


@request_id_bp.before_app_request
def assign_request_id():
    rid = request.headers.get('X-Request-ID')
    if not rid:
        rid = uuid.uuid4().hex
    g.request_id = rid


@request_id_bp.after_app_request
def append_request_id(response):
    rid = getattr(g, 'request_id', None)
    if rid:
        response.headers['X-Request-ID'] = rid
    return response
