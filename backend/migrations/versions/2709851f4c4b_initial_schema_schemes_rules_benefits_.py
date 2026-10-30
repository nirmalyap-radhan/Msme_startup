"""Initial schema: schemes, rules, benefits, profiles, tracking

Revision ID: 2709851f4c4b
Revises: 
Create Date: 2026-10-24 22:37:37.864959

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2709851f4c4b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. source_documents
    op.create_table(
        'source_documents',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('local_path', sa.Text(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('retrieved_at_utc', sa.DateTime(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('is_scanned', sa.Boolean(), nullable=True),
        sa.Column('ocr_applied', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sha256_hash')
    )

    # 2. document_passages
    op.create_table(
        'document_passages',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('document_id', sa.String(length=64), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=False),
        sa.Column('section_heading', sa.String(length=256), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('character_count', sa.Integer(), nullable=True),
        sa.Column('is_ocr', sa.Boolean(), nullable=True),
        sa.Column('ocr_confidence', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['source_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. schemes
    op.create_table(
        'schemes',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('official_name', sa.String(length=512), nullable=False),
        sa.Column('official_name_odia', sa.String(length=512), nullable=True),
        sa.Column('department', sa.String(length=256), nullable=False),
        sa.Column('implementing_agency', sa.String(length=256), nullable=True),
        sa.Column('jurisdiction', sa.String(length=64), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('source_document_id', sa.String(length=64), nullable=False),
        sa.Column('document_sha256', sa.String(length=64), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('version', sa.String(length=16), nullable=True),
        sa.Column('effective_date', sa.String(length=32), nullable=True),
        sa.Column('expiry_date', sa.String(length=32), nullable=True),
        sa.Column('required_documents', sa.JSON(), nullable=True),
        sa.Column('application_process', sa.Text(), nullable=True),
        sa.Column('official_portal_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('verified_by_reviewer', sa.String(length=128), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('supersedes_scheme_id', sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(['source_document_id'], ['source_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. eligibility_rules
    op.create_table(
        'eligibility_rules',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('scheme_id', sa.String(length=64), nullable=False),
        sa.Column('attribute_name', sa.String(length=64), nullable=False),
        sa.Column('operator', sa.String(length=16), nullable=False),
        sa.Column('value_json', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('source_clause', sa.String(length=256), nullable=False),
        sa.Column('source_page', sa.Integer(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. benefit_rules
    op.create_table(
        'benefit_rules',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('scheme_id', sa.String(length=64), nullable=False),
        sa.Column('benefit_type', sa.String(length=64), nullable=False),
        sa.Column('formula_description', sa.Text(), nullable=False),
        sa.Column('subsidy_percentage', sa.Float(), nullable=True),
        sa.Column('max_limit_inr', sa.Float(), nullable=True),
        sa.Column('duration_years', sa.Integer(), nullable=True),
        sa.Column('source_clause', sa.String(length=256), nullable=False),
        sa.Column('source_page', sa.Integer(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. review_events
    op.create_table(
        'review_events',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('scheme_id', sa.String(length=64), nullable=False),
        sa.Column('reviewer_id', sa.String(length=64), nullable=False),
        sa.Column('reviewer_name', sa.String(length=128), nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('notes', sa.Text(), nullable=False),
        sa.Column('verified_fields', sa.JSON(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. ingestion_jobs
    op.create_table(
        'ingestion_jobs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('document_id', sa.String(length=64), nullable=True),
        sa.Column('scheme_id', sa.String(length=64), nullable=True),
        sa.Column('extraction_stats', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. user_profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=128), nullable=False),
        sa.Column('hashed_password', sa.String(length=256), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=True),
        sa.Column('enterprise_name', sa.String(length=256), nullable=True),
        sa.Column('enterprise_class', sa.String(length=32), nullable=True),
        sa.Column('sector', sa.String(length=64), nullable=True),
        sa.Column('state', sa.String(length=64), nullable=True),
        sa.Column('district', sa.String(length=64), nullable=True),
        sa.Column('udyam_number', sa.String(length=64), nullable=True),
        sa.Column('udyam_registered', sa.Boolean(), nullable=True),
        sa.Column('production_status', sa.String(length=32), nullable=True),
        sa.Column('investment_plant_machinery', sa.Float(), nullable=True),
        sa.Column('annual_turnover', sa.Float(), nullable=True),
        sa.Column('promoter_category', sa.String(length=32), nullable=True),
        sa.Column('promoter_gender', sa.String(length=32), nullable=True),
        sa.Column('working_capital_loan_sanctioned', sa.Float(), nullable=True),
        sa.Column('annual_interest_paid', sa.Float(), nullable=True),
        sa.Column('trademark_expenditure', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # 9. saved_schemes
    op.create_table(
        'saved_schemes',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('scheme_id', sa.String(length=64), nullable=False),
        sa.Column('saved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. application_tracking
    op.create_table(
        'application_tracking',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('scheme_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('acknowledgement_ref', sa.String(length=128), nullable=True),
        sa.Column('submitted_portal_url', sa.Text(), nullable=True),
        sa.Column('filing_date', sa.String(length=32), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scheme_id'], ['schemes.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('application_tracking')
    op.drop_table('saved_schemes')
    op.drop_table('user_profiles')
    op.drop_table('ingestion_jobs')
    op.drop_table('review_events')
    op.drop_table('benefit_rules')
    op.drop_table('eligibility_rules')
    op.drop_table('schemes')
    op.drop_table('document_passages')
    op.drop_table('source_documents')
