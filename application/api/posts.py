from http import HTTPStatus

from flask import jsonify, request, url_for, abort

from application import db
from application.api import bp
from application.api.errors import bad_request
# from application.models.user import User
from application.models.post import Post
from application.api.auth import token_auth


@bp.route("/posts/<int:id>", methods=["GET"])
@token_auth.login_required
def get_post(id):
    return jsonify(Post.query.get_or_404(id).to_dict())


@bp.route("/posts", methods=["GET"])
@token_auth.login_required
def get_posts():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    data = Post.to_collection_dict(Post.query, page, per_page, "api.get_posts")
    return jsonify(data)
