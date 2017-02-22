import sqlite3

con = sqlite3.connect("ruoka.db")

cur = con.cursor()

cursor.execute("CREATE TABLE paikat(id INTEGER PRIMARY KEY ASC, nimi TEXT)")

cursor.execute("CREATE TABLE matka(id INTEGER FOREIGN KEY , kaukana INTEGER)")

cursor.execute("""CREATE TABLE ominaisuudet(id INTEGER FOREIGN KEY,
                tasalaatuisuus INTEGER,
                parkkipaikka INTEGER,
                palvelu INTEGER,
                hinta INTEGER,
                bonus INTEGER)""")

cursor.commit()
cursor.close()
