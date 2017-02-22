# -*- coding: utf-8 -*-
from flask import Flask
from flask import render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
import os
import sqlite3
from flask import g


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

# connection = sqlite3.connect("ruoka.db")

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
        p_name = request.form.get('submit')
        return render_template("rand.html", jepa=p_name)
        
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
    #return render_template("list.html", rows=[[1, 'veeruska']])

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
                INNER JOIN ominaisuudet ON paikat.id=ominaisuudet.paikka """

    cur.execute(qry)
    rows = cur.fetchall()

    app.logger.info(dev)
    return rows

def delete_with_id(id):
    con = get_db()
    cur = con.cursor()

    if dev:
        cur.execute("DELETE FROM paikat WHERE id=?", (id,))
        cur.execute("DELETE FROM matka WHERE paikka=?", (id,))
        cur.execute("DELETE FROM ominaisuudet WHERE paikka=?", (id,))
    else:
        cur.execute("DELETE FROM matka WHERE paikka=%s", (id,))
        cur.execute("DELETE FROM ominaisuudet WHERE paikka=%s", (id,))
        cur.execute("DELETE FROM paikat WHERE id=%s", (id,))


    con.commit()

        
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))


    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    app.run(host='127.0.0.1', port=5002, debug=True)