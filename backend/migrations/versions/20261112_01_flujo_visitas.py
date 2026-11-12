"""Ampliar flujo de arriendos: visitas y contratos con información completa."""

from alembic import op
import sqlalchemy as sa

revision = "20261112_01"
down_revision = "20261111_01"
branch_labels = None
depends_on = None


def _agregar_columna_si_falta(inspector, tabla, columna, tipo, **kwargs):
    existentes = {col["name"] for col in inspector.get_columns(tabla)}
    if columna not in existentes:
        op.add_column(tabla, sa.Column(columna, tipo, **kwargs))


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1. Columnas en solicitudes_arriendo
    _agregar_columna_si_falta(
        inspector, "solicitudes_arriendo", "cedula_arrendatario", sa.String(20), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "solicitudes_arriendo", "telefono_arrendatario", sa.String(20), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "solicitudes_arriendo", "fecha_visita_propuesta", sa.Date(), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "solicitudes_arriendo", "fecha_visita_confirmada", sa.Date(), nullable=True
    )

    # 2. Nuevos valores en enum estado_solicitud
    op.execute("ALTER TYPE estado_solicitud ADD VALUE IF NOT EXISTS 'pendiente_visita'")
    op.execute("ALTER TYPE estado_solicitud ADD VALUE IF NOT EXISTS 'visita_programada'")
    op.execute("ALTER TYPE estado_solicitud ADD VALUE IF NOT EXISTS 'contrato_generado'")

    # 3. Columnas en contratos_arriendo
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "numero_contrato", sa.String(20), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "trabaja", sa.Boolean(), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "empresa", sa.String(200), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "cargo", sa.String(200), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "ingreso_mensual", sa.Numeric(12, 2), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "fiador_nombre", sa.String(200), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "fiador_cedula", sa.String(20), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "fiador_telefono", sa.String(20), nullable=True
    )
    _agregar_columna_si_falta(
        inspector, "contratos_arriendo", "clausulas_adicionales", sa.Text(), nullable=True
    )

    # 5. Generar numero_contrato para existentes
    op.execute(
        """
        UPDATE contratos_arriendo
        SET numero_contrato = 'RNT-' || LPAD(id::text, 6, '0')
        WHERE numero_contrato IS NULL
        """
    )


def downgrade():
    op.drop_column("contratos_arriendo", "clausulas_adicionales")
    op.drop_column("contratos_arriendo", "fiador_telefono")
    op.drop_column("contratos_arriendo", "fiador_cedula")
    op.drop_column("contratos_arriendo", "fiador_nombre")
    op.drop_column("contratos_arriendo", "ingreso_mensual")
    op.drop_column("contratos_arriendo", "cargo")
    op.drop_column("contratos_arriendo", "empresa")
    op.drop_column("contratos_arriendo", "trabaja")
    op.drop_column("contratos_arriendo", "numero_contrato")
    op.drop_column("solicitudes_arriendo", "fecha_visita_confirmada")
    op.drop_column("solicitudes_arriendo", "fecha_visita_propuesta")
    op.drop_column("solicitudes_arriendo", "telefono_arrendatario")
    op.drop_column("solicitudes_arriendo", "cedula_arrendatario")
