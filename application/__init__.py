import os, rq
import logging

from redis import Redis
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_babel import Babel, lazy_gettext as _l

from logging.handlers import  SMTPHandler, RotatingFileHandler

from config import Config
from elasticsearch import Elasticsearch


app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
mail = Mail(app)
bootstrap = Bootstrap(app)
moment = Moment(app)
babel = Babel(app)

login.login_view = "auth.login"
login.login_message = _l('Kindly log in to access this page.')


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    bootstrap.init_app(app)
    moment.init_app(app)
    babel.init_app(app)

    app.elasticsearch = Elasticsearch([app.config["ELASTICSEARCH_URL"]]) \
        if app.config["ELASTICSEARCH_URL"] else None
    app.redis = Redis.from_url(app.config["REDIS_URL"])
    app.task_queue = rq.Queue(app.config["EXPORT_TASK_QUEUE"],
                              connection=app.redis)

    from application.main import bp as main_bp
    app.register_blueprint(main_bp)

    from application.errors import bp as error_bp
    app.register_blueprint(error_bp)

    from application.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from application.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    if not app.debug and not app.testing:
        if app.config["MAIL_SERVER"]:
            auth = None
            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr=f"no-reply@{app.config['MAIL_SERVER']}",
                toaddrs=app.config["ADMINS"],
                subject="Microblog Failure",
                credentials=auth,
                secure=secure,
                # timeout=...
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)

        if app.config["LOG_TO_STDOUT"]:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)

        else:    
            if not os.path.exists("logs"):
                os.mkdir("logs")                
            file_handler = RotatingFileHandler("logs/microblog.log",
                                                maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s "
                "[in %(pathname)s:%(lineno)d]"))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("Microblog startup")

    return app


@babel.localeselector
def get_local():
    return request.accept_languages.best_match(app.config["LANGUAGES"])


from application import models
