# coding=utf-8

import peewee
import os
import datetime



dev = bool(os.getenv('DEV', False))

#if dev:
if 'DATABASE_URL' not in os.environ:
    dev = True
    database = peewee.SqliteDatabase("ruoka_orm.db")
else:
    from peewee import Proxy
    import urllib
    from urllib.parse import urlparse
    import psycopg2
    urllib.parse.uses_netloc.append('postgres')
    url = urllib.parse.urlparse(os.getenv('DATABASE_URL'))

    database = peewee.PostgresqlDatabase(database=url.path[1:], user=url.username, password=url.password,
                                         host=url.hostname, port=url.port)


class BaseModel(peewee.Model):
    """
    ORM Base Model
    """
    class Meta:
        database = database

class Kayttaja(BaseModel):
    """ORM Model for Kayttaja"""
    nimi = peewee.CharField(unique=True)

    def to_json(self):
        return {'nimi': self.nimi}
    
    # @property
    # def paikat(self):
        # return Paikka.select().where(Paikka.kayttaja == self)


class Paikka(BaseModel):
    """
    ORM Model for Paikka
    """
    nimi = peewee.CharField()
    kayttaja = peewee.ForeignKeyField(Kayttaja, related_name="paikat")

    @property
    def ominaisuudet(self):
        return self.ominaisuudet_.get()

    @property
    def etaisyys(self):
        return self.etaisyys_.get()

    @property
    def etaisyys_suomeksi(self):
        if self.etaisyys.kaukana == True:
            return 'Kaukana'
        else:
            return 'Lähellä'

    @property
    def jaahyn_kesto(self):
        return self.jaahy_.get().kesto

    @property
    def jaahylla(self):
        if self.jaahy_.select().count() == 0:
            return True
        else:
            return False

    def to_json(self):
        # kayt = self.kayttaja.to_json()
        return {'nimi': self.nimi,
                'painotus': self.ominaisuudet.painotus,
                'kayttaja': self.kayttaja.to_json(),
                'ominaisuudet': self.ominaisuudet.to_json(),
                'id': self.id
                }

class Historia(BaseModel):
    """
    ORM Model for Historia
    """
    otsikko = peewee.TextField()
    teksti = peewee.TextField(null=True)
    aika = peewee.DateTimeField(default=datetime.datetime.now())
    kayttaja = peewee.ForeignKeyField(Kayttaja, related_name="historia")



class Etaisyys(BaseModel):
    """
    ORM Model for Etaisyys
    """
    kaukana = peewee.BooleanField()
    paikka = peewee.ForeignKeyField(Paikka, related_name="etaisyys_")

    def to_json(self):
        return {'kaukana': self.kaukana}


class Ominaisuudet(BaseModel):
    """
    ORM model for ominaisuudet
    """
    tasalaatuisuus = peewee.IntegerField()
    parkkipaikka = peewee.IntegerField()
    palvelu = peewee.IntegerField()
    hinta = peewee.IntegerField()
    bonus = peewee.IntegerField()
    paikka = peewee.ForeignKeyField(Paikka, related_name="ominaisuudet_")

    @property
    def painotus(self):
        return self.tasalaatuisuus + self.parkkipaikka + self.palvelu + self.hinta + self.bonus

    def to_json(self):
        return {
            'tasalaatuisuus': self.tasalaatuisuus,
            'parkkipaikka': self.parkkipaikka,
            'palvelu': self.palvelu,
            'hinta': self.hinta,
            'bonus': self.bonus
        }

class Jaahy(BaseModel):
    """ORM model for Jaahy"""
    kesto = peewee.IntegerField()
    paikka = peewee.ForeignKeyField(Paikka, related_name="jaahy_")

    @property
    def empty(self):
        if self.select().count() == 0:
            return True
        else:
            return False

    def to_json(self):
        return {
            'kesto': self.kesto
        }

class Salainen(BaseModel):
    """ORM model for Salainen"""
    hash = peewee.TextField()
    suola = peewee.TextField()
    kayttaja = peewee.ForeignKeyField(Kayttaja, related_name="salainen")
    

if __name__ == "__main__":

    # try:
    #     Kayttaja.create_table()
    # except peewee.OperationalError:
    #     print("Kayttaja already exists")
    #
    # try:
    #     Paikka.create_table()
    # except peewee.OperationalError:
    #     print("Paikka already exists")
    # except Exception as e:
    #     print(e)
    #
    #
    # try:
    #     Etaisyys.create_table()
    # except peewee.OperationalError:
    #     print("Etaisyys already exists")
    #
    # try:
    #     Ominaisuudet.create_table()
    # except peewee.OperationalError:
    #     print("Ominaisuudet already exists")
    #
    # try:
    #     Jaahy.create_table()
    # except peewee.OperationalError:
    #     print("Jaahy already exists")
    #
    # try:
    #     Salainen.create_table()
    # except peewee.OperationalError:
    #     print("Salainen already exists")

    try:
        Historia.create_table()
    except peewee.OperationalError:
        print("Salainen already exists")

    database.commit()
