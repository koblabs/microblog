from threading import Thread

from flask import render_template
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
    print(body)
    Thread(target=send_async_email, args=(app, message)).start()

def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_mail("[Microblg] Reset Password",
        sender=app.config["ADMINS"][0],
        recipients=[user.email],
        body=render_template("email/reset_password.txt",
                                user=user, token=token),
        html=render_template("email/reset_password.html",
                                user=user, token=token)
    )