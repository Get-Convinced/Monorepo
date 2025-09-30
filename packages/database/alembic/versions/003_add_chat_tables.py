"""Add chat tables for RAG-powered conversations

Revision ID: 003
Revises: 59880a0db462
Create Date: 2025-01-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '59880a0db462'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create chat_sessions table
    op.create_table('chat_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=False),
        sa.Column('max_context_messages', sa.Integer(), nullable=False),
        sa.Column('session_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_sessions_active', 'chat_sessions', ['user_id', 'is_active'], unique=False)
    op.create_index('idx_chat_sessions_org_updated', 'chat_sessions', ['organization_id', 'updated_at'], unique=False)
    op.create_index('idx_chat_sessions_user_updated', 'chat_sessions', ['user_id', 'updated_at'], unique=False)
    op.create_index(op.f('ix_chat_sessions_is_active'), 'chat_sessions', ['is_active'], unique=False)
    op.create_index(op.f('ix_chat_sessions_organization_id'), 'chat_sessions', ['organization_id'], unique=False)
    op.create_index(op.f('ix_chat_sessions_user_id'), 'chat_sessions', ['user_id'], unique=False)
    
    # Create chat_messages table
    op.create_table('chat_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('temperature_used', sa.Float(), nullable=True),
        sa.Column('tokens_prompt', sa.Integer(), nullable=True),
        sa.Column('tokens_completion', sa.Integer(), nullable=True),
        sa.Column('tokens_total', sa.Integer(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('message_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_messages_role', 'chat_messages', ['session_id', 'role'], unique=False)
    op.create_index('idx_chat_messages_session_created', 'chat_messages', ['session_id', 'created_at'], unique=False)
    op.create_index(op.f('ix_chat_messages_role'), 'chat_messages', ['role'], unique=False)
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)
    
    # Create chat_sources table
    op.create_table('chat_sources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('message_id', sa.UUID(), nullable=False),
        sa.Column('ragie_document_id', sa.String(length=255), nullable=False),
        sa.Column('ragie_chunk_id', sa.String(length=255), nullable=True),
        sa.Column('document_name', sa.String(length=500), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('chunk_text', sa.Text(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('source_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['chat_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chat_sources_message', 'chat_sources', ['message_id'], unique=False)
    op.create_index('idx_chat_sources_ragie_doc', 'chat_sources', ['ragie_document_id'], unique=False)
    op.create_index(op.f('ix_chat_sources_message_id'), 'chat_sources', ['message_id'], unique=False)
    op.create_index(op.f('ix_chat_sources_ragie_document_id'), 'chat_sources', ['ragie_document_id'], unique=False)
    
    # Create chat_rate_limits table
    op.create_table('chat_rate_limits',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('messages_count', sa.Integer(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('window_duration_hours', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_rate_limits_org_window', 'chat_rate_limits', ['organization_id', 'window_start'], unique=False)
    op.create_index('idx_rate_limits_user_window', 'chat_rate_limits', ['user_id', 'window_start'], unique=False)
    op.create_index(op.f('ix_chat_rate_limits_organization_id'), 'chat_rate_limits', ['organization_id'], unique=False)
    op.create_index(op.f('ix_chat_rate_limits_user_id'), 'chat_rate_limits', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('chat_rate_limits')
    op.drop_table('chat_sources')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
