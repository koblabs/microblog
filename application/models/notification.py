import json

from application import db
from application.models.base import CRUDMixin, CreateUpdateTimesMixin


class Notification(CRUDMixin, CreateUpdateTimesMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    payload = db.Column(db.Text)

    def __repr__(self):
        return f"<Notification {self.name}"

    def get_data(self):
        return json.loads(str(self.payload))
