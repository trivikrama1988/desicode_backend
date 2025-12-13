# alembic/versions/add_webhook_url.py
"""Add webhook_url to user model
Revision ID: add_webhook_url
Create Date: 2025-12-13 12:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_webhook_url'
down_revision = 'add_transpiler_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Add webhook_url column to users table
    op.add_column('users', sa.Column('webhook_url', sa.String(length=500), nullable=True))


def downgrade():
    # Remove webhook_url column from users table
    op.drop_column('users', 'webhook_url')
