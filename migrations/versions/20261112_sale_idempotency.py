"""enforce daily-sale idempotency without deleting existing local data"""
from alembic import op
from sqlalchemy import inspect

revision="20261112_sale_idempotency"
down_revision="20261111_supplier_ingredients"
branch_labels=None
depends_on=None

def upgrade():
    indexes={item["name"] for item in inspect(op.get_bind()).get_indexes("daily_sales")}
    if "uq_daily_sales_menu_item_sold_on" not in indexes:
        op.create_index("uq_daily_sales_menu_item_sold_on","daily_sales",["menu_item","sold_on"],unique=True)

def downgrade():
    # Intentionally retained: local-demo migrations are data-preserving.
    pass
