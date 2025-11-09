from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from database.base import Base
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection():
    print("Try to connect to database...")
    try:
        with SessionLocal() as session:
            result = session.execute(text("SELECT 1"))
            if result.fetchone():
                print("Base de données connectée et valide.")
            else:
                print("Erreur : La base de données ne renvoie aucun résultat.")
    except Exception as e:
        print(f"Erreur de connexion à la base de données : {e}")

    print("Création des tables (si manquantes)...")
    Base.metadata.create_all(bind=engine)
    print("Tables OK.")