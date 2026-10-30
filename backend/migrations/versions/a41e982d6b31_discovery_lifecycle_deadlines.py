"""Add scheme lifecycle, deadline monitoring, source discovery registry, and audit logging

Revision ID: a41e982d6b31
Revises: 2709851f4c4b
Create Date: 2026-10-25 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a41e982d6b31'
down_revision: Union[str, Sequence[str], None] = '2709851f4c4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend schemes table with lifecycle, category, organization, and deadline fields
    with op.batch_alter_table('schemes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('category', sa.String(length=64), server_default='finance_credit', nullable=True))
        batch_op.add_column(sa.Column('organization', sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column('application_status', sa.String(length=32), server_default='unknown', nullable=True))
        batch_op.add_column(sa.Column('claim_status', sa.String(length=32), server_default='unknown', nullable=True))
        batch_op.add_column(sa.Column('application_start_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('application_deadline', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('claim_deadline', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('is_rolling', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('financial_year_cycle', sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column('last_verified_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('next_verification_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('official_application_url', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('official_guidelines_url', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('official_notification_url', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('confidence_score', sa.Float(), server_default='1.0', nullable=True))
        batch_op.add_column(sa.Column('status_history', sa.JSON(), nullable=True))

        batch_op.create_index(batch_op.f('ix_schemes_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_schemes_organization'), ['organization'], unique=False)
        batch_op.create_index(batch_op.f('ix_schemes_application_status'), ['application_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_schemes_claim_status'), ['claim_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_schemes_application_deadline'), ['application_deadline'], unique=False)

    # 2. Create discovered_sources table
    op.create_table(
        'discovered_sources',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('base_url', sa.Text(), nullable=False),
        sa.Column('discovery_endpoint', sa.Text(), nullable=False),
        sa.Column('discovery_method', sa.String(length=64), server_default='html_directory', nullable=True),
        sa.Column('polling_frequency_hours', sa.Integer(), server_default='24', nullable=True),
        sa.Column('last_checked_at', sa.DateTime(), nullable=True),
        sa.Column('last_successful_at', sa.DateTime(), nullable=True),
        sa.Column('health_status', sa.String(length=32), server_default='healthy', nullable=True),
        sa.Column('error_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), server_default='1', nullable=True),
        sa.Column('headers_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discovered_sources_source_type'), 'discovered_sources', ['source_type'], unique=False)
    op.create_index(op.f('ix_discovered_sources_health_status'), 'discovered_sources', ['health_status'], unique=False)
    op.create_index(op.f('ix_discovered_sources_is_enabled'), 'discovered_sources', ['is_enabled'], unique=False)

    # 3. Create scheme_deadline_alerts table
    op.create_table(
        'scheme_deadline_alerts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('scheme_id', sa.String(length=64), nullable=False),
        sa.Column('alert_type', sa.String(length=64), nullable=False),
        sa.Column('target_date', sa.DateTime(), nullable=True),
        sa.Column('days_remaining', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_dismissed', sa.Boolean(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheme_deadline_alerts_scheme_id'), 'scheme_deadline_alerts', ['scheme_id'], unique=False)
    op.create_index(op.f('ix_scheme_deadline_alerts_alert_type'), 'scheme_deadline_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_scheme_deadline_alerts_is_dismissed'), 'scheme_deadline_alerts', ['is_dismissed'], unique=False)

    # 4. Create discovery_audit_logs table
    op.create_table(
        'discovery_audit_logs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('scheme_id', sa.String(length=64), nullable=True),
        sa.Column('source_id', sa.String(length=64), nullable=True),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('previous_state', sa.JSON(), nullable=True),
        sa.Column('new_state', sa.JSON(), nullable=True),
        sa.Column('supporting_evidence', sa.Text(), nullable=True),
        sa.Column('source_clause_or_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_discovery_audit_logs_scheme_id'), 'discovery_audit_logs', ['scheme_id'], unique=False)
    op.create_index(op.f('ix_discovery_audit_logs_event_type'), 'discovery_audit_logs', ['event_type'], unique=False)


def downgrade() -> None:
    op.drop_table('discovery_audit_logs')
    op.drop_table('scheme_deadline_alerts')
    op.drop_table('discovered_sources')
    with op.batch_alter_table('schemes', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_schemes_application_deadline'))
        batch_op.drop_index(batch_op.f('ix_schemes_claim_status'))
        batch_op.drop_index(batch_op.f('ix_schemes_application_status'))
        batch_op.drop_index(batch_op.f('ix_schemes_organization'))
        batch_op.drop_index(batch_op.f('ix_schemes_category'))
        batch_op.drop_column('status_history')
        batch_op.drop_column('confidence_score')
        batch_op.drop_column('official_notification_url')
        batch_op.drop_column('official_guidelines_url')
        batch_op.drop_column('official_application_url')
        batch_op.drop_column('next_verification_at')
        batch_op.drop_column('last_verified_at')
        batch_op.drop_column('financial_year_cycle')
        batch_op.drop_column('is_rolling')
        batch_op.drop_column('claim_deadline')
        batch_op.drop_column('application_deadline')
        batch_op.drop_column('application_start_date')
        batch_op.drop_column('claim_status')
        batch_op.drop_column('application_status')
        batch_op.drop_column('organization')
        batch_op.drop_column('category')
