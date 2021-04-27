from os import environ

class Config(object):
    SECRET_KEY = environ.get("SECRET_KEY") or "secret_key"