import sqlite3

con = sqlite3.connect("ruoka.db")

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

cur.commit()
cur.close()
