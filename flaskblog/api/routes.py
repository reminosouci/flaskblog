from flask import current_app as app
from flask import Blueprint, request, jsonify, make_response
from flaskblog.models import User
from flaskblog import bcrypt
from functools import wraps
import jwt
import datetime

restfulapi = Blueprint('restfulapi', __name__)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


@restfulapi.route('/api_login', methods=['POST'])
def api_login():
    auth = request.authorization
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return make_response('Missing email or password', 400)
    user = User.query.filter_by(email=email).first()
    if user and bcrypt.check_password_hash(user.password, password):
        token = jwt.encode({'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
                           app.config['SECRET_KEY'])
        return jsonify({'token': token, 'user_id': user.id, 'email': user.email})
    return make_response('Invalid email or password', 401)

