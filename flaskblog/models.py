from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from sqlalchemy import select, func, and_, event
from flaskblog import db, login_manager
from flask_login import UserMixin
import pytz
from math import modf
from sqlalchemy.ext.hybrid import hybrid_property
from flaskblog.script import get_latitude_longitude
from datetime import date
from flask_admin.contrib.sqla import ModelView

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    date_registration = db.Column(db.DateTime(), default=datetime.now(pytz.timezone('Australia/Melbourne')))
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(9), default='nan', nullable=False)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)


class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(20), nullable=True)
    surname = db.Column(db.String(20), nullable=True)
    picture = db.Column(db.String(20), nullable=False, default='worker-default.jpg')
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(50), nullable=True)
    note = db.Column(db.Text, nullable=True)
    date_birth = db.Column(db.Date, nullable=True)
    review = db.Column(db.Float(), default=0)
    nb_vote = db.Column(db.Integer(), default=0)
    user = db.relationship("User", backref=db.backref("worker", uselist=False))
    blacklisted_organizer = db.relationship("BlackList", back_populates="worker")

    @property
    def is_blacklisted_by(self, organizer):
        return any(blacklist.organizer == organizer for blacklist in self.blacklisted_organizer)

    @property
    def age(self):
        today = date.today()
        age = today.year - self.date_birth.year
        if today < date(today.year, self.date_birth.month, self.date_birth.day):
            age -= 1
        return age

    @property
    def get_star_html(self):
        # Round the review to the nearest integer
        review = round(self.review)
        decimal_review = modf(self.review)[0]
        star_html = ""
        # Add the full yellow stars
        for i in range(review):
            star_html += '<i class="fas fa-star"></i>'
        # Check if the review is a fractional number

        if decimal_review < 0.25:
            star_html += '<i class="far fa-star"></i>'
        elif decimal_review >= 0.75:
            star_html += '<i class="fas fa-star"></i>'
        else:
            star_html += '<i class="fas fa-star-half-alt"></i>'
        # Add the remaining grey stars
        for i in range(4 - review):
            star_html += '<i class="far fa-star"></i>'
        # jinja code {{ worker.get_star_html | safe }}
        return star_html + f" ({self.nb_vote})"


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=True)
    date_posted = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Australia/Melbourne')))
    startdatetime = db.Column(db.DateTime, nullable=True)
    enddatetime = db.Column(db.DateTime, nullable=True)
    address = db.Column(db.String(50), nullable=True)
    note_event = db.Column(db.Text, nullable=True)
    max_workers_needed = db.Column(db.Integer(), default=0)
    organizer_id = db.Column(db.Integer, db.ForeignKey('organizer.id'), nullable=False)
    latitude = db.Column(db.Float(), nullable=True)
    longitude = db.Column(db.Float(), nullable=True)

    def nb_worker_event_accepted_needingcover(self):
        return Worker_Event.query.filter(Worker_Event.event_id == self.id,
                                         Worker_Event.state.in_(['accepted', 'looking for recovery'])).count()

    @hybrid_property
    def available(self):
        return self.max_workers_needed - Worker_Event.query.filter_by(event_id=self.id, state='accept').count()

    @available.expression
    def available(cls):
        return cls.max_workers_needed - (select([func.count(Worker_Event.id)]).where(
            and_(Worker_Event.event_id == cls.id, Worker_Event.state == 'accept')
        )
        )

    @property
    def text_start_end_datetime(self):
        delta = self.enddatetime - self.startdatetime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        duration = f"{hours}H{minutes:02d} long"
        start_string = self.startdatetime.strftime("%a, %d %b %I:%M %p")
        return f"{start_string} {duration}"

    @property
    def text_address(self):
        text_address = ""
        if self.address_1:
            text_address = str(self.address_1) + ", "
        if self.address_2:
            text_address = str(self.address_2) + ", "
        return f"{text_address}{self.town}, {self.zip}, {self.state}"

    @property
    def get_accepted_workers(self):
        accepted_worker_events = Worker_Event.query.filter_by(event_id=self.id, state='accept').all()
        accepted_workers = []
        for worker_event in accepted_worker_events:
            accepted_workers.append(worker_event.worker)
        return accepted_workers

    @property
    def get_need_cover_workers(self):
        need_cover_workers_events = Worker_Event.query.filter_by(event_id=self.id, state='request cover').all()
        need_cover_workers = []
        for worker_event in need_cover_workers_events:
            need_cover_workers.append(worker_event.worker)
        return need_cover_workers

    @property
    def get_interested_workers(self):
        interested_workers_events = Worker_Event.query.filter_by(event_id=self.id, state='interested').all()
        interested_workers = []
        for worker_event in interested_workers_events:
            interested_workers.append(worker_event.worker)
        return interested_workers

    def nb_worker_event_accepted_needingcover(self):
        return Worker_Event.query.filter(Worker_Event.event_id == self.id,
                                         Worker_Event.state.in_(['accepted', 'request cover'])).count()

    @property
    def get_google_map_iframe(self):
        api_key = "AIzaSyCLYCsyffL84AgTvNV79Tp-IvAm_OcaQcE"
        address = self.address.replace(" ", "+")
        # jinja code {{ event.get_google_map_iframe | safe }}
        return f'<iframe width="320" height="300" frameborder="0" style="border:0" src="https://www.google.com/maps/embed/v1/place?key={api_key}&q={address}&zoom=11" allowfullscreen></iframe>'

    @property
    def start_time_passed(self):
        return self.startdatetime < datetime.now()

    # @property
    # def events_with_incomplete_reviews(self):
    #     # Use filter() to check that all the columns `clock_in_organizer`, `clock_out_organizer` and `review` are `None`
    #     return Event.query.join(Worker_Event).filter(Worker_Event.clock_in_organizer == None,
    #                                                  Worker_Event.clock_out_organizer == None,
    #                                                  Worker_Event.review == None).all()
    @property
    def review_submitted(self):
        return any(we.review is not None for we in self.worker_event)




class Organizer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    company_name = db.Column(db.String(30), nullable=True)
    name = db.Column(db.String(20), nullable=True)
    surname = db.Column(db.String(20), nullable=True)
    picture = db.Column(db.String(20), nullable=False, default='worker-default.jpg')
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(50), nullable=True)
    note = db.Column(db.Text, nullable=True)
    user = db.relationship("User", backref=db.backref("organizer", uselist=False))
    list_event = db.relationship("Event", backref='organizer')
    blacklisted_worker = db.relationship("BlackList", back_populates="organizer")
    @property
    def workers_blacklisted(self):
        return [blacklist.worker for blacklist in self.blacklisted_worker]

    @property
    def unfinished_events(self):
        # list of events where review not done by Organizer yet
        return Event.query.join(Worker_Event).filter(Event.organizer_id == self.id, Worker_Event.review == None).all()


class Worker_Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    state = db.Column(db.String(10), default='pending')
    clock_in_worker = db.Column(db.DateTime, nullable=True)
    clock_out_worker = db.Column(db.DateTime, nullable=True)
    clock_in_organizer = db.Column(db.DateTime, nullable=True)
    clock_out_organizer = db.Column(db.DateTime, nullable=True)
    review = db.Column(db.Integer(), nullable=True)
    created_organizer = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Australia/Melbourne')))
    worker = db.relationship(Worker, backref=db.backref("worker_event", cascade="all, delete-orphan"))
    event = db.relationship(Event, backref=db.backref("worker_event", cascade="all, delete-orphan"))


class BlackList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey('organizer.id'), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    organizer = db.relationship("Organizer", back_populates="blacklisted_worker")
    worker = db.relationship("Worker", back_populates="blacklisted_organizer")
    @property
    def is_worker_in_blacklist(self):
        return self.worker in self.organizer.blacklist

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    content = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Australia/Melbourne')))
    read = db.Column(db.Boolean, default=False)
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])
    event = db.relationship("Event", backref='message')







def update_geolocation(mapper, connection, target):
    # get the latitude and longitude of the address
    address, lat, long = get_latitude_longitude(target.address)
    # update the event object with the latitude and longitude
    target.latitude = lat
    target.longitude = long
    target.address = address
event.listen(Event, 'before_update', update_geolocation)
event.listen(Event, 'before_insert', update_geolocation)


