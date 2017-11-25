from flask import Flask
from flask import request, jsonify, abort, make_response
from database import db, User, transaction_wrapper, Team, IntegrityError, \
    Mark, Photo, MarksPhotos
from base64 import b64encode, b64decode
from functools import wraps
from werkzeug.utils import secure_filename
from pathlib import Path
from os.path import abspath, dirname
from uuid import uuid4

app = Flask('hansel')

MEDIA_DIR = Path(dirname(abspath(__file__))) / 'media'


def is_authorized(func, *args, **kwargs):

    @wraps(func)
    def wrapped():
        token = request.headers.get('X-API-TOKEN')
        if token is None:
            return error(409, 'Head X-API-TOKEN is reqiered')
        try:
            request.current_user = User.get(User.email == b64decode(token))
            return func(*args, **kwargs)
        except User.DoesNotExist:
            return error(404, "User with token {} not found".format(token))

    return wrapped

def error(code, mess):
    resp = jsonify({'error': mess})
    resp.status = str(code)
    return resp


@app.route('/user/register', methods=['POST'])
@transaction_wrapper
def user_regiter():
    body = request.get_json(force=True)
    try:
        user = User.create(
            email=body['email'],
            password=body['password'],
            name=body['name'],
            token=b64encode(body['email'].encode('utf-8')).decode('utf-8'),
            team=Team.get_random_team()
        )
    except IntegrityError:
        return error(404, "User not found")
    return jsonify({'token': user.token})


@app.route('/user/login', methods=['POST'])
@transaction_wrapper
def user_login():
    body = request.get_json(force=True)
    try:
        user = User.get(
            (User.email == body['email']) &
            (User.password == body['password'])
        )
    except User.DoesNotExist:
        return error(404, "User not found")
    return jsonify({'token': user.token})


@app.route('/user/info', methods=['GET'])
@transaction_wrapper
@is_authorized
def user_info():
    return jsonify(request.current_user.info())

@app.route('/mark/<mark_id>', methods=['POST'])
@transaction_wrapper
@is_authorized
def register_mark(mark_id):
    body = request.get_json(force=True)
    mark = Mark.create(
        hardware_id=mark_id,
        name=body['name'],
        value=5,
        current_user=request.current_user,
        registred_at=body['registred_at'],
        **body['coordinates']
    )
    for photo_id in body['photos']:
        MarksPhotos.create(
            mark=mark,
            photo=photo_id
        )
    abort(200)

@app.route('/photo', methods=['POST'])
@transaction_wrapper
@is_authorized
def upload_photo():
    if len(request.files) == 0:
        return error(404, "No one file wasn't sended")
    files = []
    for new_file in request.files:
        file_name = str(uuid4())
        Photo.create(
            photo_id=file_name
        )
        new_file.save(MEDIA_DIR, file_name)
        files.append(file_name)

    return jsonify(files)
