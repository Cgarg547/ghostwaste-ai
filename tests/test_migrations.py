from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

def test_initial_migration_upgrades_fresh_database(tmp_path):
    db=tmp_path / "fresh.db"; root=Path(__file__).resolve().parents[1]
    config=Config(str(root / "alembic.ini")); config.set_main_option("script_location",str(root / "migrations")); config.set_main_option("sqlalchemy.url",f"sqlite:///{db}")
    command.upgrade(config,"head")
    tables=set(inspect(create_engine(f"sqlite:///{db}")).get_table_names())
    assert {"ingredients","inventory_batches","recipes","suppliers","waste_events","forecast_runs","forecast_predictions"}.issubset(tables)

def test_forecast_upgrade_preserves_existing_data(tmp_path):
    db=tmp_path / "existing.db"; root=Path(__file__).resolve().parents[1]
    config=Config(str(root / "alembic.ini")); config.set_main_option("script_location",str(root / "migrations")); config.set_main_option("sqlalchemy.url",f"sqlite:///{db}")
    command.upgrade(config,"20261108_initial")
    engine=create_engine(f"sqlite:///{db}")
    with engine.begin() as con: con.execute(text("INSERT INTO ingredients (id,name,unit,storage_category,created_at) VALUES ('kept','kept ingredient','kg','chilled','2026-01-01')"))
    command.upgrade(config,"head")
    with engine.connect() as con: assert con.execute(text("SELECT name FROM ingredients WHERE id='kept'")).scalar()=="kept ingredient"
