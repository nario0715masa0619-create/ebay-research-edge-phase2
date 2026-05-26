"""add_report_artifacts_table

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2026-05-26 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('report_artifacts',
        sa.Column('report_id', sa.String(length=36), nullable=False),
        sa.Column('report_type', sa.String(length=100), nullable=False),
        sa.Column('format', sa.String(length=20), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('generated_by', sa.String(length=100), nullable=False),
        sa.Column('trigger_source', sa.String(length=50), nullable=False),
        sa.Column('filter_snapshot', sa.JSON(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('blob_ref', sa.String(length=500), nullable=True),
        sa.Column('seller_account_id', sa.String(length=100), nullable=True),
        sa.Column('environment', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.PrimaryKeyConstraint('report_id')
    )
    op.create_index('idx_report_artifacts_generated_at', 'report_artifacts', [sa.text('generated_at DESC')], unique=False)
    op.create_index('idx_report_artifacts_seller_account_id', 'report_artifacts', ['seller_account_id'], unique=False)
    op.create_index('idx_report_artifacts_report_type', 'report_artifacts', ['report_type'], unique=False)
    op.create_index('idx_report_artifacts_created_at', 'report_artifacts', [sa.text('created_at DESC')], unique=False)

def downgrade() -> None:
    op.drop_index('idx_report_artifacts_created_at', table_name='report_artifacts')
    op.drop_index('idx_report_artifacts_report_type', table_name='report_artifacts')
    op.drop_index('idx_report_artifacts_seller_account_id', table_name='report_artifacts')
    op.drop_index('idx_report_artifacts_generated_at', table_name='report_artifacts')
    op.drop_table('report_artifacts')
