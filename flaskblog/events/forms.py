from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length
from wtforms.fields.html5 import DateTimeField, DateField, TimeField


class EventForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=2, max=40)])
    startdate = DateField('Start', format='%Y-%m-%d', validators=[DataRequired()])
    starttime = TimeField('', format='%H:%M')
    enddate = DateField('End', format='%Y-%m-%d', validators=[DataRequired()])
    endtime = TimeField('', format='%H:%M')
    address = StringField('Address', validators=[Length(min=0, max=50)])
    note_event = TextAreaField('Note for the event', validators=[Length(min=0, max=200)])
    max_workers_needed = IntegerField('Number of workers needed', validators=[DataRequired()])
    submit = SubmitField('Post')

class TimeSheetForm(FlaskForm):
    clock_in = DateTimeField('Clock In')
    clock_out = DateTimeField('Clock Out')
    review = IntegerField('Review')