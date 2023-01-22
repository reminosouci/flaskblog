from flask import render_template, request, Blueprint, url_for, flash, redirect, jsonify
from flaskblog.models import Event, Organizer, BlackList, Worker_Event
from flask_login import current_user, login_required
from sqlalchemy import and_, exists, or_
from datetime import datetime
from flaskblog.main.forms import FilterForm
from flaskblog.decorator import organizer, worker, is_admin



main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    if current_user.is_anonymous:
        return render_template('home-anonymous.html', title='Home')
    if not current_user.organizer and current_user.role == "organizer":
        flash('You need to update your details', 'warning')
        return redirect(url_for('users.account_organizer'))
    if not current_user.worker and current_user.role == "worker":
        flash('You need to update your details', 'warning')
        return redirect(url_for('users.account_worker'))
    if current_user.organizer:
        page = request.args.get('page', 1, type=int)
        events = Event.query.filter(Event.organizer_id == current_user.id).order_by(Event.date_posted.desc()).paginate(
            page=page, per_page=5)
        return render_template('home-organizer.html', title="Event to come", events=events)
    if current_user.worker:
        # filter the events where the current user is in the black list of the black list of the organizer and where the startdatetime is earlier than the current time.
        events = Event.query.join(Organizer, Event.organizer_id == Organizer.id).outerjoin(BlackList,
                                                                                           Organizer.id == BlackList.organizer_id).filter(
            Event.startdatetime > datetime.utcnow(),
            ~exists().where(BlackList.worker_id == current_user.worker.id)  # ,Event.available>0
        ).paginate(page=page, per_page=5)

        return render_template('home-worker.html', title="Event to come", events=events)
    events = Event.query.paginate(page=page, per_page=5)
    return render_template('home-worker.html', title="Event to come", events=events)


@main.route("/about")
def about():
    return render_template('about.html', title='About')
















@main.route("/home2")
def home2():
    return render_template('home2.html', title='About')