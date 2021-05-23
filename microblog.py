from application import create_app, db, cli
from application.models.user import User
from application.models.post import Post
from application.models.notification import Notification
from application.models.message import Message
from application.models.task import Task


app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Post": Post, "Task": Task,
            "Notification": Notification, "Message": Message}
