"""Migration : user_params (theme_id / layout_id) -> palette de 3 couleurs.

Relançable sans risque (IF EXISTS / IF NOT EXISTS).
À lancer AVANT le seed et AVANT de démarrer le nouveau code :

    python migrate_palette.py
"""

import traceback

from sqlalchemy import inspect, text

from database.connection import SessionLocal, check_db_connection

# Valeurs données aux lignes déjà existantes
OLD_ROWS_PALETTE = ["#00D4FF", "#7B8CFF", "#9AA5B8"]

STATEMENTS = [
    f"""
    ALTER TABLE user_params
        ADD COLUMN IF NOT EXISTS color_1 VARCHAR(7) NOT NULL DEFAULT '{OLD_ROWS_PALETTE[0]}',
        ADD COLUMN IF NOT EXISTS color_2 VARCHAR(7) NOT NULL DEFAULT '{OLD_ROWS_PALETTE[1]}',
        ADD COLUMN IF NOT EXISTS color_3 VARCHAR(7) NOT NULL DEFAULT '{OLD_ROWS_PALETTE[2]}',
        ADD COLUMN IF NOT EXISTS last_color_id INTEGER NOT NULL DEFAULT 1
    """,
    "ALTER TABLE user_params DROP CONSTRAINT IF EXISTS ck_user_params_last_color_id",
    """
    ALTER TABLE user_params
        ADD CONSTRAINT ck_user_params_last_color_id
        CHECK (last_color_id >= 1 AND last_color_id <= 3)
    """,
    """
    ALTER TABLE user_params
        DROP COLUMN IF EXISTS theme_id,
        DROP COLUMN IF EXISTS layout_id
    """,
    # les défauts sont gérés côté Python (models/user_params.py)
    """
    ALTER TABLE user_params
        ALTER COLUMN color_1 DROP DEFAULT,
        ALTER COLUMN color_2 DROP DEFAULT,
        ALTER COLUMN color_3 DROP DEFAULT,
        ALTER COLUMN last_color_id DROP DEFAULT
    """,
]


def main():
    print("========== MIGRATION PALETTE ==========")

    check_db_connection()

    db = SessionLocal()
    try:
        if "user_params" not in inspect(db.get_bind()).get_table_names():
            print("[SKIP] Table user_params absente : elle sera créée avec le bon schéma.")
            return

        for stmt in STATEMENTS:
            db.execute(text(stmt))

        db.commit()
        print("[OK] user_params migrée (color_1..3, last_color_id).")
        print("========== MIGRATION TERMINEE ==========")
    except Exception as e:
        db.rollback()
        print("******** ERREUR DANS LA MIGRATION ********")
        print(e)
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()