from flask_wtf import FlaskForm
from flask_babel import _, lazy_gettext as _l

from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, Length

from application.models import User

class EditProfileForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired()])
    about_me = TextAreaField(_l("About me"), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l("Save"))

    def __init__(self, username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_("Username already taken"))

class FollowUnfollowForm(FlaskForm):
    submit = SubmitField("Submit")


class PostForm(FlaskForm):
    post = TextAreaField(_l("Say something"), validators=[
        DataRequired(), Length(min=1,max=140)
    ])
    submit = SubmitField(_l("Submit"))