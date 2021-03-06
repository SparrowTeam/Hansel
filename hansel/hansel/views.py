from base64 import b64decode, b64encode
from functools import wraps
from os.path import abspath, dirname
from pathlib import Path
from random import randint
from uuid import uuid4

from flask import (Flask, abort, jsonify, make_response, request,
                   send_from_directory)

from database import (IntegrityError, Mark, MarksPhotos, MarkUsersHitory,
                      Photo, SelectQuery, Team, User, db, transaction_wrapper)

app = Flask('hansel')

MEDIA_DIR = Path(dirname(abspath(__file__))) / 'media'


def is_authorized(func):

    @wraps(func)
    def wrapped(*args, **kwargs):
        token = request.headers.get('X-API-TOKEN')
        if token is None:
            return error(409, 'Head X-API-TOKEN is reqiered')
        try:
            request.current_user = User.get(User.email == b64decode(token))
            return func(*args, **kwargs)
        except User.DoesNotExist:
            return error(408, "User with token {} not found".format(token))

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


@app.route('/marks/<mark_id>', methods=['POST'])
@transaction_wrapper
@is_authorized
def register_mark(mark_id):
    body = request.get_json(force=True)
    mark = Mark.create(
        hardware_id=mark_id,
        name=body['name'],
        value=randint(100, 1000),
        current_user=request.current_user,
        **body['coordinates']
    )
    MarkUsersHitory.create(
        mark=mark,
        user=request.current_user
    )
    for photo in body['photos']:
        MarksPhotos.create(
            mark=mark,
            photo=Photo.select().where(Photo.photo_id == photo['image_id']).get()
        )
    return jsonify({'mark_id': mark_id})


@app.route('/photo', methods=['POST'])
@transaction_wrapper
@is_authorized
def upload_photo():
    return jsonify({'image_id': _upload_photo()})

@app.route('/user/photo', methods=['POST'])
@transaction_wrapper
@is_authorized
def upload_user_photo():
    request.current_user.update_photo(_upload_photo())
    return error(200, "Yay!")

def _upload_photo():
    if len(request.files) == 0:
        return error(404, "No one file wasn't sended")
    new_file = request.files['upload']
    file_name = str(uuid4())
    Photo.create(
        photo_id=file_name
    )
    new_file.save(str(MEDIA_DIR / file_name))
    return file_name


@transaction_wrapper
@app.route('/mark/<mark_id>/status', methods=['GET'])
@is_authorized
def mark_status(mark_id):
    try:
        mark = (Mark
                .select(Mark, User)
                .join(User)
                .where(Mark.hardware_id == mark_id).get())
    except Mark.DoesNotExist:
        return error(202, 'Can register thouse mark')
    if mark.current_user.id == request.current_user.id:
        return error(201, 'It is your own mark')
    if mark.current_user.team == request.current_user.team:
        return error(403, 'Your team owns thouse mark')
    mark.update_mark_owner(request.current_user)
    return error(200, 'Conquere thouse mark')


@transaction_wrapper
@app.route('/marks/<mark_id>', methods=['GET'])
@is_authorized
def mark_info(mark_id):
    return _marks_info(mark_id)


@transaction_wrapper
@app.route('/marks', methods=['GET'])
@is_authorized
def marks():
    return _marks_info()


@transaction_wrapper
@app.route('/user/marks', methods=['GET'])
@is_authorized
def user_own_marks():
    return _marks_info(user=request.current_user)


@transaction_wrapper
@app.route('/user/marks/<user_id>', methods=['GET'])
@is_authorized
def user_marks(user_id):
    return _marks_info(user=User.select().where(User.id == user_id).get())


def _marks_info(mark_id=None, user=None):
    prepared_query = Mark.select()
    if not (mark_id is None):
        prepared_query = prepared_query.where(Mark.hardware_id == mark_id)
    if not (user is None):
        prepared_query = prepared_query.where(Mark.current_user == user)

    try:
        marks = prepared_query.execute()
    except Mark.DoesNotExist:
        return error(202, 'Can register thouse mark')

    marks_list = []
    for mark in marks:
        marks_list.append(mark.get_info())
    if not (mark_id is None):
        marks_list = marks_list[0]
    return jsonify(marks_list)


@app.route('/photo/<image_id>', methods=['GET'])
@is_authorized
def get_image(image_id):
    return send_from_directory(MEDIA_DIR, image_id)
