"""Migration : ajoute le modèle IA utilisé à l'historique
(history.model_id et history.model_name, nullables).

Relançable sans risque : une colonne déjà présente est ignorée.
À lancer AVANT de redémarrer le backend avec le nouveau modèle :

    python migrate_history_model.py

Pour ajouter d'autres colonnes, ajoute une ligne dans TARGETS.
"""

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from database.connection import SessionLocal, check_db_connection

# (table, colonne, type SQL)
TARGETS = [
    ("history", "model_id", "VARCHAR(100)"),
    ("history", "model_name", "VARCHAR(200)"),
]


def main():
    print("========== MIGRATION HISTORY MODEL ==========")

    check_db_connection()

    db = SessionLocal()
    try:
        insp = inspect(db.get_bind())
        tables = insp.get_table_names()

        for table, column, sql_type in TARGETS:
            if table not in tables:
                print(
                    f"[SKIP] Table {table} absente : elle sera créée avec le bon schéma."
                )
                continue

            existing = {c["name"] for c in insp.get_columns(table)}

            if column in existing:
                print(f"[OK] {table}.{column} existe déjà.")
                continue

            # identifiants en dur (TARGETS) : pas d'entrée utilisateur
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))
            print(f"[+] {table}.{column} ajoutée ({sql_type}, nullable).")

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