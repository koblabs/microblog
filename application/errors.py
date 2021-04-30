from http import HTTPStatus

from flask import render_template

from application import app, db


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), HTTPStatus.NOT_FOUND

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("500.html"), HTTPStatus.INTERNAL_SERVER_ERROR