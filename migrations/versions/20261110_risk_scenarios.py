"""add persisted simulated risk scenarios"""
from alembic import op
from sqlalchemy import inspect
from apps.api.main import RiskScenarioDB
revision="20261110_risk"
down_revision="20261109_forecasts"
branch_labels=None
depends_on=None
def upgrade():
    if "risk_scenarios" not in set(inspect(op.get_bind()).get_table_names()): RiskScenarioDB.__table__.create(op.get_bind())
def downgrade():
    if "risk_scenarios" in set(inspect(op.get_bind()).get_table_names()): RiskScenarioDB.__table__.drop(op.get_bind())
