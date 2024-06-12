from sqlalchemy import Column, Integer, String, Float, ForeignKey
from database import Base


class Turist(Base):
    __tablename__ = 'turisti'
    id = Column(Integer, primary_key=True)
    ime = Column(String(255))
    prezime = Column(String(255))
    lozinka = Column(String(255))
    email = Column(String(255))


class Destinacija(Base):
    __tablename__ = 'destinacije'
    id = Column(Integer, primary_key=True)
    naziv = Column(String(255))
    opis = Column(String(255))
    klima = Column(String(255))
    jezik = Column(String(255))
    kultura = Column(String(255))


class Smjestaj(Base):
    __tablename__ = 'smjestaji'
    id = Column(Integer, primary_key=True)
    naziv = Column(String(255))
    vrsta_smjestaja = Column(String(255))
    cijena = Column(Integer)
    broj_soba = Column(Integer)


class Putovanje(Base):
    __tablename__ = 'putovanja'
    id = Column(Integer, primary_key=True)
    datum_polaska = Column(String(255))
    datum_povratka = Column(String(255))
    cijena = Column(Integer)
    broj_slobodnih_mjesta = Column(Integer)
    destinacija_id = Column(Integer, ForeignKey("destinacije.id", ondelete="CASCADE"), nullable=False)


class Rezervacija(Base):
    __tablename__ = "rezervacije"
    id = Column(Integer, primary_key=True)
    datum_rezervacije = Column(String(255))
    broj_putnika = Column(Integer)
    turisti_id = Column(Integer, ForeignKey("turisti.id", ondelete="CASCADE"), nullable=False)
    putovanje_id = Column(Integer, ForeignKey("putovanja.id", ondelete="CASCADE"), nullable=False)
    smjestaj_id = Column(Integer, ForeignKey("smjestaji.id", ondelete="CASCADE"), nullable=False)
