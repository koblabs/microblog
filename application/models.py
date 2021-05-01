import jwt

from datetime import datetime
from hashlib import md5
from time import time

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from application import db, login, app


followers = db.Table("followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("following_id", db.Integer, db.ForeignKey("user.id"))
)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class CRUDMixin(object):
    @classmethod
    def create(cls, **kwargs):
        instance = cls(**kwargs)
        return instance.save()

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()

    def reload(self):
        db.session.refresh(self)


class CreateUpdateTimesMixin(object):
    created_on = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, index=True, default=datetime.utcnow,
                           onupdate=datetime.utcnow)


class  User(UserMixin, CRUDMixin, CreateUpdateTimesMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(16), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password = db.Column(db.String(64))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    following = db.relationship(
        "User", secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.following_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
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
            app.config["SECRET_KEY"], 
            algorithm=app.config["JWT_ALGORITHM"]
        )

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token,
                app.config["SECRET_KEY"],
                algorithms=app.config["JWT_ALGORITHM"]
            )["reset_password"]
        except:
            return
        return User.query.get(id)

class Post(CRUDMixin, CreateUpdateTimesMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def __repr__(self):
        return f"<Post {self.body}>"
