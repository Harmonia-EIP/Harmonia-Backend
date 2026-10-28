"""Migration : allonge les noms de l'historique (history.name : 120 -> 1000).

Relançable sans risque : une colonne déjà assez large est ignorée.
À lancer AVANT de redémarrer le backend avec le nouveau modèle :

    python migrate_history_name.py

Pour allonger d'autres colonnes, ajoute une ligne dans TARGETS.
"""

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from database.connection import SessionLocal, check_db_connection

# (table, colonne, nouvelle longueur max)
TARGETS = [
    ("history", "name", 1000),
]


def main():
    print("========== MIGRATION HISTORY NAME ==========")

    check_db_connection()

    db = SessionLocal()
    try:
        insp = inspect(db.get_bind())
        tables = insp.get_table_names()

        for table, column, new_len in TARGETS:
            if table not in tables:
                print(
                    f"[SKIP] Table {table} absente : elle sera créée avec le bon schéma."
                )
                continue

            cols = {c["name"]: c for c in insp.get_columns(table)}

            if column not in cols:
                print(f"[SKIP] Colonne {table}.{column} absente.")
                continue

            current_len = getattr(cols[column]["type"], "length", None)

            if current_len is None or current_len >= new_len:
                print(
                    f"[OK] {table}.{column} déjà assez large "
                    f"({current_len or 'sans limite'})."
                )
                continue

            # identifiants en dur (TARGETS) : pas d'entrée utilisateur
            db.execute(
                text(f"ALTER TABLE {table} ALTER COLUMN {column} TYPE VARCHAR({new_len})")
            )
            print(f"[+] {table}.{column} : VARCHAR({current_len}) -> VARCHAR({new_len})")

        db.commit()
        print("========== MIGRATION TERMINEE ==========")
    except SQLAlchemyError as e:
        db.rollback()
        print("******** ERREUR DANS LA MIGRATION ********")
        print(e)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()