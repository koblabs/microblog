from threading import Thread

from flask import current_app
from flask_mail import Message


from application import mail, app


def send_async_email(app, message):
    with app.app_context():
        mail.send(message)


def send_mail(subject, sender, recipients, body, html):
    message = Message(subject, sender=sender, recipients=recipients)
    message.body = body
    message.html = html
    # mail.send(message)
    # print(body)
    Thread(target=send_async_email, 
            args=(current_app._get_current_object(), message)).start()
