from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, FileField
from wtforms.validators import DataRequired, EqualTo, ValidationError
from .models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('readonly', 'Read Only'), ('power', 'Power User'), ('admin', 'Admin')], default='readonly')
    submit = SubmitField('Add User')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Please use a different username.')

class UploadInventoryForm(FlaskForm):
    file = FileField('Inventory File (CSV/XLS)', validators=[DataRequired()])
    submit = SubmitField('Upload & Initialize')

class CaptureForm(FlaskForm):
    snapshot_name = StringField('Snapshot Name', validators=[DataRequired()])
    submit = SubmitField('Capture Snapshot')

class ValidateForm(FlaskForm):
    baseline_id = SelectField('Baseline Snapshot', validators=[DataRequired()])
    submit = SubmitField('Validate Current State')
