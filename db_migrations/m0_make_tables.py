#import sqlite3
import psycopg2
import os

url = os.getenv('DATABASE_URL')

con = psycopg2.connect(url)

cur = con.cursor()

cur.execute("CREATE TABLE paikat(id SERIAL PRIMARY KEY, nimi TEXT)")

cur.execute("CREATE TABLE matka(paikka INTEGER REFERENCES paikat(id), kaukana INTEGER)")

cur.execute("""CREATE TABLE ominaisuudet(paikka INTEGER REFERENCES paikat(id),
                tasalaatuisuus INTEGER,
                parkkipaikka INTEGER,
                palvelu INTEGER,
                hinta INTEGER,
                bonus INTEGER)""")

#cur.commit()
con.commit()
cur.close()
