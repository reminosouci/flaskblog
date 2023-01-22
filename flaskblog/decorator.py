from functools import wraps
from flask_login import current_user
from flask import url_for, flash, redirect

def organizer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            flash("You are not logged in", "warning")
            return redirect(url_for('main.home'))
        elif current_user.role == 'worker':
            flash("You are a Team Member, you do not have permission to view that page", "warning")
            return redirect(url_for('main.home'))
        elif not current_user.organizer:
            flash("You haven't filled this form, you do not have permission to view that page", "warning")
            return redirect(url_for('users.account_organizer'))
        return f(*args, **kwargs)

    return decorated_function


def worker(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            flash("You are not logged in", "warning")
            return redirect(url_for('main.home'))
        elif current_user.role == 'organizer':
            flash("You are a Event Organizer, you do not have permission to view that page", "warning")
            return redirect(url_for('main.home'))
        elif current_user.worker == None:
            flash("You haven't filled this form, you do not have permission to view that page", "warning")
            return redirect(url_for('users.account_worker'))
        return f(*args, **kwargs)

    return decorated_function

def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or current_user.role != 'admin' or current_user.is_authenticated:
            flash("You are not an admin", "warning")
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function