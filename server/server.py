#!/usr/bin/env python3
import argparse
from sys import argv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
import ydb
import ydb.iam

import os
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "yql+ydb://dummy_url:2135"
db = SQLAlchemy(app)

with app.app_context():
    @sa.event.listens_for(db.engine, "do_connect")
    def provide_token(dialect, conn_rec, cargs, cparams):
        driver = ydb.Driver(
          endpoint='grpcs://ydb.serverless.yandexcloud.net:2135',
          database='/ru-central1/b1gq3fjp39rvbfkapjns/etnr359bpbdiq83sm41h',
          credentials=ydb.iam.MetadataUrlCredentials(),
        )
        driver.wait(fail_fast=True, timeout=5)
        cparams["ydb_session_pool"] = ydb.SessionPool(driver)

# with engine.connect() as conn:
#   rs = conn.execute(sa.text("SELECT 1 AS value"))
#   print(rs.fetchone())


# def execute_query(session):
#   # Create the transaction and execute query.
#   return session.transaction().execute(
#     'select 1 as cnt;',
#     commit_tx=True,
#     settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
#   )
# def handler():
#   # Execute query with the retry_operation helper.
#   result = pool.retry_operation_sync(execute_query)
#   return {
#     'statusCode': 200,
#     'body': str(result[0].rows[0].cnt == 1),
#   }

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    handle = db.Column(db.String(64), index = True, unique = True)
    token = db.Column(db.String(64))
    def __repr__(self):
        return '<Admin %r>' % (self.handle)

def generate_token():
    return "todo: token"

@app.route('/api/1.0/admin', methods=['POST'])
def create_admin():
    if not request.json or not 'handle' in request.json:
        abort(400)
    admin = models.Admin(
                handle = request.json['handle'],
                token = generate_token(),
            )
    db.session.add(admin)
    db.session.commit()
    return "OK", 200

@app.route('/api/1.0/admin', methods=['GET'])
def get_admin():
    return jsonify(models.User.query.all()), 200

parser = argparse.ArgumentParser(prog="kserver-dispatch")
parser.add_argument('--db_ip', nargs=1, required=True)

def main():
    with app.app_context():
        db.create_all()

    args = parser.parse_args(argv[1:])

    try:
        db_ip = args.db_ip[0]
    except:
        print("Db ip is undefined")
        return 0

    print("Using database ip is:", db_ip)

    app.run(host='0.0.0.0', port=8080, debug=True)

if __name__ == "__main__":
    main()
