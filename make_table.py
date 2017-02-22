#import sqlite3
import psycopg2
import os

url = os.getenv('DATABASE_URL')

con = psycopg2.connect(url)

cur = con.cursor()

cur.execute("CREATE TABLE paikat(id INTEGER PRIMARY KEY ASC, nimi TEXT)")

cur.execute("CREATE TABLE matka(paikka INTEGER, kaukana INTEGER, FOREIGN KEY(paikka) REFERENCES paikat(id))")

cur.execute("""CREATE TABLE ominaisuudet(paikka INTEGER,
                tasalaatuisuus INTEGER,
                parkkipaikka INTEGER,
                palvelu INTEGER,
                hinta INTEGER,
                bonus INTEGER,
                FOREIGN KEY(paikka) REFERENCES paikat(id))""")

#cur.commit()
con.commit()
cur.close()
