from typing import List
from confluent_kafka import Consumer, KafkaError
import redis
import utils
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Response, status, Depends
import oauth2
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from database import Base, engine, SessionLocal
from models import *
from confluent_kafka import Producer

producer = Producer({'bootstrap.servers': 'kafka:9092'})

def consume_kafka_messages():
    conf = {
        'bootstrap.servers': 'kafka:9092',
        'group.id': 'mygroup',
        'auto.offset.reset': 'earliest'
    }

    consumer = Consumer(conf)

    consumer.subscribe(['likes'])

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(msg.error())
                    break

            # Ispisivanje Kafka poruke u terminalu
            print('Received message: {}'.format(msg.value().decode('utf-8')))

    except KeyboardInterrupt:
        pass

    finally:
        consumer.close()

app = FastAPI()
Base.metadata.create_all(bind=engine)
r = redis.Redis(host='redis', port=6379, decode_responses=True)

db = SessionLocal()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class Destinacija_schema(BaseModel):
    naziv: str
    opis: str
    klima: str
    jezik: str
    kultura: str


class Smjestaj_schema(BaseModel):
    naziv: str
    vrsta_smjestaja: str
    cijena: int
    broj_soba: int


class Putovanje_schema(BaseModel):
    datum_polaska: str
    datum_povratka: str
    cijena: int
    broj_slobodnih_mjesta: int
    destinacija_id: int


class Rezervacija_schema(BaseModel):
    datum_rezervacije: str
    broj_putnika: int
    turisti_id: int
    putovanje_id: int
    smjestaj_id: int

class Turist_schema(BaseModel):
    email: str
    lozinka: str
    ime: str
    prezime: str


@app.post("/signup")
async def create_user(turist: Turist_schema = Depends(Turist_schema)):


    turist_in_db = db.query(Turist).filter(Turist.email == turist.email).first()
    if turist_in_db:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Email se već koristi.")

    hashed_password = utils.hash_password(turist.lozinka)
    turist.lozinka = hashed_password

    turist_data = turist.model_dump()

    novi_turist = Turist(**turist_data)
    db.add(novi_turist)
    db.commit()
    db.refresh(novi_turist)

    return novi_turist

@app.post("/login")
def login_user(turist_credentials: OAuth2PasswordRequestForm = Depends()):

    turist = db.query(Turist).filter(Turist.email == turist_credentials.username).first()

    if not turist:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    if not utils.verify_password(turist_credentials.password, turist.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials")

    data = {"turist_id": str(turist.id), "email": turist.email, "turistname": turist.username}

    access_token = oauth2.create_access_token(data)


    return {"access_token": access_token, "token_type": "Bearer"}


@app.post("/destinacija")
def kreiraj_destinaciju(destinacija: Destinacija_schema):
    nova_destinacija = Destinacija(**destinacija.dict())
    db.add(nova_destinacija)
    db.commit()
    db.refresh(nova_destinacija)
    r.set("Nova destinacija", nova_destinacija.naziv, ex=300)
    return nova_destinacija


@app.get("/destinacija")
def dohvati_sve_destinacije():
    destinacije = db.query(Destinacija).all()
    return destinacije


@app.get("/destinacija/{id}")
def dohvati_destinaciju_preko_id(id: int):
    destinacija = db.query(Destinacija).filter(Destinacija.id == id).first()
    if destinacija is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destinacija s id " + str(id) + " ne postoji")
    return destinacija


@app.delete("/destinacija/{id}")
def izbrisi_destinaciju(id: int):
    destinacija = db.query(Destinacija).filter(Destinacija.id == id)
    if destinacija.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destinacija s id " + str(id) + " ne postoji")
    destinacija.delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/smjestaj")
def kreiraj_smjestaj(smjestaj: Smjestaj_schema):
    novi_smjestaj = Smjestaj(**smjestaj.dict())
    db.add(novi_smjestaj)
    db.commit()
    db.refresh(novi_smjestaj)
    return novi_smjestaj


@app.get("/smjestaj")
def dohvati_sve_smjestaje():
    smjestaji = db.query(Smjestaj).all()
    return smjestaji


@app.get("/smjestaj/{id}")
def dohvati_smjestaj_preko_id(id: int):
    smjestaj = db.query(Smjestaj).filter(Smjestaj.id == id).first()
    if smjestaj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Smjestaj s id " + str(id) + " ne postoji")
    return smjestaj


@app.delete("/smjestaj/{id}")
def izbrisi_smjestaj(id: int):
    smjestaj = db.query(Smjestaj).filter(Smjestaj.id == id)
    if smjestaj.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Smjestaj s id " + str(id) + " ne postoji")
    smjestaj.delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/putovanje")
def kreiraj_putovanje(putovanje: Putovanje_schema):
    novo_putovanje = Putovanje(**putovanje.dict())
    db.add(novo_putovanje)
    db.commit()
    db.refresh(novo_putovanje)
    return novo_putovanje


@app.get("/putovanje")
def dohvati_sva_putovanja():
    putovanja = db.query(Putovanje).all()
    return putovanja


@app.get("/putovanje/{id}")
def dohvati_putovanje_preko_id(id: int):
    putovanje = db.query(Putovanje).filter(Putovanje.id == id).first()
    if putovanje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Putovanje s id " + str(id) + " ne postoji")
    return putovanje


@app.delete("/putovanje/{id}")
def izbrisi_putovanje(id: int):
    putovanje = db.query(Putovanje).filter(Putovanje.id == id)
    if putovanje.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Putovanje s id " + str(id) + " ne postoji")
    putovanje.delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/rezervacija")
def kreiraj_rezervaciju(rezervacija: Rezervacija_schema):
    nova_rezervacija = Rezervacija(**rezervacija.dict())
    db.add(nova_rezervacija)
    db.commit()
    db.refresh(nova_rezervacija)
    kafka_message = f"Rezervacija sa id {nova_rezervacija.id} je kreirana"
    producer.produce('likes', value=kafka_message.encode('utf-8'))
    return nova_rezervacija


@app.get("/rezervacija")
def dohvati_sve_rezervacije():
    rezervacije = db.query(Rezervacija).all()
    return rezervacije


@app.get("/rezervacija/{id}")
def dohvati_rezervaciju_preko_id(id: int):
    rezervacija = db.query(Rezervacija).filter(Rezervacija.id == id).first()
    if rezervacija is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezervacija s id " + str(id) + " ne postoji")
    return rezervacija


@app.delete("/rezervacija/{id}")
def izbrisi_rezervaciju(id: int):
    rezervacija = db.query(Rezervacija).filter(Rezervacija.id == id)
    if rezervacija.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezervacija s id " + str(id) + " ne postoji")
    rezervacija.delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    import uvicorn
    from threading import Thread
    kafka_thread = Thread(target=consume_kafka_messages)
    kafka_thread.daemon = True
    kafka_thread.start()
    uvicorn.run(app, host="0.0.0.0", port=5000)