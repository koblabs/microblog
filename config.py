from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, ".env"))

class Config(object):
    SECRET_KEY = environ.get("SECRET_KEY") or "secret_key"
    JWT_ALGORITHM = environ.get("JWT_ALGORITHM") or "HS256"
    
    SQLALCHEMY_DATABASE_URI = environ.get("DATABASE_URL") or \
        f"sqlite:///{path.join(basedir, 'app.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = environ.get("MAIL_SERVER")
    MAIL_PORT = int(environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
    ADMINS = environ.get("MAIL_ADMINS") or ["koowusuboaky@gmail.com"]

    POSTS_PER_PAGE = 10
    MESSAGES_PER_PAGE = 15

    LANGUAGES = ["en", "es"]
    #LANGUAGES = [en-US, en-GB, en-CA]

    MS_TRANSLATOR_KEY = environ.get("MS_TRANSLATOR_KEY")
    MS_TRANSLATOR_REGION = environ.get("MS_TRANSLATOR_REGION") or "eastus2"

    ELASTICSEARCH_URL = environ.get("ELASTICSEARCH_URL")
    REDIS_URL = environ.get("REDIS_URL") or "redis://"

    LOG_TO_STDOUT = environ.get("LOG_TO_STDOUT")

    EXPORT_TASK_QUEUE = environ.get("EXPORT_TASK_QUEUE") or "microblog-tasks"
