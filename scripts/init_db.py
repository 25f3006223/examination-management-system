"""Create the SQLite schema and the single administrator account.

Set ADMIN_EMAIL and ADMIN_PASSWORD before running this script. The password is
never stored in plain text; only its Werkzeug hash is saved to the database.
"""

import os
import sys

from app import create_app, db
from app.models import User


def main():
    email = os.environ.get("ADMIN_EMAIL", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")
    full_name = os.environ.get("ADMIN_NAME", "System Administrator").strip()
    if not email or not password:
        sys.exit(
            "Set ADMIN_EMAIL and ADMIN_PASSWORD before initializing the database."
        )
    if len(password) < 12:
        sys.exit("ADMIN_PASSWORD must contain at least 12 characters.")

    app = create_app()
    with app.app_context():
        admin, created = User.create_admin(email, password, full_name)
        db.session.commit()
        action = "Created" if created else "Found existing"
        print(f"{action} admin account: {admin.email}")
        print(f"Database ready at: {app.config['SQLALCHEMY_DATABASE_URI']}")


if __name__ == "__main__":
    main()
