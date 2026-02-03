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
        with engine.begin() as conn:
            # test connexion
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("Base de données connectée et valide.")
            else:
                print("Erreur : La base de données ne renvoie aucun résultat.")

            conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
            conn.execute(text("SET search_path TO public"))

        print("Création des tables (si manquantes)...")
        Base.metadata.create_all(bind=engine)
        print("Tables OK.")

    except Exception as e:
        print(f"Erreur de connexion / init DB : {e}")
        raise
