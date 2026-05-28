"""add incident tables

Revision ID: 20260526_01
Revises: 
Create Date: 2026-05-26 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '20260526_01'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # incidents
    op.create_table(
        'incidents',
        sa.Column('incident_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('incident_status', sa.String(), nullable=False),
        sa.Column('sla_state', sa.String(), nullable=False),
        sa.Column('seller_account_id', sa.String(), nullable=True),
        sa.Column('environment', sa.String(), nullable=True),
        sa.Column('assigned_to', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('ack_due_at', sa.DateTime(), nullable=True),
        sa.Column('resolve_due_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('duplicate_of_incident_id', UUID(as_uuid=True), nullable=True),
        sa.Column('root_cause_code', sa.String(), nullable=True),
        sa.Column('is_reopened', sa.Boolean(), nullable=True, default=False),
        sa.Column('trigger_source', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_incidents_opened_at', 'incidents', [sa.text('opened_at DESC')])
    op.create_index('idx_incidents_seller', 'incidents', ['seller_account_id'])
    op.create_index('idx_incidents_env', 'incidents', ['environment'])
    op.create_index('idx_incidents_status', 'incidents', ['incident_status'])
    op.create_index('idx_incidents_sla', 'incidents', ['sla_state'])
    op.create_index('idx_incidents_created_at', 'incidents', [sa.text('created_at DESC')])

    # incident_events
    op.create_table(
        'incident_events',
        sa.Column('event_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.incident_id'), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('from_status', sa.String(), nullable=True),
        sa.Column('to_status', sa.String(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('actor_type', sa.String(), nullable=False),
        sa.Column('actor_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=True),
    )
    op.create_index('idx_incident_events_created_at', 'incident_events', ['created_at'])

    # incident_links
    op.create_table(
        'incident_links',
        sa.Column('link_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', UUID(as_uuid=True), sa.ForeignKey('incidents.incident_id'), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('idx_incident_links_entity', 'incident_links', ['entity_type', 'entity_id'])

def downgrade():
    op.drop_table('incident_links')
    op.drop_table('incident_events')
    op.drop_table('incidents')
