"""add learning tables

Revision ID: phase_o_learning
Revises: phase_n_policy
Create Date: 2026-05-26 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'phase_o_learning'
down_revision = 'phase_n_policy'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. learning_records
    op.create_table(
        'learning_records',
        sa.Column('learning_record_id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('root_cause_category', sa.String(50), nullable=False),
        sa.Column('root_cause_subcategory', sa.String(255), nullable=True),
        sa.Column('impact_scope', sa.String(50), nullable=False),
        sa.Column('seller_account_id', sa.String(255), nullable=True),
        sa.Column('environment', sa.String(255), nullable=True),
        sa.Column('linked_incident_id', sa.String(36), nullable=True),
        sa.Column('linked_policy_id', sa.String(36), nullable=True),
        sa.Column('linked_report_id', sa.String(36), nullable=True),
        sa.Column('is_false_positive', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_false_negative', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('is_near_miss', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('effectiveness_rating', sa.String(50), nullable=False),
        sa.Column('confidence_level', sa.String(50), nullable=False),
        sa.Column('recommended_action_type', sa.String(255), nullable=True),
        sa.Column('recommended_change_scope', sa.String(255), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True)
    )
    op.create_index('ix_learning_records_status_created_at', 'learning_records', ['status', 'created_at'])
    op.create_index('ix_learning_records_root_cause_category', 'learning_records', ['root_cause_category'])
    op.create_index('ix_learning_records_seller_env', 'learning_records', ['seller_account_id', 'environment'])
    op.create_index('ix_learning_records_linked_incident', 'learning_records', ['linked_incident_id'])
    op.create_index('ix_learning_records_linked_policy', 'learning_records', ['linked_policy_id'])
    op.create_index('ix_learning_records_false_signals', 'learning_records', ['is_false_positive', 'is_false_negative'])

    # 2. root_cause_analyses
    op.create_table(
        'root_cause_analyses',
        sa.Column('rca_id', sa.String(36), primary_key=True),
        sa.Column('learning_record_id', sa.String(36), sa.ForeignKey('learning_records.learning_record_id'), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('observed_symptoms', sa.Text(), nullable=False),
        sa.Column('primary_cause', sa.Text(), nullable=False),
        sa.Column('contributing_factors', sa.Text(), nullable=False),
        sa.Column('detection_gap', sa.Text(), nullable=True),
        sa.Column('mitigation_taken', sa.Text(), nullable=False),
        sa.Column('resolution_summary', sa.Text(), nullable=False),
        sa.Column('prevention_proposal', sa.Text(), nullable=True),
        sa.Column('evidence_snapshot', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_rcas_learning_record_id', 'root_cause_analyses', ['learning_record_id'])
    op.create_index('ix_rcas_created_at', 'root_cause_analyses', ['created_at'])

    # 3. learning_recommendations
    op.create_table(
        'learning_recommendations',
        sa.Column('recommendation_id', sa.String(36), primary_key=True),
        sa.Column('learning_record_id', sa.String(36), sa.ForeignKey('learning_records.learning_record_id'), nullable=False),
        sa.Column('recommendation_type', sa.String(50), nullable=False),
        sa.Column('target_phase', sa.String(50), nullable=False),
        sa.Column('target_scope', sa.String(255), nullable=True),
        sa.Column('proposal_summary', sa.Text(), nullable=False),
        sa.Column('proposal_details', sa.Text(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('recommendation_status', sa.String(50), nullable=False),
        sa.Column('review_due_at', sa.DateTime(), nullable=False),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('implemented_in_phase', sa.String(50), nullable=True),
        sa.Column('implemented_commit_ref', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )
    op.create_index('ix_lrecs_learning_record_id', 'learning_recommendations', ['learning_record_id'])
    op.create_index('ix_lrecs_status', 'learning_recommendations', ['recommendation_status'])
    op.create_index('ix_lrecs_target_phase', 'learning_recommendations', ['target_phase'])
    op.create_index('ix_lrecs_review_due_status', 'learning_recommendations', ['review_due_at', 'recommendation_status'])

def downgrade() -> None:
    op.drop_table('learning_recommendations')
    op.drop_table('root_cause_analyses')
    op.drop_table('learning_records')
