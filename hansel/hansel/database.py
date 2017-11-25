from peewee import Model, CharField, DateTimeField, IntegerField, \
    ForeignKeyField, FloatField, TextField, UUIDField, IntegrityError, \
    SqliteDatabase, PrimaryKeyField

from datetime import datetime
from flask import abort, request
from functools import wraps
import logging as log
from random import randint

db = SqliteDatabase(database='hansel.db')


class BaseModel(Model):

    class Meta:
        database=db


class Team(BaseModel):

    id = PrimaryKeyField()
    name = CharField(unique=True, index=True)
    color = CharField(unique=True)

    @staticmethod
    def get_random_team():
        a = Team.select()
        team_counts = randint(1, a.count())
        return Team.get(Team.id == team_counts)



class User(BaseModel):

    id = PrimaryKeyField()
    email = CharField(unique=True, index=True)
    password = CharField()
    name = CharField()
    registred_at = DateTimeField(default=datetime.utcnow())

    token = CharField()

    team = ForeignKeyField(Team)

    def info(self):
        info = (
            User
            .select(User, Team)
            .join(Team)
            .where(User.id == self.id).get())
        return {
            "name": info.name,
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

    value = IntegerField(default=5)

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


class MarkUsersHitory(BaseModel):

    id = PrimaryKeyField()
    mark = ForeignKeyField(Mark)
    user = ForeignKeyField(User)

    class Meta:
        indexes = (
            (('user', 'mark'), True),
        )

# class Comment(BaseModel):

#     id = PrimaryKeyField()
#     created_at = DateTimeField(default=datetime.utcnow())
#     text = TextField()

#     user = ForeignKeyField(User, related_name='commanted_by')
#     mark = ForeignKeyField(Mark, related_name='commented_on')

#     class Meta:
#         indexes = (
#             (('user', 'mark'), True),
#         )


class Photo(BaseModel):

    id = PrimaryKeyField()
    photo_id = UUIDField(unique=True, index=True)

    # longtitude = FloatField()
    # latitude = FloatField()
    # altitude = FloatField()
    # code = CharField()

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
    db.create_tables([Team, User, Mark, MarkUsersHitory, # Comment,
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

def transaction_wrapper(func, *args, **kwargs):

    @wraps(func)
    def wrapped():
        try:
            with db.transaction():
                log.debug('Handle request %s', request)
                return func(*args, **kwargs)
        except Exception as e:
            db.close()
            log.error('Transaction error')
            log.exception(e)
            abort(502)
    return wrapped
