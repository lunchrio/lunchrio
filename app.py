# -*- coding: utf-8 -*-
from flask import Flask
from flask import Response, make_response
from flask import render_template, request, redirect, url_for, flash
from flask import g, session
from flask import jsonify
from flask_bootstrap import Bootstrap
from werkzeug.contrib.atom import AtomFeed


import hashlib
import time
import os
import sqlite3
from collections import defaultdict
import random
from functools import wraps
import datetime

import logging
from logging.handlers import RotatingFileHandler

from models import Kayttaja, Paikka, Ominaisuudet, Etaisyys, Jaahy, Salainen, Historia

dev = bool(os.getenv('DEV', False))

#if dev:
if 'DATABASE_URL' not in os.environ:
    dev = True
    DATABASE = 'ruoka.db'
else:
    import psycopg2
    import psycopg2.extras
    DATABASE = os.getenv('DATABASE_URL')

app = Flask(__name__)
Bootstrap(app)
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?Rs'  

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
    """This decorator passes Content-Type: application/json"""
    @wraps(f)
    @add_response_headers({'Content-type': 'application/json'})
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        g.user = session['username']
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
        lisaa_historiaan(g.user, winner['nimi'])

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
        return render_template('login.html', no_session=True)
    else:
        g.user = request.form.get('username')
        if user_exists(g.user, request.form.get('password')):
            response = redirect(url_for('index'))
            session['username'] = request.form.get('username')
        else:
            #flash("Error, no such user exists") 
            response = redirect(url_for('login', error="Käyttäjänimi tai PIN ei täsmää."))
 
        return response  

@app.route('/logout', methods=['GET'])
def logout():
    response = redirect(url_for('login'))
    session.pop('username', None)
    return response
 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html', no_session=True)
    else:
        register_user(request.form)
        return redirect(url_for('login', error="Kokeile kirjautua sisään uusilla tunnuksillasi."))
        
#################
# API functions #
#################

@app.route('/api/v1/data')
def data_get():
    return jsonify(data_to_json())


@app.route('/api/v1/arvo/<nimi>/normaali')
def arvo_normaali(nimi):
    g.user = nimi
    voittaja = get_rand(None)
    voittaja.pop('threshold')
    voittaja.pop('value')
    decrease_cooldowns()
    set_cooldown(voittaja['id'], 5)
    lisaa_historiaan(g.user, voittaja['nimi'])
    return jsonify(voittaja)

@app.route('/api/v1/arvo/<nimi>/kiirus')
def arvo_kiirus(nimi):
    g.user = nimi
    voittaja = get_rand(1)
    voittaja.pop('threshold')
    voittaja.pop('value')   
    decrease_cooldowns()
    set_cooldown(voittaja['id'], 5)
    lisaa_historiaan(g.user, voittaja['nimi'])
    return jsonify(voittaja)

#################
#      RSS      #
#################

@app.route('/feed/<nimi>')
def anna_feedi(nimi):
    historiat = Historia.select().where(Historia.kayttaja == Kayttaja.get(nimi=nimi))
    feed = AtomFeed('Lnchrio', feed_url=request.url, url=request.url_root)

    for h in historiat:
        feed.add(h.otsikko, published=h.aika, id=h.id, url=request.url_root + 'historia/' + str(h.id),
                 author=nimi, updated=h.aika)

    return feed.get_response()

@app.route("/historia/<id>")
def historia_yksi(id):
    h = Historia.get(id=id)
    return h.otsikko




def lisaa_historiaan(kayttaja, paikka):
    k = Kayttaja.get(nimi=kayttaja)
    nyt = datetime.datetime.now()
    otsikko = "{0} - {1}".format(nyt.strftime('%d.%m.%Y'), paikka)
    h = Historia(kayttaja=k, aika=nyt, otsikko=otsikko)
    h.save()


def user_exists(username, passu):
    try:
        k = Kayttaja.get(nimi=username)
        s = k.salainen.get()
        suola = s.suola
        pansuola = suola + passu
        m = hashlib.sha256()
        m.update(bytes(pansuola, encoding="utf-8")) 
        hassu = m.hexdigest()
        if hassu == s.hash:
            return True
        else:
            return False
    except:
        return False


def register_user(form):
    u = Kayttaja(nimi=form.get('username'))
    passu = form.get('password')
    suola = str(time.time())
    pansuola = suola + passu
    app.logger.info(pansuola)
    m = hashlib.sha256()
    m.update(bytes(pansuola, encoding="utf-8")) 
    hassu = m.hexdigest()
    s = Salainen(hash=hassu, suola=suola, kayttaja=u)
    u.save()
    s.save()
        
def save_to_db(form):
    p = Paikka(nimi=form.get('name'), kayttaja=Kayttaja.get(nimi=g.user))
    k = Etaisyys(kaukana=(form.get('kaukana') or False), paikka=p)
    o = Ominaisuudet(tasalaatuisuus=form.get('laatu'), parkkipaikka=form.get('parkki'), bonus=form.get('bonus'),
                     hinta=form.get('hinta'), palvelu=form.get('palvelu'), paikka=p)
    j = Jaahy(paikka=p, kesto=0)

    p.save()
    k.save()
    o.save()
    j.save()

def get_from_db():
    return Kayttaja.get(nimi=g.user).paikat
    
# def get_paikat_for_user(nimi):
    # return Kayttaha.get(nimi=nimi).paikat

def delete_with_id(id):
    #p = Paikka.get(id=id)
    p = Kayttaja.get(nimi=g.user).paikat.where(Paikka.id==id).get()
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

    paikat = Kayttaja.get(nimi=g.user).paikat
    for paikka in paikat:
        j = paikka.jaahy_.get()
        if j.kesto > 0:
            j.kesto -= 1
            j.save()
        # q.execute()

def set_cooldown(id, cd):
    if Jaahy.get(id=id).paikka.kayttaja.nimi == g.user:
        q = Jaahy.update(kesto=5).where(Jaahy.paikka==id)
        q.execute()

def reset_cd(id):
    if Jaahy.get(id=id).paikka.kayttaja.nimi == g.user:
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


    app.run(host='0.0.0.0', port=5002, debug=True)
