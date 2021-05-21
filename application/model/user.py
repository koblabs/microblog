import jwt, json, rq, base64, os

from datetime import datetime, timedelta
from hashlib import md5
from time import time

from flask import current_app, url_for
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from application import db, login
from application.model.api import PaginationMixin
from application.model.base import CRUDMixin, CreateUpdateTimesMixin
from application.models import Message
from application.models import Post
from application.models import Notification
from application.models import Task

followers = db.Table("followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("following_id", db.Integer, db.ForeignKey("user.id"))
)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class  User(UserMixin, CRUDMixin, CreateUpdateTimesMixin,
            PaginationMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(64))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    following = db.relationship("User", secondary=followers,
                                primaryjoin=(followers.c.follower_id == id),
                                secondaryjoin=(followers.c.following_id == id),
                                backref=db.backref("followers", lazy="dynamic"),
                                lazy="dynamic")
    messages_sent = db.relationship("Message", 
                                    foreign_keys="Message.sender_id",
                                    backref="author", lazy="dynamic")
    messages_received = db.relationship("Message", 
                                        foreign_keys="Message.recipient_id",
                                        backref="recipient", lazy="dynamic")
    messages_last_read = db.Column(db.DateTime)
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")
    tasks = db.relationship("Task", backref="user", lazy="dynamic")
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}"

    def is_following(self, user):
        return self.following.filter(
            followers.c.following_id == user.id
        ).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            self.following.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def following_posts(self):
        my_posts = Post.query.filter_by(user_id=self.id)

        my_following_posts = Post.query.join(
            followers, (followers.c.following_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)

        return my_posts.union(my_following_posts).order_by(
            Post.created_on.desc()
        )

    def get_reset_password_token(self, span=1800):
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + span},
            current_app.config["SECRET_KEY"], 
            algorithm=current_app.config["JWT_ALGORITHM"])

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"],
                algorithms=current_app.config["JWT_ALGORITHM"]
                )["reset_password"]
        except:
            return
        return User.query.get(id)

    def new_messages(self):
        last_read = self.messages_last_read or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.created_on > last_read).count()

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload=json.dumps(data), user=self)
        db.session.add(n)
        return n

    def launch_task(self, name, description, *args, **kwargs):
        rq_job = current_app.task_queue.enqueue("application.tasks." + name,
                                                self.id, *args, **kwargs)
        task = Task(id=rq_job.get_id(), name=name, description=description,
                    user=self)
        db.session.add(task)
        return task

    def get_tasks_in_progress(self):
        return Task.query.filter_by(user=self, complete=False).all()

    def get_task_in_progress(self, name):
        return Task.query.filter_by(name=name, user=self,
                                    complete=False).first()

    def to_dict(self, include_email=False):
        data = {
            "id": self.id,
            "username": self.username,
            "last_seen": self.last_seen.isoformat() + "Z",
            "about_me": self.about_me,
            "post_count": self.posts.count(),
            "follower_count": self.followers.count(),
            "following_count": self.following.count(),
            "_links": {
                "self": url_for("api.get_user", id=self.id),
                "followers": url_for("api.get_followers", id=self.id),
                "following": url_for("api.get_following", id=self.id),
                "avatar": self.avatar(128)
            }
        }
        if include_email:
            data["email"] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ["username", "email", "about_me"]:
            if field in data:
                setattr(self, field, data[field])
        if new_user and "password" in data:
            self.set_password(data["password"])
    
    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode("utf-8")
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def verify_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user
