"""add explicit supplier ingredient availability without altering existing data"""
from alembic import op
from sqlalchemy import inspect
from apps.api.main import SupplierIngredientDB

revision="20261111_supplier_ingredients"
down_revision="20261110_risk"
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    if "supplier_ingredients" not in set(inspect(bind).get_table_names()):
        SupplierIngredientDB.__table__.create(bind)

def downgrade():
    # Intentionally retained: local demo migrations are additive and data-preserving.
    pass
