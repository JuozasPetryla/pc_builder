"""Serialize migrations and initial administrator creation before serving traffic."""

import os

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import engine
from scripts.bootstrap_admin import bootstrap_admin


def main() -> None:
    with engine.begin() as connection:
        # A replaced Render container can overlap with a new deployment.
        # PostgreSQL releases this transaction lock on success or failure.
        connection.execute(text("SELECT pg_advisory_xact_lock(736284910)"))
        config = Config("alembic.ini")
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        with Session(bind=connection) as db:
            bootstrap_admin(
                db,
                os.environ.get("BOOTSTRAP_ADMIN_USERNAME"),
                os.environ.get("BOOTSTRAP_ADMIN_PASSWORD"),
            )
    print("Database migrations and administrator bootstrap complete.")


if __name__ == "__main__":
    main()
