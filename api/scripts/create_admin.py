"""Create the initial administrator without a public privilege-escalation endpoint."""

from getpass import getpass

from sqlalchemy import select

from app.core.security import password_hash
from app.db.session import SessionLocal
from app.models.auth import Role, User
from app.schemas.auth import Credentials


def main() -> None:
    credentials = Credentials(username=input("Username: "), password=getpass("Password: "))
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == credentials.username)):
            raise SystemExit("Username already exists; choose a new administrator username.")
        db.add(
            User(
                username=credentials.username,
                password_hash=password_hash.hash(credentials.password),
                role=Role.ADMIN,
            )
        )
        db.commit()
    print("Administrator created.")


if __name__ == "__main__":
    main()
