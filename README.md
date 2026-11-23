# Examination Management Portal

The Examination Management Portal helps administrators manage courses and
examinations, examiners manage assessment slots and evaluations, and students
book examinations and view results. The project uses Flask, SQLite, Vue, and
Bootstrap, and is being built milestone by milestone. This repository currently
contains the Milestone 1 database schema and administrator initializer; later
milestones will add authentication, role workflows, and the Vue interface.

## Requirements

- Python 3.10 or newer
- pip

## Initialize the database

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="use-a-unique-password-of-at-least-12-characters"
python -m scripts.init_db
```

The database is created at `instance/examination.db`. The initializer is safe to
run more than once: it creates the administrator only if one does not exist.
The password is stored as a hash. Keep `.env` files, database files, and real
credentials out of version control.

## Schema in this milestone

- `User` holds the shared Admin, Examiner, and Student identity fields.
- `Course` has many `Examination` records.
- Each `Examination` has rubric criteria and examiner-created time slots.
- `ExaminerProfile` extends an examiner's `User` record and owns their slots.
- `Booking` joins a student, examination, and slot; a database constraint limits
  each student to one booking per examination.
- `Evaluation` stores the result for a booking, including marks and remarks.

The tables are created from SQLAlchemy models when the Flask app starts; no
manual database setup is required.

## Start the Flask app

```bash
flask --app 'app:create_app' run --debug
```

The `/health` endpoint returns a small status response. This milestone focuses
on schema setup; authentication, API resources, and the Vue user interface are
planned for later milestones.
