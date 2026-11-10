"""Include Medellín's 16 urban communes in the location catalog."""

import sqlalchemy as sa
from alembic import op

revision = "20261111_01"
down_revision = "20261110_01"
branch_labels = None
depends_on = None


COMUNAS = (
    ("Comuna 1 - Popular", "Nororiental"),
    ("Comuna 2 - Santa Cruz", "Nororiental"),
    ("Comuna 3 - Manrique", "Nororiental"),
    ("Comuna 4 - Aranjuez", "Nororiental"),
    ("Comuna 5 - Castilla", "Noroccidental"),
    ("Comuna 6 - Doce de Octubre", "Noroccidental"),
    ("Comuna 7 - Robledo", "Noroccidental"),
    ("Comuna 8 - Villa Hermosa", "Centro-oriental"),
    ("Comuna 9 - Buenos Aires", "Centro-oriental"),
    ("Comuna 10 - La Candelaria", "Centro-oriental"),
    ("Comuna 11 - Laureles-Estadio", "Centro-occidental"),
    ("Comuna 12 - La América", "Centro-occidental"),
    ("Comuna 13 - San Javier", "Centro-occidental"),
    ("Comuna 14 - El Poblado", "Suroriental"),
    ("Comuna 15 - Guayabal", "Suroccidental"),
    ("Comuna 16 - Belén", "Suroccidental"),
)


def upgrade():
    bind = op.get_bind()
    barrios = sa.Table("barrios", sa.MetaData(), autoload_with=bind)
    existentes = {
        (nombre.casefold(), comuna.casefold())
        for nombre, comuna in bind.execute(
            sa.select(barrios.c.nombre, barrios.c.comuna)
        )
    }
    nuevos = [
        {
            "nombre": nombre,
            "comuna": nombre,
            "zona": zona,
            "tipo": "comuna",
        }
        for nombre, zona in COMUNAS
        if (nombre.casefold(), nombre.casefold()) not in existentes
    ]
    if nuevos:
        op.bulk_insert(barrios, nuevos)


def downgrade():
    # Keep catalog data intact; removals could break properties referencing it.
    pass
