import sqlite3

con = sqlite3.connect("ruoka.db")

cur = con.cursor()

cur.execute("CREATE TABLE paikat(id INTEGER PRIMARY KEY ASC, nimi TEXT)")

cur.execute("CREATE TABLE matka(id INTEGER FOREIGN KEY , kaukana INTEGER)")

cur.execute("""CREATE TABLE ominaisuudet(id INTEGER FOREIGN KEY,
                tasalaatuisuus INTEGER,
                parkkipaikka INTEGER,
                palvelu INTEGER,
                hinta INTEGER,
                bonus INTEGER)""")

cur.commit()
cur.close()
