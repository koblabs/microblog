from http import HTTPStatus

from flask import render_template

from application import db
from application.errors import bp


@bp.app_errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), HTTPStatus.NOT_FOUND


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("errors/500.html"), HTTPStatus.INTERNAL_SERVER_ERROR
