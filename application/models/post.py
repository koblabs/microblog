from flask import url_for

from application import db
from application.models.base import CRUDMixin, CreateUpdateTimesMixin, \
    SearchableMixin


class Post(CRUDMixin, CreateUpdateTimesMixin, SearchableMixin, db.Model):
    __searchable__ = ["body"]

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    language = db.Column(db.String(5))

    def __repr__(self):
        return f"<Post {self.body}>"

    def to_dict(self):
        return {
            "id": self.id,
            "body": self.body,
            "language": self.language,
            "_links": {
                "self": url_for("api.get_post", id=self.id),
                "user": url_for("api.get_user", id=self.user_id)
            }
        }
