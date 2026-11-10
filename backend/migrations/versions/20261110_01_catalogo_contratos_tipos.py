"""Add Medellín official locations, supported property types, and contract data."""

import csv
import re
import unicodedata
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "20261110_01"
down_revision = "20261102_01"
branch_labels = None
depends_on = None

TIPOS_NUEVOS = ("apartaestudio", "local_comercial", "oficina", "bodega")
FUENTE_CATALOGO = (
    "https://services1.arcgis.com/FZVaYraI7sEGQ6rF/arcgis/rest/services/"
    "shp_barrios_y_veredas_mr/FeatureServer/0"
)


def _normalizar(valor):
    normalizado = unicodedata.normalize("NFKD", valor.strip().casefold()).encode("ASCII", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", normalizado).strip()


def _agregar_columna_si_falta(inspector, tabla, columna, tipo, **kwargs):
    if columna not in {item["name"] for item in inspector.get_columns(tabla)}:
        op.add_column(tabla, sa.Column(columna, tipo, **kwargs))


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    _agregar_columna_si_falta(
        inspector,
        "barrios",
        "tipo",
        sa.String(20),
        nullable=False,
        server_default="barrio",
    )
    for valor in TIPOS_NUEVOS:
        op.execute(f"ALTER TYPE tipo_propiedad ADD VALUE IF NOT EXISTS '{valor}'")

    for columna, longitud in (
        ("arrendatario_nombre", 100),
        ("arrendatario_apellido", 100),
        ("arrendatario_cedula", 20),
        ("arrendatario_telefono", 20),
    ):
        _agregar_columna_si_falta(
            inspector,
            "solicitudes_arriendo",
            columna,
            sa.String(longitud),
            nullable=True,
        )
    _agregar_columna_si_falta(inspector, "contratos_arriendo", "contenido", sa.Text(), nullable=True)

    catalogo = Path(__file__).resolve().parents[2] / "data" / "catalogos" / "barrios_medellin_geomedellin.csv"
    if not catalogo.is_file():
        raise RuntimeError(f"No se encontró el catálogo oficial requerido: {catalogo}")

    barrios = sa.Table("barrios", sa.MetaData(), autoload_with=bind)
    existentes = bind.execute(sa.select(barrios.c.id, barrios.c.nombre, barrios.c.comuna)).all()
    por_nombre = {}
    for item in existentes:
        por_nombre.setdefault(_normalizar(item.nombre), []).append(item)

    with catalogo.open(encoding="utf-8-sig", newline="") as archivo:
        registros = list(csv.DictReader(archivo))

    oficiales = {}
    for registro in registros:
        clave = _normalizar(registro["nombre"])
        oficiales.setdefault(clave, []).append(registro)

    agregados = []
    actualizados = []
    comuna_a_codigo = {}
    for fila in registros:
        coincidencia = re.fullmatch(r"Comuna\s+(\d+)\s*-\s*(.+)", fila["comuna"], re.IGNORECASE)
        if coincidencia:
            codigo = int(coincidencia.group(1))
            comuna_a_codigo[_normalizar(fila["comuna"])] = codigo
            comuna_a_codigo[_normalizar(coincidencia.group(2))] = codigo

    for clave, filas in oficiales.items():
        for fila in filas:
            comuna_key = _normalizar(fila["comuna"])
            existente = next(
                (
                    item
                    for item in por_nombre.get(clave, [])
                    if _normalizar(item.comuna) == comuna_key
                ),
                None,
            )
            if existente:
                actualizados.append(
                    {
                        "id": existente.id,
                        "comuna": fila["comuna"],
                        "zona": fila["zona"],
                        "tipo": fila["tipo"],
                    }
                )
                continue

            candidatos_existentes = por_nombre.get(clave, [])
            if candidatos_existentes and fila["tipo"] == "barrio":
                for candidato in candidatos_existentes:
                    codigo = comuna_a_codigo.get(_normalizar(candidato.comuna))
                    if codigo and comuna_key.startswith(f"comuna {codigo} "):
                        actualizados.append(
                            {
                                "id": candidato.id,
                                "comuna": fila["comuna"],
                                "zona": fila["zona"],
                                "tipo": fila["tipo"],
                            }
                        )
                        break
                else:
                    agregados.append(
                        {
                            "nombre": fila["nombre"],
                            "comuna": fila["comuna"],
                            "zona": fila["zona"],
                            "tipo": fila["tipo"],
                        }
                    )
            else:
                agregados.append(
                    {
                        "nombre": fila["nombre"],
                        "comuna": fila["comuna"],
                        "zona": fila["zona"],
                        "tipo": fila["tipo"],
                    }
                )

    for registro in actualizados:
        bind.execute(
            barrios.update()
            .where(barrios.c.id == registro["id"])
            .values(
                comuna=registro["comuna"],
                zona=registro["zona"],
                tipo=registro["tipo"],
            )
        )
    if agregados:
        op.bulk_insert(barrios, agregados)

    print(
        f"Catálogo Medellín sincronizado desde GeoMedellín ({FUENTE_CATALOGO}): "
        f"{len(agregados)} ubicaciones agregadas, {len(actualizados)} registros existentes asociados."
    )


def downgrade():
    # Keep catalog, applicant identity, and generated contract data intact.
    pass
