from flask import Flask
from database import db


app = Flask('hansel')


@app.before_request
def before_req():
    db.connect()

@app.after_request
def after_req(response):
    db.close()
    return response
