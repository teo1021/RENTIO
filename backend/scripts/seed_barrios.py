"""
Puebla la base de datos con los barrios y comunas representativos de Medellín.

Uso:
    python scripts/seed_barrios.py
"""

from app import crear_app, db
from app.dominios.barrios.modelos import Barrio
from app.dominios.barrios.repositorios import BarrioRepositorio

DATOS_BARRIOS = [
    # ── Comuna 14: El Poblado (Zona Suroriental) ───────────────────────
    {"nombre": "Provenza", "comuna": "El Poblado", "zona": "Suroriental"},
    {"nombre": "Manila", "comuna": "El Poblado", "zona": "Suroriental"},
    {"nombre": "Castropol", "comuna": "El Poblado", "zona": "Suroriental"},
    {"nombre": "Patio Bonito", "comuna": "El Poblado", "zona": "Suroriental"},
    {"nombre": "El Tesoro", "comuna": "El Poblado", "zona": "Suroriental"},
    {"nombre": "San Lucas", "comuna": "El Poblado", "zona": "Suroriental"},
    {"nombre": "Las Lomas", "comuna": "El Poblado", "zona": "Suroriental"},
    {"nombre": "Los Naranjos", "comuna": "El Poblado", "zona": "Suroriental"},
    # ── Comuna 11: Laureles - Estadio (Zona Centro Occidental) ─────────
    {"nombre": "Laureles", "comuna": "Laureles - Estadio", "zona": "Centro Occidental"},
    {"nombre": "Conquistadores", "comuna": "Laureles - Estadio", "zona": "Centro Occidental"},
    {"nombre": "Estadio", "comuna": "Laureles - Estadio", "zona": "Centro Occidental"},
    {"nombre": "San Joaquín", "comuna": "Laureles - Estadio", "zona": "Centro Occidental"},
    {"nombre": "Florida Nueva", "comuna": "Laureles - Estadio", "zona": "Centro Occidental"},
    {"nombre": "Bolivariana", "comuna": "Laureles - Estadio", "zona": "Centro Occidental"},
    # ── Comuna 16: Belén (Zona Suroccidental) ──────────────────────────
    {"nombre": "Belén Central", "comuna": "Belén", "zona": "Suroccidental"},
    {"nombre": "Rosales", "comuna": "Belén", "zona": "Suroccidental"},
    {"nombre": "Fátima", "comuna": "Belén", "zona": "Suroccidental"},
    {"nombre": "La Palma", "comuna": "Belén", "zona": "Suroccidental"},
    {"nombre": "Los Alpes", "comuna": "Belén", "zona": "Suroccidental"},
    {"nombre": "San Bernardo", "comuna": "Belén", "zona": "Suroccidental"},
    # ── Comuna 10: La Candelaria (Centro) ──────────────────────────────
    {"nombre": "Boston", "comuna": "La Candelaria", "zona": "Centro Oriental"},
    {"nombre": "Prado", "comuna": "La Candelaria", "zona": "Centro Oriental"},
    {"nombre": "San Diego", "comuna": "La Candelaria", "zona": "Centro Oriental"},
    # ── Comuna 15: Guayabal (Zona Suroccidental) ───────────────────────
    {"nombre": "Santa Fe", "comuna": "Guayabal", "zona": "Suroccidental"},
    {"nombre": "Campo Amor", "comuna": "Guayabal", "zona": "Suroccidental"},
    # ── Comuna 7: Robledo (Zona Noroccidental) ─────────────────────────
    {"nombre": "Robledo", "comuna": "Robledo", "zona": "Noroccidental"},
    {"nombre": "Pilarica", "comuna": "Robledo", "zona": "Noroccidental"},
    {"nombre": "San Germán", "comuna": "Robledo", "zona": "Noroccidental"},
    # ── Área Metropolitana (Sur) ───────────────────────────────────────
    {"nombre": "Jardines", "comuna": "Envigado", "zona": "Sur (Valle de Aburrá)"},
    {"nombre": "Otraparte", "comuna": "Envigado", "zona": "Sur (Valle de Aburrá)"},
    {"nombre": "Zuñiga", "comuna": "Envigado", "zona": "Sur (Valle de Aburrá)"},
    {"nombre": "Calle Larga", "comuna": "Sabaneta", "zona": "Sur (Valle de Aburrá)"},
    {"nombre": "Sabaneta Real", "comuna": "Sabaneta", "zona": "Sur (Valle de Aburrá)"},
]


def main():
    app = crear_app()
    with app.app_context():
        db.create_all()
        agregados = 0
        for item in DATOS_BARRIOS:
            existente = BarrioRepositorio.obtener_por_nombre_y_comuna(
                item["nombre"], item["comuna"]
            )
            if not existente:
                barrio = Barrio(
                    nombre=item["nombre"],
                    comuna=item["comuna"],
                    zona=item["zona"],
                )
                BarrioRepositorio.guardar(barrio)
                agregados += 1

        print(
            f" Carga completa: {agregados} nuevos barrios agregados ({len(DATOS_BARRIOS)} en total)."
        )


if __name__ == "__main__":
    main()
