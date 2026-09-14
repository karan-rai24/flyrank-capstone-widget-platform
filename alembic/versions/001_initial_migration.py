"""initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create widgets table
    op.create_table(
        'widgets',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('owner_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('type', sa.String(50), nullable=False, server_default='lead_capture'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('form_config', sa.JSON, nullable=True),
        sa.Column('button_text', sa.String(100), nullable=False, server_default='Submit'),
        sa.Column('display_options', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create submissions table
    op.create_table(
        'submissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('widget_id', sa.String(36), sa.ForeignKey('widgets.id'), nullable=False, index=True),
        sa.Column('submission_data', sa.JSON, nullable=False),
        sa.Column('visitor_ip', sa.String(45), nullable=True),
        sa.Column('country', sa.String(100), nullable=True),
        sa.Column('city', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('submissions')
    op.drop_table('widgets')
    op.drop_table('users')
