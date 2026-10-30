"""fix ck_user_role to include board_member

Databases created before the model gained the board_member role have a stale
CHECK constraint that rejects board_member inserts even though the ORM allows
it. Recreate the constraint so the DB matches the model.

Revision ID: 20261030_0005
Revises: 20261030_0004
Create Date: 2026-10-30 00:05:00.000000
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20261030_0005"
down_revision = "20261030_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_user_role", "user", type_="check")
    op.create_check_constraint(
        "ck_user_role",
        "user",
        "role IN ('student', 'admin', 'staff', 'board_member')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_role", "user", type_="check")
    op.create_check_constraint(
        "ck_user_role",
        "user",
        "role IN ('student', 'admin', 'staff')",
    )
