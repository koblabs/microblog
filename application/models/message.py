from application import db
from application.models.base import CRUDMixin, CreateUpdateTimesMixin


class Message(CRUDMixin, CreateUpdateTimesMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    body = db.Column(db.String(140))

    def __repr__(self):
        return f"<Message {self.body}"
