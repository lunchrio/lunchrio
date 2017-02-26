# -*- coding: utf-8 -*-
from flask import Flask
from flask import Response, make_response
from flask import render_template, request, redirect, url_for
from flask import g
from flask import jsonify

from flask_bootstrap import Bootstrap

import os
import sqlite3
from collections import defaultdict
import random
from functools import wraps

import logging
from logging.handlers import RotatingFileHandler

from models import Kayttaja, Paikka, Ominaisuudet, Etaisyys, Jaahy

dev = bool(os.getenv('DEV', False))

if dev:
    DATABASE = 'ruoka.db'
else:
    import psycopg2
    import psycopg2.extras
    DATABASE = os.getenv('DATABASE_URL')

app = Flask(__name__)
Bootstrap(app)

def add_response_headers(headers={}):
    """This decorator adds the headers passed in to the response"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            resp = make_response(f(*args, **kwargs))
            h = resp.headers
            for header, value in headers.items():
                h[header] = value
            return resp
        return decorated_function
    return decorator


def apiheaders(f):
    """This decorator passes X-Robots-Tag: noindex"""
    @wraps(f)
    @add_response_headers({'Content-type': 'application/json'})
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.cookies.get('username') is None:
            return redirect(url_for('login', next=request.url))
        g.user = request.cookies.get('username')
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    if dev:
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    else:
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = psycopg2.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'GET':
        return render_template("index.html")
    else:
        winner = get_rand(request.form.get('kiirus'))
        decrease_cooldowns()
        set_cooldown(winner['id'], 5)

        return render_template("rand.html", voittaja=winner)
        
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'GET':
        return render_template("add.html", method='GET')
    else:
        save_to_db(request.form)
        return render_template("add.html", method='POST', values=request.form)

@app.route('/delete', methods=['GET'])
@login_required
def delete():
    delete_with_id(request.args.get('id'))
    return redirect(url_for('list_'))

@app.route('/list')
@login_required
def list_():
    return render_template("list.html", rows=get_from_db())

@app.route('/update')
@login_required
def update():
    decrease_cooldowns()
    return redirect(url_for('list_'))

@app.route('/setcd/<int:id>')
@login_required
def set_cd(id):
    set_cooldown(id, 5)
    return redirect(url_for('list_'))

@app.route('/reset')
@login_required
def reset():
    reset_cd(request.args.get('id'))
    return redirect(url_for('list_'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        g.user = request.form.get('username')
        app.logger.info(request.form.get('username'))
        if user_exists():
            response = redirect(url_for('index'))
            response.set_cookie('username', value=request.form.get('username'))
        else:
            response = redirect(url_for('login'))

        return response

#################
# API functions #
#################

@app.route('/api/v1/data')
def data_get():
    return jsonify(data_to_json())


@app.route('/api/v1/arvo/normaali')
def arvo_normaali():
    voittaja = get_rand(None)
    voittaja.pop('threshold')
    voittaja.pop('value')
    return jsonify(voittaja)


@app.route('/api/v1/arvo/kiirus')
def arvo_kiirus():
    voittaja = get_rand(1)
    voittaja.pop('threshold')
    voittaja.pop('value')
    return jsonify(voittaja)


def user_exists(username):
    yritys = Kayttaja.select().where(Kayttaja.nimi == username)


def save_to_db(form):
    p = Paikka(nimi=form.get('name'), kayttaja=Kayttaja.get(id=1))
    k = Etaisyys(kaukana=(form.get('kaukana') or False), paikka=p)
    o = Ominaisuudet(tasalaatuisuus=form.get('laatu'), parkkipaikka=form.get('parkki'), bonus=form.get('bonus'),
                     hinta=form.get('hinta'), palvelu=form.get('palvelu'), paikka=p)
    j = Jaahy(paikka=p, kesto=0)

    p.save()
    k.save()
    o.save()
    j.save()

def get_from_db():

    return Paikka.select()

def delete_with_id(id):

    p = Paikka.get(id=id)
    p.delete_instance(recursive=True)



def get_rand(kiirus):
    if kiirus == None:
        kiirus = 0
    rows = get_from_db()
    app.logger.info(rows)
    hashi = defaultdict(dict)

    for row in rows:
        if ((int(kiirus) == 1 and row.etaisyys.kaukana) or (row.jaahyn_kesto > 0)):
            pass
        else:
            hashi[row.nimi]['value'] = row.ominaisuudet.painotus
            hashi[row.nimi]['id'] = row.id
            hashi[row.nimi]['nimi'] = row.nimi

    return wrandom(hashi)


def wrandom(dick):
    sum_ = 0
    for name in dick.keys():
        sum_ += dick[name]['value']
        dick[name]['threshold'] = sum_

    randn = random.randint(0, sum_ - 1)


    choice = None
    for key, val in dick.items():
        if randn < val['threshold']:
            choice = key
            break

    return dick[choice]

def decrease_cooldowns():

    q = Jaahy.update(kesto=Jaahy.kesto - 1).where(Jaahy.kesto > 0)
    q.execute()

def set_cooldown(id, cd):

    q = Jaahy.update(kesto=5).where(Jaahy.paikka==id)
    q.execute()

def reset_cd(id):

    q = Jaahy.update(kesto=0).where(Jaahy.paikka==id)
    q.execute()

def data_to_json():
    rows = get_from_db()
    ls = [row.to_json() for row in rows]

    return ls

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))


    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    app.run(host='127.0.0.1', port=5002, debug=True)