#import sqlite3
import psycopg2
import os

url = os.getenv('DATABASE_URL')

con = psycopg2.connect(url)

cur = con.cursor()

cur.execute("CREATE TABLE jaahyt(paikka INTEGER REFERENCES paikat(id), kesto INTEGER)")

con.commit()
con.close()
