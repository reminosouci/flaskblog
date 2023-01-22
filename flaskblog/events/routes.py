from flask import (render_template, url_for, flash,
                   redirect, request, abort, Blueprint)
from flask_login import current_user, login_required
from flaskblog import db
from flaskblog.models import Event, Worker_Event
from flaskblog.events.forms import EventForm, TimeSheetForm
from flaskblog.decorator import organizer, worker
from flaskblog.tasks import send_sms
from datetime import datetime

events = Blueprint('events', __name__)


@events.route("/event/new", methods=['GET', 'POST'])
@login_required
@organizer
def new_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(title=form.title.data, startdatetime=datetime.combine(form.startdate.data, form.starttime.data),
                      enddatetime=datetime.combine(form.enddate.data, form.endtime.data),
                      address=form.address.data, note_event=form.note_event.data,
                      max_workers_needed=form.max_workers_needed.data, organizer_id=current_user.organizer.id)
        db.session.add(event)
        db.session.commit()
        flash('Your event has been created!', 'success')
        return redirect(url_for('main.home'))
    return render_template('create_event.html', title='New Event',
                           form=form, legend='New Event')


@events.route("/event/<int:event_id>")
def event(event_id):
    event = Event.query.get_or_404(event_id)
    return render_template('event.html', title=event.title, event=event)


@events.route("/event/<int:event_id>/update", methods=['GET', 'POST'])
@login_required
@organizer
def update_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer.user != current_user:
        abort(403)
    form = EventForm()
    if form.validate_on_submit():
        event.title = form.title.data
        event.startdatetime = datetime.combine(form.startdate.data, form.starttime.data)
        event.enddatetime = datetime.combine(form.enddate.data, form.endtime.data)
        event.address = form.address.data
        event.note_event = form.note_event.data
        event.max_workers_needed = form.max_workers_needed.data
        db.session.commit()

        attendees = event.get_accepted_workers + event.get_need_cover_workers + event.get_interested_workers
        print(attendees)
        phone_number_list = [attendee.phone for attendee in attendees]
        message = f"The event '{event.title}' on the {event.startdatetime} has been updated. Please check the details for any changes."
        for phone_number in phone_number_list:
            send_sms.delay(phone_number, message)

        flash('Your event has been updated!', 'success')
        return redirect(url_for('events.event', event_id=event.id))
    elif request.method == 'GET':
        form.title.data = event.title
        form.startdate.data = event.startdatetime.date()
        form.starttime.data = event.startdatetime.time()
        form.enddate.data = event.enddatetime.date()
        form.endtime.data = event.enddatetime.time()
        form.address.data = event.address
        form.note_event.data = event.note_event
        form.max_workers_needed.data = event.max_workers_needed
    return render_template('create_event.html', title='Update Event',
                           form=form, legend='Update Event')


@events.route("/event/<int:event_id>/delete", methods=['POST'])
@login_required
@organizer
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.organizer.user != current_user:
        abort(403)
    db.session.delete(event)
    db.session.commit()
    flash('Your event has been deleted!', 'success')
    return redirect(url_for('main.home'))


@events.route("/event/<int:event_id>/accept_event", methods=['POST'])
@login_required
def accept_event(event_id):
    event = Event.query.get_or_404(event_id)
    # not sure
    # if current_user.worker in event.get_accepted_workers:
    #     abort(403)
    new_worker_event = Worker_Event(event_id=event.id, state='accept', worker=current_user.worker)
    db.session.add(new_worker_event)
    db.session.commit()
    flash('You have been enrolled to this Event!', 'success')
    return redirect(url_for('events.event', event_id=event.id))


@events.route("/event/<int:event_id>/ask_cover_event", methods=['POST'])
# @login_required
def ask_cover_event(event_id):
    event = Event.query.get_or_404(event_id)
    # not sure
    # if current_user.worker in event.get_accepted_workers:
    #     abort(403)
    Worker_Event.query.filter_by(event_id=event.id, worker=current_user.worker).update({'state': 'request cover'})
    db.session.commit()
    flash('You have ask for cover for this Event!', 'success')
    return redirect(url_for('events.event', event_id=event.id))


@events.route("/event/<int:event_id>/cancel_cover_event", methods=['POST'])
@login_required
def cancel_cover_event(event_id):
    event = Event.query.get_or_404(event_id)
    # not sure
    # if current_user.worker in event.get_accepted_workers:
    #     abort(403)
    Worker_Event.query.filter_by(event_id=event.id, worker=current_user.worker).update({'state': 'accept'})
    db.session.commit()
    flash('You have cancelled you request for cover for this Event!', 'success')
    return redirect(url_for('events.event', event_id=event.id))


@events.route("/event/<int:event_id>/update_interest_status", methods=['POST'])
@login_required
def update_interest_status(event_id):
    event = Event.query.get_or_404(event_id)
    interest_status = request.form['interest_status']
    if interest_status == 'add':
        worker_event = Worker_Event(worker_id=current_user.worker.id, event_id=event.id, state='interested')
        db.session.add(worker_event)
    elif interest_status == 'remove':
        worker_event = Worker_Event.query.filter_by(worker_id=current_user.worker.id, event_id=event.id).first()
        db.session.delete(worker_event)
    db.session.commit()
    return redirect(url_for('events.event', event_id=event.id))


@events.route("/calendar")
@login_required
def calendar():
    if current_user.role == 'organizer':
        events = Event.query.order_by(Event.date_posted.asc()).filter_by(
            organizer=current_user.organizer).all()
        return render_template('calendar-organizer.html', events=events)
    elif current_user.role == 'worker':
        worker_events = Worker_Event.query.filter_by(worker=current_user.worker).all()
        return render_template('calendar-worker.html', worker_events=worker_events)


@events.route("/timesheet")
@login_required
def timesheet():
    page = request.args.get('page', 1, type=int)
    if current_user.role == 'organizer':
        events = Event.query.order_by(Event.date_posted.asc()).filter(Event.organizer == current_user.organizer,
                                                                      Event.startdatetime < datetime.now()).paginate(
            page=page, per_page=5)
        return render_template('timesheet-organizer.html', events=events)
    elif current_user.role == 'worker':
        worker_events = Worker_Event.query.filter(Worker_Event.worker == current_user.worker).paginate(page=page,
                                                                                                       per_page=5)
        print(worker_events)
        events = Worker_Event.query.group_by(Worker_Event.event_id).filter_by(worker=current_user.worker).all()

        return render_template('timesheet-worker.html', worker_events=worker_events)


@events.route('/event/<int:event_id>/time-sheet', methods=['GET', 'POST'])
def event_time_sheet(event_id):
    events = Event.query.all()
    for event in events:
        print(event)
        print(event.review_submitted)
    event = Event.query.get_or_404(event_id)
    worker_events = event.worker_event
    forms = []
    if request.method == 'POST':
        print(request.form)
        for worker_event in worker_events:
            worker_event.clock_in_organizer = datetime.strptime(request.form[f'clock_in_{worker_event.worker.id}'],
                                                                "%Y-%m-%dT%H:%M")
            worker_event.clock_out_organizer = datetime.strptime(request.form[f'clock_out_{worker_event.worker.id}'],
                                                                 "%Y-%m-%dT%H:%M")
            worker_event.review = request.form[f'review_{worker_event.worker.id}']
            db.session.commit()
        flash('Time-sheet successfully submitted', 'success')
        # return redirect(url_for('event_timesheet', event_id=event.id))
        return render_template('event_timesheet.html', event=event, worker_events=worker_events)
    else:
        for worker_event in worker_events:
            form = TimeSheetForm()
            forms.append((form, worker_event))
    return render_template('event_timesheet.html', event=event, worker_events=worker_events,
                           forms=forms)



#filter all the events where the timesheet has not been submitted
#    events = Event.query.filter(
#         Event.startdatetime < datetime.now(),
#         Event.organizer_id == current_user.organizer.id,
#         Worker_Event.event_id == Event.id,
#         Worker_Event.review == None).all()