from http import HTTPStatus

from flask import render_template, request  

from application import db
from application.errors import bp
from application.api.errors import error_response as api_error_response


def wants_json_response():
    return request.accept_mimetypes['application/json'] >= \
        request.accept_mimetypes['text/html']


@bp.app_errorhandler(404)
def not_found(error):
    if wants_json_response():
        return api_error_response(HTTPStatus.NOT_FOUND)
    return render_template("errors/404.html"), HTTPStatus.NOT_FOUND


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if wants_json_response():
        return api_error_response(HTTPStatus.INTERNAL_SERVER_ERROR)
    return render_template("errors/500.html"), HTTPStatus.INTERNAL_SERVER_ERROR
