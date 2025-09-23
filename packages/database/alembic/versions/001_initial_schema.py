"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ingestion_jobs table
    op.create_table('ingestion_jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('collection_name', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('created_by', sa.String(length=255), nullable=True),
    sa.Column('priority', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('job_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('processing_options', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('total_files', sa.Integer(), nullable=False),
    sa.Column('successful_files', sa.Integer(), nullable=False),
    sa.Column('failed_files', sa.Integer(), nullable=False),
    sa.Column('total_chunks_created', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ingestion_jobs_collection', 'ingestion_jobs', ['collection_name', 'status'], unique=False)
    op.create_index('idx_ingestion_jobs_status_created', 'ingestion_jobs', ['status', 'created_at'], unique=False)
    op.create_index(op.f('ix_ingestion_jobs_collection_name'), 'ingestion_jobs', ['collection_name'], unique=False)
    op.create_index(op.f('ix_ingestion_jobs_priority'), 'ingestion_jobs', ['priority'], unique=False)
    op.create_index(op.f('ix_ingestion_jobs_status'), 'ingestion_jobs', ['status'], unique=False)

    # Create processed_documents table
    op.create_table('processed_documents',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('ingestion_job_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('file_name', sa.String(length=500), nullable=False),
    sa.Column('file_path', sa.Text(), nullable=False),
    sa.Column('file_type', sa.String(length=50), nullable=False),
    sa.Column('file_size_bytes', sa.Integer(), nullable=False),
    sa.Column('file_hash', sa.String(length=64), nullable=True),
    sa.Column('processor_type', sa.String(length=50), nullable=False),
    sa.Column('processing_method', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('processing_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('structured_elements', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('page_statistics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('collection_name', sa.String(length=255), nullable=False),
    sa.Column('vector_point_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('total_chunks_created', sa.Integer(), nullable=False),
    sa.Column('total_points_stored', sa.Integer(), nullable=False),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('processing_duration_seconds', sa.Float(), nullable=True),
    sa.Column('token_usage', sa.Integer(), nullable=True),
    sa.Column('model_used', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['ingestion_job_id'], ['ingestion_jobs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('file_hash', 'collection_name', name='uq_document_file_hash_collection')
    )
    op.create_index('idx_processed_docs_file_hash', 'processed_documents', ['file_hash'], unique=False)
    op.create_index('idx_processed_docs_job_status', 'processed_documents', ['ingestion_job_id', 'status'], unique=False)
    op.create_index('idx_processed_docs_processor_type', 'processed_documents', ['processor_type', 'status'], unique=False)
    op.create_index(op.f('ix_processed_documents_collection_name'), 'processed_documents', ['collection_name'], unique=False)
    op.create_index(op.f('ix_processed_documents_file_name'), 'processed_documents', ['file_name'], unique=False)
    op.create_index(op.f('ix_processed_documents_file_type'), 'processed_documents', ['file_type'], unique=False)
    op.create_index(op.f('ix_processed_documents_processor_type'), 'processed_documents', ['processor_type'], unique=False)
    op.create_index(op.f('ix_processed_documents_status'), 'processed_documents', ['status'], unique=False)

    # Create vector_store_references table
    op.create_table('vector_store_references',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('collection_name', sa.String(length=255), nullable=False),
    sa.Column('point_id', sa.String(length=255), nullable=False),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('chunk_type', sa.String(length=100), nullable=False),
    sa.Column('content_preview', sa.Text(), nullable=True),
    sa.Column('chunk_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('embedding_model', sa.String(length=100), nullable=False),
    sa.Column('embedding_dimension', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['processed_documents.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('point_id', 'collection_name', name='uq_vector_point_id_collection')
    )
    op.create_index('idx_vector_refs_collection_point', 'vector_store_references', ['collection_name', 'point_id'], unique=False)
    op.create_index('idx_vector_refs_document_chunk', 'vector_store_references', ['document_id', 'chunk_index'], unique=False)
    op.create_index(op.f('ix_vector_store_references_chunk_type'), 'vector_store_references', ['chunk_type'], unique=False)
    op.create_index(op.f('ix_vector_store_references_collection_name'), 'vector_store_references', ['collection_name'], unique=False)
    op.create_index(op.f('ix_vector_store_references_point_id'), 'vector_store_references', ['point_id'], unique=False)

    # Create processing_statistics table
    op.create_table('processing_statistics',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('hour', sa.Integer(), nullable=True),
    sa.Column('total_documents_processed', sa.Integer(), nullable=False),
    sa.Column('successful_documents', sa.Integer(), nullable=False),
    sa.Column('failed_documents', sa.Integer(), nullable=False),
    sa.Column('gpt_documents', sa.Integer(), nullable=False),
    sa.Column('docling_documents', sa.Integer(), nullable=False),
    sa.Column('avg_processing_time_seconds', sa.Float(), nullable=True),
    sa.Column('total_processing_time_seconds', sa.Float(), nullable=False),
    sa.Column('total_tokens_used', sa.Integer(), nullable=False),
    sa.Column('avg_tokens_per_document', sa.Float(), nullable=True),
    sa.Column('file_type_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('total_chunks_created', sa.Integer(), nullable=False),
    sa.Column('total_points_stored', sa.Integer(), nullable=False),
    sa.Column('error_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_processing_stats_date', 'processing_statistics', ['date'], unique=False)
    op.create_index('idx_processing_stats_date_hour', 'processing_statistics', ['date', 'hour'], unique=False)
    op.create_index(op.f('ix_processing_statistics_hour'), 'processing_statistics', ['hour'], unique=False)

    # Create system_configuration table
    op.create_table('system_configuration',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('key', sa.String(length=255), nullable=False),
    sa.Column('value', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_by', sa.String(length=255), nullable=True),
    sa.Column('config_type', sa.String(length=100), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('key')
    )
    op.create_index(op.f('ix_system_configuration_config_type'), 'system_configuration', ['config_type'], unique=False)
    op.create_index(op.f('ix_system_configuration_is_active'), 'system_configuration', ['is_active'], unique=False)
    op.create_index(op.f('ix_system_configuration_key'), 'system_configuration', ['key'], unique=False)

    # Create processing_logs table
    op.create_table('processing_logs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('ingestion_job_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('level', sa.String(length=20), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('processor_type', sa.String(length=50), nullable=True),
    sa.Column('processing_stage', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_processing_logs_created_level', 'processing_logs', ['created_at', 'level'], unique=False)
    op.create_index('idx_processing_logs_document_level', 'processing_logs', ['document_id', 'level'], unique=False)
    op.create_index('idx_processing_logs_job_stage', 'processing_logs', ['ingestion_job_id', 'processing_stage'], unique=False)
    op.create_index(op.f('ix_processing_logs_created_at'), 'processing_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_processing_logs_level'), 'processing_logs', ['level'], unique=False)
    op.create_index(op.f('ix_processing_logs_processing_stage'), 'processing_logs', ['processing_stage'], unique=False)
    op.create_index(op.f('ix_processing_logs_processor_type'), 'processing_logs', ['processor_type'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('processing_logs')
    op.drop_table('system_configuration')
    op.drop_table('processing_statistics')
    op.drop_table('vector_store_references')
    op.drop_table('processed_documents')
    op.drop_table('ingestion_jobs')
