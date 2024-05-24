#!/usr/bin/env python3
import argparse
import secrets
from sys import argv
from flask import Flask, jsonify, request, abort
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

class Admin(Base):
    __tablename__ = 'admins'

    handle = sa.Column(sa.String(64), primary_key=True)
    token = sa.Column(sa.String(64), nullable=False)

class Project(Base):
    __tablename__ = 'projects'
    token = sa.Column(sa.String(64), nullable=False)
    handle = sa.Column(sa.String(64), nullable=False, index=True, primary_key=True)
    name = sa.Column(sa.String(64), nullable=False, primary_key=True)
    def __repr__(self):
        return '<Project %r(%r-%r)>' % (self.proj_id, self.proj_handle, self.admin_handle)

class Host(Base):
    __tablename__ = 'hosts'
    port = sa.Column(sa.Integer, primary_key=True)
    token = sa.Column(sa.String(64), nullable=False)
    proj_token = sa.Column(sa.String(64), nullable=False)
    def __repr__(self):
        return '<Host on port %r for project %r>' % (self.port, self.proj_id)

def generate_token(pref):
    return f"{pref}_{secrets.token_urlsafe(16)}"

@app.route('/api/admin/register/', methods=['GET'])
def register_admin():
    if not 'handle' in request.args:
        abort(400)
    with db_engine.connect() as conn:
        handle = request.args['handle']
        rs = conn.execute(sa.text(f"""SELECT admins.handle, admins.token
                                      FROM admins WHERE admins.handle = '{handle}'""")).fetchall()
        print(rs)
        if len(rs) != 0:
            abort(406)
        # success, create user
        token = generate_token("adm")
        conn.execute(sa.text(f"INSERT INTO admins (handle, token) VALUES ('{handle}', '{token}')"))
        return token, 200

@app.route('/api/service/register', methods=['POST'])
def register_service():
    if not request.json \
        or not 'name' in request.json \
        or not 'admin_token' in request.json:
        abort(400)
    with db_engine.connect() as conn:
        name = request.json['name']
        admin_token = request.json['admin_token']
        rs = conn.execute(sa.text(f"""SELECT admins.handle
                                      FROM admins WHERE admins.token = '{admin_token}'""")).fetchall()
        if len(rs) == 0:
            abort(403)
        elif len(rs) > 1:
            abort(500)
        else:
            handle = rs[0][0]
            token = generate_token("prj")
            try:
                conn.execute(sa.text(f"INSERT INTO projects (token, handle, name) \
                                       VALUES ('{token}', '{handle}', '{name}')"))
            except:
                abort(406)
            return token, 200



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
