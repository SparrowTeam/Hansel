import logging as log
from datetime import datetime
from functools import wraps
from random import randint
from itertools import cycle

from flask import abort, request
from peewee import (CharField, DateTimeField, FloatField, ForeignKeyField,
                    IntegerField, IntegrityError, Model, PrimaryKeyField,
                    SelectQuery, SqliteDatabase, TextField, UUIDField)

db = SqliteDatabase(database='hansel.db')

mebious_line = cycle([1, 2])


class BaseModel(Model):

    class Meta:
        database = db


class Team(BaseModel):

    id = PrimaryKeyField()
    name = CharField(unique=True, index=True)
    color = CharField(unique=True)

    @staticmethod
    def get_random_team():
        q = Team.select()
        _team_id = int(next(mebious_line))
        return Team.get(Team.id == _team_id)


class User(BaseModel):

    id = PrimaryKeyField()
    email = CharField(unique=True, index=True)
    password = CharField()
    name = CharField()
    registred_at = DateTimeField(default=datetime.utcnow())

    token = CharField()

    photo = CharField(null=True)

    team = ForeignKeyField(Team)

    def update_photo(self, photo_id):
        (User
         .update(photo='/photo/{}'.format(photo_id))
         .where(User.id == self.id))

    def info(self):
        info = (
            User
            .select(User, Team)
            .join(Team)
            .where(User.id == self.id).get())
        return {
            "name": info.name,
            "photo": info.photo,
            "team": {
                "id": info.team.id,
                "name": info.team.name,
                "color": info.team.color
            }
        }


class Mark(BaseModel):

    id = PrimaryKeyField()
    hardware_id = CharField(index=True, unique=True)

    longtitude = FloatField()
    latitude = FloatField()
    altitude = FloatField()
    code = CharField()

    name = CharField(null=True)

    value = IntegerField(default=100)

    registred_at = DateTimeField(default=datetime.utcnow())
    updated_at = DateTimeField(null=True)

    current_user = ForeignKeyField(User, related_name='who_owns')

    def update_mark_owner(self, user):
        (
            Mark
            .update(
                current_user=ser,
                updatetd_at=datetime.utcnow())
            .where(
                Mark.id == self.id,
                Mark.current_user == user)
        )

    def get_info(self):
        mark = (Mark
                .select(Mark)
                .where(Mark.id == self.id)
                .get())
        records = MarkUsersHitory.select().where(MarkUsersHitory.mark == self)
        photos = MarksPhotos.select().where(MarksPhotos.mark == self)
        return {
            'id': mark.hardware_id,
            'related_datetime': {
                'registered': mark.registred_at,
                'updated': mark.updated_at
            },
            'name': mark.name,
            'value': mark.value,
            'coordinates': {
                'longtitude': mark.longtitude,
                'latitude': mark.latitude,
                'altitude': mark.altitude,
                'code': mark.code
            },
            'team': {
                'id': mark.current_user.team.id,
                'color': mark.current_user.team.color
            },
            'users': [{
                'id': rec.user.id,
                'name': rec.user.name,
                'team_color': rec.user.team.color
            } for rec in records],
            'photos': [
                '/photo/{}'.format(p.photo.photo_id) for p in photos
            ]
        }


class MarkUsersHitory(BaseModel):

    id = PrimaryKeyField()
    mark = ForeignKeyField(Mark)
    user = ForeignKeyField(User)

    class Meta:
        indexes = (
            (('user', 'mark'), True),
        )


class Photo(BaseModel):

    id = PrimaryKeyField()
    photo_id = UUIDField(unique=True, index=True)


class MarksPhotos(BaseModel):

    id = PrimaryKeyField()
    photo = ForeignKeyField(Photo)
    mark = ForeignKeyField(Mark, related_name='was_made_for')

    class Meta:
        indexes = (
            (('photo', 'mark'), True),
        )


def create_tables():
    db.connect()
    db.create_tables([Team, User, Mark, MarkUsersHitory,  # Comment,
                      Photo,
                      MarksPhotos], True)
    try:
        Team.select().get()
    except Team.DoesNotExist:
        for n, c in (
                ('Sithes', '#70FF0000'),
                ('Jedi', '#70000FFF')
        ):
            Team.create(name=n, color=c)


def transaction_wrapper(func):

    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            with db.transaction():
                return func(*args, **kwargs)
        except Exception as e:
            db.close()
            log.error('Transaction error')
            log.exception(e)
            abort(502)
    return wrapped
