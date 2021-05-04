from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l

from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo

from application.models import User


class LoginForm(FlaskForm):
    username = StringField("Usename", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class RegistrationForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired()])
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    confirm_password = PasswordField(_l("Confirm password"), validators=[
        DataRequired(), EqualTo("password")
    ])
    submit = SubmitField(_l("Register"))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_("Username taken, please use a different username"))

    def validate_email(self, email):
        user = User.query.filter_by(username=email.data).first()
        if user is not None:
            raise ValidationError(_("Email taken, please use a different email"))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l("Email"), validators=[DataRequired(), Email()])
    submit = SubmitField(_l("Request password reset"))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    confirm_password = PasswordField(_l("Confirm password"), validators=[
        DataRequired(), EqualTo("password")
    ])
    submit = SubmitField(_l("Reset password"))
