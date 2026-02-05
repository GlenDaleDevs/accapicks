"""
Database migration script - now uses Alembic.

Run from the backend directory:
    python migrate.py          # upgrade to latest
    python migrate.py downgrade   # downgrade one step

Or use Alembic directly from the project root:
    python -m alembic upgrade head
    python -m alembic revision --autogenerate -m "description"
    python -m alembic downgrade -1
"""
import sys
import subprocess
import os

def run_migrations():
    # Change to project root where alembic.ini is located
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)

    # Default to upgrade head if no args provided
    args = sys.argv[1:] if len(sys.argv) > 1 else ["upgrade", "head"]

    # Run alembic with the provided arguments
    subprocess.run(["python", "-m", "alembic"] + args, check=True)

if __name__ == "__main__":
    run_migrations()
