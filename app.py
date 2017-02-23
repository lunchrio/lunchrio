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
import json
from functools import wraps

import logging
from logging.handlers import RotatingFileHandler

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
def index():
    if request.method == 'GET':
        return render_template("index.html")
    else:
        winner = get_rand(request.form.get('kiirus'))
        decrease_cooldowns()
        set_cooldown(winner['id'], 5)

        return render_template("rand.html", voittaja=winner)
        
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'GET':
        return render_template("add.html", method='GET')
    else:
        save_to_db(request.form)
        return render_template("add.html", method='POST', values=request.form)

@app.route('/delete', methods=['GET'])
def delete():
    delete_with_id(request.args.get('id'))
    return redirect(url_for('list_'))

@app.route('/list')
def list_():
    return render_template("list.html", rows=get_from_db())

@app.route('/update')
def update():
    decrease_cooldowns()
    return redirect(url_for('list_'))

@app.route('/setcd/<int:id>')
def set_cd(id):
    set_cooldown(id, 5)
    return redirect(url_for('list_'))

@app.route('/reset')
def reset():
    reset_cd(request.args.get('id'))
    return redirect(url_for('list_'))

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

def save_to_db(form):
    con = get_db()
    cur = con.cursor()
    name = form.get('name')
    laatu = form.get('laatu')
    palvelu = form.get('palvelu')
    parkki = form.get('parkki')
    bonus = form.get('bonus')
    hinta = form.get('hinta')
    kaukana = form.get('kaukana') or False

    if dev:
        cur.execute("INSERT INTO paikat(nimi) VALUES(?)", (name,))
        id_ = cur.lastrowid
        cur.execute("INSERT INTO matka VALUES(?,?)", (id_, int(kaukana)))
        cur.execute("INSERT INTO ominaisuudet VALUES(?,?,?,?,?,?)", (id_, laatu, parkki, palvelu, hinta, bonus))
    else:
        cur.execute("INSERT INTO paikat(nimi) VALUES(%s) RETURNING id", (name,))
        id_ = cur.fetchone()[0]
        cur.execute("INSERT INTO matka VALUES(%s,%s)", (id_, int(kaukana)))
        cur.execute("INSERT INTO ominaisuudet VALUES(%s,%s,%s,%s,%s,%s)", (id_, laatu, parkki, palvelu, hinta, bonus))
    con.commit()
    con.close()

def get_from_db():
    if dev:
        cur = get_db().cursor()
    else:
        cur = cur = get_db().cursor(cursor_factory=psycopg2.extras.DictCursor)

    qry = """select * FROM paikat
                INNER JOIN matka on paikat.id=matka.paikka
                INNER JOIN ominaisuudet ON paikat.id=ominaisuudet.paikka
                LEFT OUTER JOIN jaahyt ON paikat.id=jaahyt.paikka """

    cur.execute(qry)
    rows = cur.fetchall()

    return rows

def delete_with_id(id):
    con = get_db()
    cur = con.cursor()

    if dev:
        cur.execute("DELETE FROM paikat WHERE id=?", (id,))
        cur.execute("DELETE FROM matka WHERE paikka=?", (id,))
        cur.execute("DELETE FROM jaahyt WHERE paikka=?", (id,))
        cur.execute("DELETE FROM ominaisuudet WHERE paikka=?", (id,))
    else:
        cur.execute("DELETE FROM matka WHERE paikka=%s", (id,))
        cur.execute("DELETE FROM jaahyt WHERE paikka=%s", (id,))
        cur.execute("DELETE FROM ominaisuudet WHERE paikka=%s", (id,))
        cur.execute("DELETE FROM paikat WHERE id=%s", (id,))


    con.commit()

def get_rand(kiirus):
    if kiirus == None:
        kiirus = 0
    rows = get_from_db()
    hashi = defaultdict(dict)

    for row in rows:
        if ((kiirus == 1) and (row['kaukana'] == 1)) or (row['kesto'] is not None):
            continue
        hashi[row['nimi']]['value'] = row['tasalaatuisuus'] + row['parkkipaikka'] + row['palvelu'] + \
        row['hinta'] + row['bonus']
        hashi[row['nimi']]['id'] = row['id']
        hashi[row['nimi']]['nimi'] = row['nimi']

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
    con = get_db()
    cur = con.cursor()

    cur.execute("UPDATE jaahyt SET kesto = kesto - 1")
    cur.execute("DELETE FROM jaahyt WHERE kesto < 1")

    con.commit()

def set_cooldown(id, cd):
    con = get_db()
    cur = con.cursor()

    if dev:
        cur.execute("""INSERT INTO jaahyt(paikka, kesto)
        SELECT * FROM (SELECT ?, ?) AS tmp
        WHERE NOT EXISTS (
            SELECT paikka FROM jaahyt WHERE paikka = ?) LIMIT 1""", (id, cd, id))
    else:
        cur.execute("""INSERT INTO jaahyt(paikka, kesto)
        SELECT * FROM (SELECT %s, %s) AS tmp
        WHERE NOT EXISTS (
            SELECT paikka FROM jaahyt WHERE paikka = %s) LIMIT 1""", (id, cd, id))

    con.commit()

def reset_cd(id):
    con = get_db()
    cur = con.cursor()

    if dev:
        cur.execute("""DELETE FROM jaahyt
        WHERE paikka=?""", (id,))
    else:
        cur.execute("""DELETE FROM jaahyt
        WHERE paikka=%s""", (id,))

    con.commit()

def data_to_json():
    rows = get_from_db()
    the_d = defaultdict(dict)

    for row in rows:
        the_d[row['nimi']]['tasalaatuisuus'] = row['tasalaatuisuus']
        the_d[row['nimi']]['parkkipaikka'] = row['parkkipaikka']
        the_d[row['nimi']]['palvelu'] = row['palvelu']
        the_d[row['nimi']]['hinta'] = row['hinta']
        the_d[row['nimi']]['bonus'] = row['bonus']
        the_d[row['nimi']]['painotus'] = sum(the_d[row['nimi']].values())

    return the_d

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))


    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    app.run(host='127.0.0.1', port=5002, debug=True)