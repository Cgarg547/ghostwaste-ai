"""add persistent forecast tables safely"""
from alembic import op
from sqlalchemy import inspect
from apps.api.main import ForecastRunDB, ForecastPredictionDB

revision="20261109_forecasts"
down_revision="20261108_initial"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind(); existing=set(inspect(bind).get_table_names())
    if "forecast_runs" not in existing: ForecastRunDB.__table__.create(bind)
    if "forecast_predictions" not in existing: ForecastPredictionDB.__table__.create(bind)

def downgrade():
    bind=op.get_bind(); existing=set(inspect(bind).get_table_names())
    if "forecast_predictions" in existing: ForecastPredictionDB.__table__.drop(bind)
    if "forecast_runs" in existing: ForecastRunDB.__table__.drop(bind)
