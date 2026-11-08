"""initial GhostWaste schema"""
from alembic import op
from apps.api.main import Base

revision = "20261108_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    Base.metadata.create_all(bind=op.get_bind())

def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
