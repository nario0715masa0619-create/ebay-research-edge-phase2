"""add ops_policies and ops_policy_events tables

Revision ID: 20260526_ops_pol
Revises: 
Create Date: 2026-05-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260526_ops_pol'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # ops_policies table
    op.create_table(
        'ops_policies',
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scope_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(255), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('level', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('reason_summary', sa.Text(), nullable=False),
        sa.Column('evidence_summary', sa.Text(), nullable=True),
        sa.Column('linked_incident_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('effective_from', sa.DateTime(), nullable=True),
        sa.Column('effective_until', sa.DateTime(), nullable=True),
        sa.Column('review_due_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.String(255), nullable=False),
        sa.Column('approved_by', sa.String(255), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('released_at', sa.DateTime(), nullable=True),
        sa.Column('is_expired', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False)
    )

    op.create_index('ix_ops_policies_scope_target_status', 'ops_policies', ['scope_type', 'target_id', 'status'])
    op.create_index('ix_ops_policies_status_created', 'ops_policies', ['status', sa.text('created_at DESC')])
    op.create_index('ix_ops_policies_linked_incident', 'ops_policies', ['linked_incident_id'])
    op.create_index('ix_ops_policies_created_at', 'ops_policies', [sa.text('created_at DESC')])

    # ops_policy_events table
    op.create_table(
        'ops_policy_events',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ops_policies.policy_id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('from_status', sa.String(50), nullable=True),
        sa.Column('to_status', sa.String(50), nullable=False),
        sa.Column('actor_type', sa.String(50), nullable=False),
        sa.Column('actor_id', sa.String(255), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('details_json', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )

    op.create_index('ix_ops_policy_events_policy_id', 'ops_policy_events', ['policy_id'])
    op.create_index('ix_ops_policy_events_policy_created', 'ops_policy_events', ['policy_id', 'created_at'])
    op.create_index('ix_ops_policy_events_type', 'ops_policy_events', ['event_type'])
    op.create_index('ix_ops_policy_events_created', 'ops_policy_events', [sa.text('created_at DESC')])


def downgrade():
    op.drop_table('ops_policy_events')
    op.drop_table('ops_policies')
