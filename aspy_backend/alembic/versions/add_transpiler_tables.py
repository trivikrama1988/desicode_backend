# alembic/versions/add_transpiler_tables.py
"""Add transpiler and execution tables
Revision ID: add_transpiler_tables
Create Date: 2025-12-11 21:39:45

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_transpiler_tables'
down_revision = 'initial'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to plans table
    op.add_column('plans', sa.Column('monthly_executions', sa.Integer(), nullable=True, server_default='10'))
    op.add_column('plans', sa.Column('max_execution_time', sa.Integer(), nullable=True, server_default='30'))
    op.add_column('plans', sa.Column('max_code_length', sa.Integer(), nullable=True, server_default='10000'))
    op.add_column('plans', sa.Column('concurrent_executions', sa.Integer(), nullable=True, server_default='1'))
    op.add_column('plans', sa.Column('api_access', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('plans', sa.Column('priority_support', sa.Boolean(), nullable=True, server_default='false'))

    # Add new columns to subscriptions table
    op.add_column('subscriptions', sa.Column('executions_this_month', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('subscriptions', sa.Column('total_executions', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('subscriptions', sa.Column('quota_reset_date', sa.DateTime(timezone=True), nullable=True))

    # Add new columns to users table
    op.add_column('users', sa.Column('total_code_executions', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('last_execution_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('preferred_language', sa.String(length=50), nullable=True))

    # Create code_executions table
    op.create_table('code_executions',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('execution_id', sa.String(), nullable=False),
                    sa.Column('language', sa.String(), nullable=False),
                    sa.Column('code_hash', sa.String(), nullable=True),
                    sa.Column('input_data', sa.Text(), nullable=True),
                    sa.Column('output', sa.Text(), nullable=True),
                    sa.Column('errors', sa.Text(), nullable=True),
                    sa.Column('transpiled_code', sa.Text(), nullable=True),
                    sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
                    sa.Column('execution_time_ms', sa.Integer(), nullable=True),
                    sa.Column('quota_used', sa.Integer(), nullable=False, server_default='1'),
                    sa.Column('ip_address', sa.String(), nullable=True),
                    sa.Column('user_agent', sa.String(), nullable=True),
                    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
                    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )

    # Create indexes
    op.create_index(op.f('ix_code_executions_execution_id'), 'code_executions', ['execution_id'], unique=True)
    op.create_index(op.f('ix_code_executions_user_id'), 'code_executions', ['user_id'])
    op.create_index(op.f('ix_code_executions_code_hash'), 'code_executions', ['code_hash'])
    op.create_index(op.f('ix_code_executions_created_at'), 'code_executions', ['created_at'])


def downgrade():
    # Drop tables and columns in reverse order
    op.drop_index(op.f('ix_code_executions_created_at'), table_name='code_executions')
    op.drop_index(op.f('ix_code_executions_code_hash'), table_name='code_executions')
    op.drop_index(op.f('ix_code_executions_user_id'), table_name='code_executions')
    op.drop_index(op.f('ix_code_executions_execution_id'), table_name='code_executions')
    op.drop_table('code_executions')

    op.drop_column('users', 'preferred_language')
    op.drop_column('users', 'last_execution_at')
    op.drop_column('users', 'total_code_executions')

    op.drop_column('subscriptions', 'quota_reset_date')
    op.drop_column('subscriptions', 'total_executions')
    op.drop_column('subscriptions', 'executions_this_month')

    op.drop_column('plans', 'priority_support')
    op.drop_column('plans', 'api_access')
    op.drop_column('plans', 'concurrent_executions')
    op.drop_column('plans', 'max_code_length')
    op.drop_column('plans', 'max_execution_time')
    op.drop_column('plans', 'monthly_executions')