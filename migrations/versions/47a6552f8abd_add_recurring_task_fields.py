"""Add recurring task fields

Revision ID: 47a6552f8abd
Revises:
Create Date: 2025-07-21 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "47a6552f8abd"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add recurring task fields to the tasks table
    op.add_column(
        "tasks", sa.Column("is_recurring", sa.Boolean(), nullable=True, default=False)
    )
    op.add_column(
        "tasks", sa.Column("recurrence_pattern", sa.String(50), nullable=True)
    )
    op.add_column(
        "tasks",
        sa.Column("recurrence_frequency", sa.Integer(), nullable=True, default=1),
    )
    op.add_column(
        "tasks",
        sa.Column("recurrence_end_date", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column("last_recurrence_date", sa.DateTime(timezone=True), nullable=True),
    )

    # Update existing tasks to set is_recurring to False
    op.execute("UPDATE tasks SET is_recurring = FALSE WHERE is_recurring IS NULL")


def downgrade() -> None:
    # Drop recurring task fields from the tasks table
    op.drop_column("tasks", "last_recurrence_date")
    op.drop_column("tasks", "recurrence_end_date")
    op.drop_column("tasks", "recurrence_frequency")
    op.drop_column("tasks", "recurrence_pattern")
    op.drop_column("tasks", "is_recurring")
