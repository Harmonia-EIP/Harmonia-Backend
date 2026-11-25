"""Met le schéma de la base à jour (Alembic). Lancé par entrypoint.sh.

    python migrate.py

Une base créée avant Alembic (tables présentes, pas de table
alembic_version) est d'abord marquée comme étant au schéma initial
(révision 0001), puis les migrations suivantes sont appliquées.

Nouvelle migration : alembic revision -m "description" (puis l'éditer).
"""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from database.connection import engine

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("migrate")

BASELINE_REVISION = "0001"


def main() -> None:
    cfg = Config(str(Path(__file__).with_name("alembic.ini")))

    tables = set(inspect(engine).get_table_names())
    if "users" in tables and "alembic_version" not in tables:
        logger.info("Base existante sans Alembic : stamp %s", BASELINE_REVISION)
        command.stamp(cfg, BASELINE_REVISION)

    command.upgrade(cfg, "head")
    logger.info("Schéma à jour")


if __name__ == "__main__":
    main()
