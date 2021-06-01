from flask import Blueprint


bp = Blueprint("api", __name__)


from application.api import users, posts, errors, tokens
