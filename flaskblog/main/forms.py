from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length
from wtforms.fields.html5 import DateTimeField, DateField, TimeField



class FilterForm(FlaskForm):
    interest = BooleanField('Interested')
    accept = BooleanField('Attending')
    need_cover = BooleanField('Needing Cover')
    startdate = DateField('Start', format='%Y-%m-%d')
    enddate = DateField('End', format='%Y-%m-%d')
    search_text = StringField('Search', validators=[Length(min=0, max=20)])
    submit = SubmitField('Filter')