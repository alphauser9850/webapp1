from flask_wtf import FlaskForm
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
    ])

class TicketStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed')
    ], validators=[validators.DataRequired()]) 