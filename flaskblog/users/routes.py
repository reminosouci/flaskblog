from flask import render_template, url_for, flash, redirect, request, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from flaskblog import db, bcrypt
from flaskblog.models import User, Event, Organizer, Worker, BlackList
from flaskblog.users.forms import (RegistrationForm, LoginForm, UpdateAccountWorkerForm,
                                   UpdateAccountOrganizerForm, RequestResetForm, ResetPasswordForm)
from flaskblog.users.utils import save_picture, send_reset_email
from flaskblog.decorator import organizer, worker

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role=form.role.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account_organizer", methods=['GET', 'POST'])
@login_required
def account_organizer():
    form = UpdateAccountOrganizerForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if current_user.organizer:
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                current_user.organizer.picture = picture_file
            current_user.organizer.company_name = form.company_name.data
            current_user.organizer.name = form.name.data
            current_user.organizer.surname = form.surname.data
            current_user.organizer.phone = form.phone.data
            current_user.organizer.address = form.address.data
            current_user.organizer.note = form.note.data
        else:
            organizer = Organizer(user=current_user, company_name=form.company_name.data, name=form.name.data,
                                  surname=form.surname.data,
                                  phone=form.phone.data, address=form.address.data, note=form.note.data)
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                organizer.picture = picture_file
            db.session.add(organizer)
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account_organizer'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        if current_user.organizer:
            form.company_name.data = current_user.organizer.company_name
            form.name.data = current_user.organizer.name
            form.surname.data = current_user.organizer.surname
            form.phone.data = current_user.organizer.phone
            form.address.data = current_user.organizer.address
            form.note.data = current_user.organizer.note
    if current_user.organizer:
        image_file = url_for('static', filename='profile_pics/' + current_user.organizer.picture)
        return render_template('account-organizer.html', title='Account',
                               image_file=image_file, form=form)
    else:
        return render_template('account-organizer.html', title='Account',
                               image_file="default.jpg", form=form)


@users.route("/account_worker", methods=['GET', 'POST'])
@login_required
def account_worker():
    form = UpdateAccountWorkerForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if current_user.worker:
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                current_user.worker.picture = picture_file
            current_user.worker.name = form.name.data
            current_user.worker.surname = form.surname.data
            current_user.worker.phone = form.phone.data
            current_user.worker.address = form.address.data
            current_user.worker.note = form.note.data
            current_user.worker.date_birth = form.date_birth.data
        else:
            worker = Worker(user=current_user, name=form.name.data, surname=form.surname.data,
                            phone=form.phone.data, address=form.address.data, note=form.note.data,
                            date_birth=form.date_birth.data)
            if form.picture.data:
                picture_file = save_picture(form.picture.data)
                worker.picture = picture_file
            db.session.add(worker)
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account_worker'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        if current_user.worker:
            form.date_birth.data = current_user.worker.date_birth
            form.name.data = current_user.worker.name
            form.surname.data = current_user.worker.surname
            form.phone.data = current_user.worker.phone
            form.address.data = current_user.worker.address
            form.note.data = current_user.worker.note

    if current_user.worker:
        image_file = url_for('static', filename='profile_pics/' + current_user.worker.picture)
        return render_template('account-worker.html', title='Account',
                               image_file=image_file, form=form)
    else:
        return render_template('account-worker.html', title='Account',
                               image_file="default.jpg", form=form)


@users.route("/user/<string:username>")
def user_events(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    events = Event.query.filter_by(organizer=user.organizer) \
        .order_by(Event.date_posted.desc()) \
        .paginate(page=page, per_page=5)
    return render_template('user_events.html', events=events, user=user)


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)


@users.route("/black-list", methods=['GET', 'POST'])
def black_list():
    if request.method == 'POST':
        data = request.get_json()
        print(data)
        workerId = data['workerId']
        blacklistValue = data['blacklistValue']
        worker = Worker.query.get(workerId)
        organizer = current_user.organizer
        if blacklistValue == 'add':
            blacklist = BlackList(organizer=organizer, worker=worker)
            db.session.add(blacklist)
            db.session.commit()
        elif blacklistValue == 'remove':
            blacklist = BlackList.query.filter_by(organizer=organizer, worker=worker).first()
            db.session.delete(blacklist)
            db.session.commit()
    page = request.args.get('page', 1, type=int)
    workers = Worker.query.paginate(page=page, per_page=5)
    return render_template('black-list.html', title='Update your black list of workers', workers=workers)
