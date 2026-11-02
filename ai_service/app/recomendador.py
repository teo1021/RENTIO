"""
Motor de recomendación de canon de arriendo basado estrictamente en datasets de mercado.
"""

import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from app.config import settings


def normalizar_cadena(texto: str) -> str:
    """Normaliza texto eliminando tildes, caracteres especiales y pasando a minúsculas."""
    if not texto:
        return ""
    texto = texto.strip().lower()
    # Quitar tildes
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    # Reemplazar caracteres no alfanuméricos por espacios
    texto = re.sub(r"[^a-z0-9]+", " ", texto).strip()
    return texto


def slugificar(texto: str) -> str:
    """Convierte un texto a slug con guiones."""
    norm = normalizar_cadena(texto)
    return re.sub(r"\s+", "-", norm)


class RecomendadorPrecio:
    """
    Gestiona los datos de mercado de Medellín y calcula estimaciones
    empíricas de canon mensual sin dobles conteos ni extrapolaciones inventadas.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_DIR
        self.barrios_db: Dict[str, Dict[str, Any]] = {}
        self.comunas_db: Dict[str, Dict[str, Any]] = {}
        self.ciudad_resumen: Dict[str, Any] = {}
        self.ciudad_por_alcobas: Dict[int, Dict[str, Any]] = {}
        self._cargado = False
        self.cargar_datos()

    def cargar_datos(self):
        """Carga y procesa los dos datasets garantizando deduplicación."""
        df1_path = self.data_dir / "precios_arriendo_barrios_detalle_api.csv"
        df2_path = self.data_dir / "arriendo_en_medellin_por_barrio_2026_datos.csv"

        if not df1_path.exists() and not df2_path.exists():
            # Intentar buscar en ubicación alternativa
            alt_dir = Path(__file__).resolve().parent.parent.parent / "backend" / "data" / "market"
            if alt_dir.exists():
                df1_path = alt_dir / "precios_arriendo_barrios_detalle_api.csv"
                df2_path = alt_dir / "arriendo_en_medellin_por_barrio_2026_datos.csv"

        # Cargar DF2 (Dataset específico de Medellín)
        if df2_path.exists():
            df2 = pd.read_csv(df2_path)
            # 1. Resumen global
            resumen_rows = df2[df2["tabla"] == "resumen"]
            if not resumen_rows.empty:
                r = resumen_rows.iloc[0]
                self.ciudad_resumen = {
                    "avisos": int(r.get("avisos", 90019)),
                    "mediana": float(r.get("mediana", 4100000.0)),
                    "pct_con_parqueadero": float(r.get("pct_con_parqueadero", 0.7396)),
                    "rentabilidad_bruta_mediana_pct": float(r.get("rentabilidad_bruta_mediana_pct", 6.4865)),
                    "fecha_datos": str(r.get("fecha_datos", "2026-10-05")),
                }

            # 2. Por alcobas global
            alcoba_rows = df2[df2["tabla"] == "por_alcobas"]
            for _, r in alcoba_rows.iterrows():
                grupo = str(r.get("grupo", ""))
                med = float(r.get("mediana", 0))
                avisos = int(r.get("avisos", 0))
                referencia = {
                    "mediana": med,
                    "avisos": avisos,
                    "fecha_datos": str(r.get("fecha_datos", "desconocida")),
                }
                if "1" in grupo:
                    self.ciudad_por_alcobas[1] = referencia
                elif "2" in grupo:
                    self.ciudad_por_alcobas[2] = referencia
                elif "3" in grupo:
                    self.ciudad_por_alcobas[3] = referencia

            # 3. 435 Barrios específicos
            barrios_rows = df2[df2["tabla"] == "por_barrio"]
            for _, r in barrios_rows.iterrows():
                barrio_id = str(r.get("barrio_id", "")).strip().lower()
                grupo = str(r.get("grupo", "")).strip()
                if not barrio_id:
                    continue

                datos_b = {
                    "barrio_id": barrio_id,
                    "nombre": grupo,
                    "avisos": int(r.get("avisos", 0)),
                    "mediana": float(r.get("mediana", 0)),
                    "p25": float(r.get("p25", 0)),
                    "p75": float(r.get("p75", 0)),
                    "avisos_1": int(r.get("avisos_1", 0)) if not pd.isna(r.get("avisos_1")) else 0,
                    "avisos_2": int(r.get("avisos_2", 0)) if not pd.isna(r.get("avisos_2")) else 0,
                    "avisos_3mas": int(r.get("avisos_3mas", 0)) if not pd.isna(r.get("avisos_3mas")) else 0,
                    "mediana_1": float(r["mediana_1"]) if not pd.isna(r.get("mediana_1")) else None,
                    "mediana_2": float(r["mediana_2"]) if not pd.isna(r.get("mediana_2")) else None,
                    "mediana_3mas": float(r["mediana_3mas"]) if not pd.isna(r.get("mediana_3mas")) else None,
                    "con_parqueadero": int(r.get("con_parqueadero", 0)) if not pd.isna(r.get("con_parqueadero")) else 0,
                    "pct_parqueadero": float(r.get("pct_parqueadero", 0)) if not pd.isna(r.get("pct_parqueadero")) else 0,
                    "mediana_con_parqueadero": float(r["mediana_con_parqueadero"]) if not pd.isna(r.get("mediana_con_parqueadero")) else None,
                    "fuentes": int(r.get("fuentes", 0)) if not pd.isna(r.get("fuentes")) else 1,
                    "fecha_datos": str(r.get("fecha_datos", "2026-10-05")),
                }
                self.barrios_db[barrio_id] = datos_b

        # Cargar DF1 (Filtrar Medellín y extraer los 93 sectores/comunas adicionales que no duplican los 435 barrios)
        if df1_path.exists():
            df1 = pd.read_csv(df1_path)
            med1 = df1[df1["ciudad"].str.contains("Medell", na=False, case=False)]
            for _, r in med1.iterrows():
                b_id = str(r.get("barrio_id", "")).strip().lower()
                if not b_id:
                    continue
                # Si no está en los 435 barrios específicos, es una macrozona/comuna
                if b_id not in self.barrios_db:
                    nombre_formateado = b_id.replace("-", " ").title()
                    datos_c = {
                        "barrio_id": b_id,
                        "nombre": nombre_formateado,
                        "avisos": int(r.get("avisos", 0)),
                        "mediana": float(r.get("mediana", 0)),
                        "p25": float(r.get("p25", 0)),
                        "p75": float(r.get("p75", 0)),
                        "avisos_1": int(r.get("avisos_1_alcoba", 0)) if not pd.isna(r.get("avisos_1_alcoba")) else 0,
                        "avisos_2": int(r.get("avisos_2_alcobas", 0)) if not pd.isna(r.get("avisos_2_alcobas")) else 0,
                        "avisos_3mas": int(r.get("avisos_3mas_alcobas", 0)) if not pd.isna(r.get("avisos_3mas_alcobas")) else 0,
                        "mediana_1": float(r["mediana_1_alcoba"]) if not pd.isna(r.get("mediana_1_alcoba")) else None,
                        "mediana_2": float(r["mediana_2_alcobas"]) if not pd.isna(r.get("mediana_2_alcobas")) else None,
                        "mediana_3mas": float(r["mediana_3mas_alcobas"]) if not pd.isna(r.get("mediana_3mas_alcobas")) else None,
                        "con_parqueadero": int(r.get("con_parqueadero", 0)) if not pd.isna(r.get("con_parqueadero")) else 0,
                        "mediana_con_parqueadero": float(r["mediana_con_parqueadero"]) if not pd.isna(r.get("mediana_con_parqueadero")) else None,
                        "fuentes": int(r.get("fuentes", 0)) if not pd.isna(r.get("fuentes")) else 1,
                        "fecha_datos": str(r.get("fecha", "2026-10-05")),
                    }
                    self.comunas_db[b_id] = datos_c

        self._cargado = True

    def buscar_barrio(self, busqueda: str) -> Optional[Dict[str, Any]]:
        """
        Busca un barrio por coincidencia exacta o difusa normalizada.
        Prioriza barrios específicos (435) y luego comunas/macrozonas (93).
        """
        if not busqueda:
            return None

        slug_busqueda = slugificar(busqueda)
        norm_busqueda = normalizar_cadena(busqueda)

        # 1. Coincidencia exacta por slug en barrios específicos
        if slug_busqueda in self.barrios_db:
            return self.barrios_db[slug_busqueda]

        # 2. Coincidencia exacta por nombre normalizado
        for b_id, b_data in self.barrios_db.items():
            if normalizar_cadena(b_data["nombre"]) == norm_busqueda:
                return b_data

        # 3. Coincidencia por subcadena contenida en nombre de barrio
        # (ej: "poblado" puede coincidir con "Altos del Poblado", pero si hay varias, buscar la mejor)
        candidatos = []
        for b_id, b_data in self.barrios_db.items():
            b_norm = normalizar_cadena(b_data["nombre"])
            if norm_busqueda in b_norm or b_norm in norm_busqueda:
                candidatos.append(b_data)

        if candidatos:
            # Ordenar por mayor cantidad de avisos (mayor representatividad)
            candidatos.sort(key=lambda x: x["avisos"], reverse=True)
            return candidatos[0]

        # 4. Búsqueda en comunas / macrozonas de DF1
        if slug_busqueda in self.comunas_db:
            return self.comunas_db[slug_busqueda]

        for c_id, c_data in self.comunas_db.items():
            c_norm = normalizar_cadena(c_data["nombre"])
            if norm_busqueda in c_norm or c_norm in norm_busqueda:
                return c_data

        return None

    def estimar_precio(
        self,
        barrio: str,
        habitaciones: int,
        parqueadero: Optional[bool] = None,
        tipo: str = "apartamento",
        estrato: Optional[int] = None,
        area_m2: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calcula la recomendación de canon con base en el método jerárquico documentado,
        retornando valores estadísticos reales, metadatos y limitaciones explícitas.
        """
        if not self._cargado:
            self.cargar_datos()

        limitaciones_comunes = [
            "Los valores corresponden a cánones ofertados en avisos públicos (asking prices), no a contratos cerrados.",
            "El dataset no contiene desglose por área (m²) ni estrato socioeconómico; no se aplican multiplicadores ficticios.",
        ]

        barrio_encontrado = self.buscar_barrio(barrio)
        alcobas_key = min(max(habitaciones, 1), 3)  # 1, 2, o 3 (para 3 o más)

        # ── Nivel 1: Barrio específico encontrado con mediana de alcobas ──
        if barrio_encontrado:
            b_id = barrio_encontrado["barrio_id"]
            b_nombre = barrio_encontrado["nombre"]
            avisos_total = barrio_encontrado["avisos"]
            fuentes = barrio_encontrado["fuentes"]
            fecha_datos = barrio_encontrado.get("fecha_datos", "2026-10-05")

            mediana_alcoba = None
            avisos_alcoba = 0
            if alcobas_key == 1:
                mediana_alcoba = barrio_encontrado["mediana_1"]
                avisos_alcoba = barrio_encontrado["avisos_1"]
            elif alcobas_key == 2:
                mediana_alcoba = barrio_encontrado["mediana_2"]
                avisos_alcoba = barrio_encontrado["avisos_2"]
            else:
                mediana_alcoba = barrio_encontrado["mediana_3mas"]
                avisos_alcoba = barrio_encontrado["avisos_3mas"]

            # Si hay muestra suficiente para esa cantidad de habitaciones (>= 5 avisos)
            if mediana_alcoba is not None and avisos_alcoba >= 5:
                precio_sugerido = float(mediana_alcoba)
                # El dataset publica cuartiles del barrio completo, no por alcobas.
                # Se reportan sin escalarlos y se identifica esa limitación.
                p25_barrio = float(barrio_encontrado["p25"])
                p75_barrio = float(barrio_encontrado["p75"])
                precio_minimo = min(p25_barrio, precio_sugerido)
                precio_maximo = max(p75_barrio, precio_sugerido)
                limitaciones_categoria = list(limitaciones_comunes)
                limitaciones_categoria.append(
                    "La mediana sí está desagregada por alcobas; p25 y p75 corresponden al barrio completo."
                )

                metadatos = {
                    "metodo": "mediana_barrio_por_habitaciones",
                    "barrio_id": b_id,
                    "barrio_nombre": b_nombre,
                    "habitaciones": habitaciones,
                    "avisos_muestra": avisos_alcoba,
                    "fuentes": fuentes,
                    "fecha_datos": fecha_datos,
                    "version_fuente": "Market Datasets 2026.10 (Deduplicados)",
                    "p25": p25_barrio,
                    "mediana": precio_sugerido,
                    "p75": p75_barrio,
                    "con_parqueadero": parqueadero,
                    "mediana_con_parqueadero": barrio_encontrado.get("mediana_con_parqueadero"),
                    "limitaciones": limitaciones_categoria,
                }

                parq_str = ""
                if parqueadero and barrio_encontrado.get("mediana_con_parqueadero"):
                    parq_str = f" Para inmuebles con parqueadero en este sector, la mediana observada es de ${barrio_encontrado['mediana_con_parqueadero']:,.0f} COP."

                analisis = (
                    f"En {b_nombre}, la mediana observada para inmuebles de {habitaciones} "
                    f"habitación(es) es de ${precio_sugerido:,.0f} COP (muestra de {avisos_alcoba} avisos en {fuentes} fuentes al {fecha_datos}). "
                    f"Los percentiles 25 y 75 del barrio completo van desde ${precio_minimo:,.0f} hasta ${precio_maximo:,.0f} COP; no están desglosados por alcobas.{parq_str}"
                )

                return {
                    "precio_sugerido": float(precio_sugerido),
                    "precio_minimo": float(precio_minimo),
                    "precio_maximo": float(precio_maximo),
                    "moneda": "COP",
                    "metadatos_calculo": metadatos,
                    "analisis": analisis,
                }

            # Si la muestra por alcobas es pequeña o nula, usar la mediana general del barrio.
            precio_sugerido = float(barrio_encontrado["mediana"])
            precio_minimo = float(barrio_encontrado["p25"])
            precio_maximo = float(barrio_encontrado["p75"])

            # Si la alcoba es 1 y la general es para promedio de 2-3, ajustar referencialmente
            limitaciones_nivel2 = list(limitaciones_comunes)
            limitaciones_nivel2.append(
                f"Muestra por alcoba insuficiente en el barrio ({avisos_alcoba} avisos para {habitaciones} habs.); "
                "se utiliza la mediana general del barrio."
            )

            metadatos = {
                "metodo": "mediana_general_barrio",
                "barrio_id": b_id,
                "barrio_nombre": b_nombre,
                "habitaciones": habitaciones,
                "avisos_muestra": avisos_total,
                "fuentes": fuentes,
                "fecha_datos": fecha_datos,
                "version_fuente": "Market Datasets 2026.10 (Deduplicados)",
                "p25": precio_minimo,
                "mediana": precio_sugerido,
                "p75": precio_maximo,
                "con_parqueadero": parqueadero,
                "mediana_con_parqueadero": barrio_encontrado.get("mediana_con_parqueadero"),
                "limitaciones": limitaciones_nivel2,
            }

            analisis = (
                f"En {b_nombre}, con base en una muestra de {avisos_total} avisos analizados, "
                f"el canon mediano general es de ${precio_sugerido:,.0f} COP con rango entre "
                f"${precio_minimo:,.0f} y ${precio_maximo:,.0f} COP. "
                f"No hay muestra suficiente específica para {habitaciones} alcoba(s); se toma la referencia global del barrio."
            )

            return {
                "precio_sugerido": float(precio_sugerido),
                "precio_minimo": float(precio_minimo),
                "precio_maximo": float(precio_maximo),
                "moneda": "COP",
                "metadatos_calculo": metadatos,
                "analisis": analisis,
            }

        # ── Nivel 4: Barrio no encontrado en dataset -> Fallback a nivel Ciudad ──
        ciudad_alcoba_data = self.ciudad_por_alcobas.get(alcobas_key)
        fallback_ciudad_general = False
        if ciudad_alcoba_data is None:
            ciudad_alcoba_data = self.ciudad_resumen
            fallback_ciudad_general = True
        if not ciudad_alcoba_data or not ciudad_alcoba_data.get("mediana"):
            raise ValueError("No hay datos de mercado cargados para calcular una referencia de precio.")
        precio_sugerido = float(ciudad_alcoba_data["mediana"])
        # El CSV trae mediana por alcobas a nivel ciudad, pero no sus cuartiles.
        # No se inventa un intervalo; se entrega el punto de referencia y se explica.
        precio_minimo = None
        precio_maximo = None

        limitaciones_ciudad = list(limitaciones_comunes)
        limitaciones_ciudad.append(
            f"El barrio '{barrio}' no cuenta con registros comparables en la muestra de Medellín al 2026-10-05. "
            "Se aplica la referencia global de ciudad por número de habitaciones."
        )
        limitaciones_ciudad.append(
            "Los conteos del resumen de ciudad y de la tabla por alcobas no coinciden; la referencia por alcobas es orientativa."
        )
        if fallback_ciudad_general:
            limitaciones_ciudad.append(
                "No hay mediana de ciudad segmentada por alcobas; se usa la mediana general de Medellín."
            )

        metadatos = {
            "metodo": "referencia_ciudad_por_habitaciones",
            "barrio_id": None,
            "barrio_nombre": barrio,
            "habitaciones": habitaciones,
            "avisos_muestra": int(ciudad_alcoba_data.get("avisos", 0)),
            "fuentes": None,
            "fecha_datos": str(ciudad_alcoba_data.get("fecha_datos", "desconocida")),
            "version_fuente": "Market Datasets 2026.10 (Consolidado Ciudad)",
            "p25": None,
            "mediana": precio_sugerido,
            "p75": None,
            "con_parqueadero": parqueadero,
            "mediana_con_parqueadero": None,
            "limitaciones": limitaciones_ciudad,
        }

        analisis = (
            f"No se encontraron comparables directos para el barrio '{barrio}' en la base de datos de mercado. "
            f"Como referencia general de Medellín para inmuebles de {habitaciones} habitación(es), "
            f"la mediana observada es de ${precio_sugerido:,.0f} COP. El dataset no ofrece cuartiles para este segmento, "
            "por lo que no se presenta un rango estadístico. "
            "Recomendamos verificar con inmuebles vecinos antes de publicar."
        )

        return {
            "precio_sugerido": float(precio_sugerido),
            "precio_minimo": precio_minimo,
            "precio_maximo": precio_maximo,
            "moneda": "COP",
            "metadatos_calculo": metadatos,
            "analisis": analisis,
        }
