from sqlalchemy import inspect, text
from app.db import Base, engine
from app import models  # noqa: F401


# create_all creates new tables; this additive migration also upgrades existing
# deployments without dropping historical round_results data.
_ADDITIVE_COLUMNS = {
    "time_of_day": "VARCHAR(5)",
    "players": "FLOAT",
    "bets": "FLOAT",
    "prize": "FLOAT",
    "source": "VARCHAR(300)",
    "source_file": "VARCHAR(180)",
    "import_batch_hash": "VARCHAR(64)",
    "created_at": "TIMESTAMP",
}


def initialize():
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if "round_results" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("round_results")}
    with engine.begin() as connection:
        for name, sql_type in _ADDITIVE_COLUMNS.items():
            if name not in existing:
                connection.execute(text(f"ALTER TABLE round_results ADD COLUMN {name} {sql_type}"))


if __name__ == "__main__":
    initialize()
    print("Database tables initialized and additive migrations applied.")
