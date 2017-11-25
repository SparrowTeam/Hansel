from database import db, create_tables
from views import app


@app.before_request
def before_req():
    db.connect()


@app.after_request
def after_req(response):
    db.close()
    return response

def main():
    create_tables()
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=True
    )

if __name__=='__main__':
    main()
