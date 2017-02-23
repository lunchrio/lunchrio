# coding=utf-8

import peewee

database = peewee.SqliteDatabase("ruoka_orm.db")

class BaseModel(peewee.Model):
    """
    ORM Base Model
    """
    class Meta:
        database = database

class Kayttaja(BaseModel):
    """ORM Model for Kayttaja"""
    nimi = peewee.CharField(unique=True)


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
    def jaahy(self):
        return self.jaahy_.get()

class Etaisyys(BaseModel):
    """
    ORM Model for Etaisyys
    """
    kaukana = peewee.BooleanField()
    paikka = peewee.ForeignKeyField(Paikka, related_name="etaisyys_")

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


class Jaahy(BaseModel):
    """ORM model for Jaahy"""
    kesto = peewee.IntegerField()
    paikka = peewee.ForeignKeyField(Paikka, related_name="jaahy_")


if __name__ == "__main__":
    try:
        Paikka.create_table()
    except peewee.OperationalError:
        print("Paikka already exists")

    try:
        Kayttaja.create_table()
    except peewee.OperationalError:
        print("Kayttaja already exists")

    try:
        Etaisyys.create_table()
    except peewee.OperationalError:
        print("Etaisyys already exists")

    try:
        Ominaisuudet.create_table()
    except peewee.OperationalError:
        print("Ominaisuudet already exists")

    try:
        Jaahy.create_table()
    except peewee.OperationalError:
        print("Jaahy already exists")

