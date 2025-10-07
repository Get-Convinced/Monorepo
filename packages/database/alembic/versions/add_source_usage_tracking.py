"""Add source usage tracking fields

Revision ID: add_source_usage_tracking
Revises: 003
Create Date: 2025-01-07

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_source_usage_tracking'
down_revision = '003'  # Depends on chat tables migration
branch_labels = None
depends_on = None


def upgrade():
    """Add source usage tracking columns to chat_sources table."""
    # Add new columns
    op.add_column('chat_sources', sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('chat_sources', sa.Column('usage_reason', sa.Text(), nullable=True))
    op.add_column('chat_sources', sa.Column('source_number', sa.Integer(), nullable=True))
    
    # Remove server_default after adding column (best practice)
    op.alter_column('chat_sources', 'is_used', server_default=None)


def downgrade():
    """Remove source usage tracking columns."""
    op.drop_column('chat_sources', 'source_number')
    op.drop_column('chat_sources', 'usage_reason')
    op.drop_column('chat_sources', 'is_used')
