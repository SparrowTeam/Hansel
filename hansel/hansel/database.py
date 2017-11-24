from peewee import PooledSqliteDatabase, Model, CharField, DateTimeField,\
    ForeignKeyField, FloatField
from datetime import datetime

db = PooledSqliteDatabase(database='hansel.db')

class BaseModel(Model):

    class Meta:
        database=db


class Team(BaseModel):

    name = CharField(unique=True)
    color = CharField(unique=True)


class User(BaseModel):

    email = CharField(unique=True)
    password = CharField()
    name = CharField()
    registred_at = DateTimeField(default=datetime.utcnow())

    team = ForeignKeyField(Team)


class Mark(BaseModel):

    hardware_id = CharField()
    longtitude = FloatField()
    latitude = FloatField()
    altitude = FloatField()
    value = IntegerField(default=5)
