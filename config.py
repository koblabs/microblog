from os import environ, path

basedir = path.abspath(path.dirname(__file__))

class Config(object):
    SECRET_KEY = environ.get("SECRET_KEY") or "secret_key"
    SQLALCHEMY_DATABASE_URI = environ.get("DATABASE_URI") or \
        f"sqlite:///{path.join(basedir, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False