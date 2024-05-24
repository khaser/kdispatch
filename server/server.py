#!/usr/bin/env python3
import argparse
from sys import argv
from flask import Flask, jsonify, request
# from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
import sqlalchemy.orm as orm
import ydb
import ydb.iam

import os
basedir = os.path.abspath(os.path.dirname(__file__))

Base = orm.declarative_base()

driver = ydb.Driver(
  endpoint='grpcs://ydb.serverless.yandexcloud.net:2135',
  database='/ru-central1/b1gq3fjp39rvbfkapjns/etnr359bpbdiq83sm41h',
  credentials=ydb.iam.MetadataUrlCredentials(),
)
driver.wait(fail_fast=True, timeout=5)
pool = ydb.SessionPool(driver)
db_engine = sa.create_engine("yql+ydb://ydb.serverless.yandexcloud.net:2135/ru-central1/b1gq3fjp39rvbfkapjns/etnr359bpbdiq83sm41h",
                             connect_args={"ydb_session_pool": pool})

app = Flask(__name__)

class Admins(Base):
    __tablename__ = 'admins'

    handle = sa.Column(sa.String(64), primary_key=True)
    token = sa.Column(sa.String(64))

class Project(Base):
    __tablename__ = 'projects'
    proj_id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    token = sa.Column(sa.String(64), nullable=False)
    admin_handle = sa.Column(sa.String(64), nullable=False, index=True)
    proj_handle = sa.Column(sa.String(64), nullable=False)
    def __repr__(self):
        return '<Project %r(%r-%r)>' % (self.proj_id, self.proj_handle, self.admin_handle)

class Host(Base):
    __tablename__ = 'hosts'
    port = sa.Column(sa.Integer, primary_key=True)
    token = sa.Column(sa.String(64), nullable=False)
    proj_id = sa.Column(sa.Integer, nullable=False, index=True)
    def __repr__(self):
        return '<Host on port %r for project %r>' % (self.port, self.proj_id)

def generate_token():
    return "todo: token"

@app.route('/api/1.0/admin', methods=['POST'])
def create_admin():
    if not request.json or not 'handle' in request.json:
        abort(400)
    with db_engine.connect() as conn:
        conn.execute(sa.text("""
                             INSERT INTO admins (handle, token) VALUES ({}, {})
                             """.format(request.json['handle'], generate_token())))

    return "OK", 200

@app.route('/api/1.0/admin', methods=['GET'])
def get_admin():
    res = [] # [{ "handle": x.handle, "token": x.token } for x in Admin.query.all()]
    return jsonify(res), 200

parser = argparse.ArgumentParser(prog="kserver-dispatch")
parser.add_argument('--db_ip', nargs=1, required=True)

def main():
    with db_engine.connect() as conn:
        Base.metadata.drop_all(conn.engine)
        Base.metadata.create_all(conn.engine)

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
