"""Create persistent marketing chat tables."""

from alembic import op
import sqlalchemy as sa

revision = "20261031_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA IF NOT EXISTS ia_marketing")
    op.create_table(
        "conversaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("propietario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("propiedad_id", sa.Integer(), sa.ForeignKey("propiedades.id", ondelete="SET NULL")),
        sa.Column("estado", sa.String(20), nullable=False, server_default="recopilando"),
        sa.Column("datos_recopilados", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("fecha_actualizacion", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("estado IN ('recopilando','lista','generada','cerrada')", name="ck_ia_conversacion_estado"),
        schema="ia_marketing",
    )
    op.create_index("ix_ia_conversaciones_propietario", "conversaciones", ["propietario_id", "fecha_actualizacion"], schema="ia_marketing")
    op.create_index("ix_ia_conversaciones_propiedad", "conversaciones", ["propiedad_id"], schema="ia_marketing")
    op.create_table(
        "mensajes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversacion_id", sa.Integer(), sa.ForeignKey("ia_marketing.conversaciones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("datos_extraidos", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("rol IN ('usuario','asistente')", name="ck_ia_mensaje_rol"),
        schema="ia_marketing",
    )
    op.create_index("ix_ia_mensajes_conversacion_id", "mensajes", ["conversacion_id"], schema="ia_marketing")
    op.create_table(
        "resultados_generados",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversacion_id", sa.Integer(), sa.ForeignKey("ia_marketing.conversaciones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("propiedad_id", sa.Integer(), sa.ForeignKey("propiedades.id", ondelete="SET NULL")),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("precio_sugerido", sa.Numeric(12, 2)),
        sa.Column("precio_minimo", sa.Numeric(12, 2)),
        sa.Column("precio_maximo", sa.Numeric(12, 2)),
        sa.Column("moneda", sa.String(3), nullable=False, server_default="COP"),
        sa.Column("datos_usados", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("fuente_datos", sa.String(100)),
        sa.Column("version_datos", sa.String(100)),
        sa.Column("metadatos_calculo", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("precio_minimo IS NULL OR precio_maximo IS NULL OR precio_minimo <= precio_maximo", name="ck_ia_rango_precio"),
        schema="ia_marketing",
    )
    op.create_index("ix_ia_resultados_conversacion_id", "resultados_generados", ["conversacion_id"], schema="ia_marketing")
    op.create_index("ix_ia_resultados_propiedad_id", "resultados_generados", ["propiedad_id"], schema="ia_marketing")


def downgrade():
    op.drop_table("resultados_generados", schema="ia_marketing")
    op.drop_table("mensajes", schema="ia_marketing")
    op.drop_table("conversaciones", schema="ia_marketing")
    op.execute("DROP SCHEMA IF EXISTS ia_marketing")
