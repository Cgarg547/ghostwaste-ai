import os
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import URL
from apps.api.main import Base

config = context.config

db_path = os.environ.get("GHOSTWASTE_DB_PATH")
staging = os.environ.get("GHOSTWASTE_STAGING_MODE", "").lower() in {
    "1", "true", "yes"
}

if staging and not db_path:
    raise RuntimeError("Staging migrations require GHOSTWASTE_DB_PATH")

if staging and db_path:
    resolved = Path(db_path).expanduser().resolve()
    config.set_main_option(
        "sqlalchemy.url",
        URL.create("sqlite", database=str(resolved)).render_as_string(
            hide_password=False
        ),
    )

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction(): context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction(): context.run_migrations()

if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
