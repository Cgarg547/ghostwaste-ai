from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

def test_initial_migration_upgrades_fresh_database(tmp_path):
    db=tmp_path / "fresh.db"; root=Path(__file__).resolve().parents[1]
    config=Config(str(root / "alembic.ini")); config.set_main_option("script_location",str(root / "migrations")); config.set_main_option("sqlalchemy.url",f"sqlite:///{db}")
    command.upgrade(config,"head")
    tables=set(inspect(create_engine(f"sqlite:///{db}")).get_table_names())
    assert {"ingredients","inventory_batches","recipes","suppliers","waste_events"}.issubset(tables)
