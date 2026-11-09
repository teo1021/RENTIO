"""Add enabled account roles for landlord and tenant modes."""

from alembic import op
import sqlalchemy as sa

revision = "20261102_01"
down_revision = "20261031_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "usuarios",
        sa.Column("roles", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.execute(
        """
        UPDATE usuarios
        SET roles = CASE
            WHEN rol = 'admin' THEN '["admin"]'::json
            ELSE '["arrendatario", "propietario"]'::json
        END
        """
    )


def downgrade():
    op.drop_column("usuarios", "roles")
