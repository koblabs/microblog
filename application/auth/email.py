from flask import render_template, current_app
from flask_babel import _

from application.email import send_mail


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_mail("[Microblg] Reset Password",
        sender=current_app.config["ADMINS"][0],
        recipients=[user.email],
        body=render_template("email/reset_password.txt",
                                user=user, token=token),
        html=render_template("email/reset_password.html",
                                user=user, token=token)
    )
