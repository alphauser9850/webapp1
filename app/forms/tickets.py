from flask_wtf import FlaskForm
<<<<<<< HEAD
from wtforms import StringField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length

class TicketForm(FlaskForm):
    subject = StringField('Subject', validators=[
        DataRequired(),
        Length(min=5, max=100, message='Subject must be between 5 and 100 characters')
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], validators=[DataRequired()])
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=10, max=2000, message='Message must be between 10 and 2000 characters')
    ])

class MessageForm(FlaskForm):
    content = TextAreaField('Message', validators=[
        DataRequired(),
        Length(min=1, max=2000, message='Message must be between 1 and 2000 characters')
=======
from wtforms import StringField, TextAreaField, SelectField, validators

class TicketForm(FlaskForm):
    """Form for creating a new ticket."""
    subject = StringField('Subject', [
        validators.DataRequired(),
        validators.Length(min=3, max=255)
    ])
    message = TextAreaField('Message', [
        validators.DataRequired(),
        validators.Length(min=10)
    ])
    priority = SelectField('Priority', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], default='low')

class MessageForm(FlaskForm):
    """Form for adding a message to a ticket."""
    message = TextAreaField('Message', [
        validators.DataRequired(),
        validators.Length(min=1)
>>>>>>> master
    ])

class TicketStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed')
<<<<<<< HEAD
    ], validators=[DataRequired()]) 
=======
    ], validators=[validators.DataRequired()]) 
>>>>>>> master
