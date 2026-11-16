"""Reconcile core schema fields for databases stamped from the bootstrap SQL."""

import sqlalchemy as sa
from alembic import op

revision = "20261115_01"
down_revision = "20261112_01"
branch_labels = None
depends_on = None


def _agregar_columna_si_falta(tabla, columna, tipo, nullable=True, server_default=None):
    existentes = {item["name"] for item in sa.inspect(op.get_bind()).get_columns(tabla)}
    if columna not in existentes:
        op.add_column(
            tabla,
            sa.Column(columna, tipo, nullable=nullable, server_default=server_default),
        )


def upgrade():
    op.execute("ALTER TYPE rol_usuario ADD VALUE IF NOT EXISTS 'admin'")
    for valor in (
        "apartaestudio",
        "local_comercial",
        "oficina",
        "bodega",
        "finca",
    ):
        op.execute(f"ALTER TYPE tipo_propiedad ADD VALUE IF NOT EXISTS '{valor}'")
    for valor in ("pendiente_visita", "visita_programada", "contrato_generado"):
        op.execute(f"ALTER TYPE estado_solicitud ADD VALUE IF NOT EXISTS '{valor}'")

    _agregar_columna_si_falta(
        "barrios", "tipo", sa.String(20), nullable=False, server_default="barrio"
    )
    _agregar_columna_si_falta(
        "solicitudes_arriendo", "cedula_arrendatario", sa.String(20)
    )
    _agregar_columna_si_falta(
        "solicitudes_arriendo", "telefono_arrendatario", sa.String(20)
    )
    _agregar_columna_si_falta(
        "solicitudes_arriendo", "fecha_visita_propuesta", sa.Date()
    )
    _agregar_columna_si_falta(
        "solicitudes_arriendo", "fecha_visita_confirmada", sa.Date()
    )
    _agregar_columna_si_falta("contratos_arriendo", "numero_contrato", sa.String(20))
    _agregar_columna_si_falta("contratos_arriendo", "trabaja", sa.Boolean())
    _agregar_columna_si_falta("contratos_arriendo", "empresa", sa.String(200))
    _agregar_columna_si_falta("contratos_arriendo", "cargo", sa.String(200))
    _agregar_columna_si_falta(
        "contratos_arriendo", "ingreso_mensual", sa.Numeric(12, 2)
    )
    _agregar_columna_si_falta("contratos_arriendo", "fiador_nombre", sa.String(200))
    _agregar_columna_si_falta("contratos_arriendo", "fiador_cedula", sa.String(20))
    _agregar_columna_si_falta("contratos_arriendo", "fiador_telefono", sa.String(20))
    _agregar_columna_si_falta(
        "contratos_arriendo", "clausulas_adicionales", sa.Text()
    )

    inspector = sa.inspect(op.get_bind())
    tiene_numero_unico = any(
        constraint.get("column_names") == ["numero_contrato"]
        for constraint in inspector.get_unique_constraints("contratos_arriendo")
    ) or any(
        index.get("unique") and index.get("column_names") == ["numero_contrato"]
        for index in inspector.get_indexes("contratos_arriendo")
    )
    if not tiene_numero_unico:
        op.create_unique_constraint(
            "uq_contratos_arriendo_numero_contrato",
            "contratos_arriendo",
            ["numero_contrato"],
        )


def downgrade():
    raise RuntimeError(
        "Esta reconciliación es aditiva y no se puede revertir sin riesgo de perder datos."
    )
