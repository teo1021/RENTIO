"""
Extractor de entidades y gestor de diálogo para la recopilación de datos de inmuebles.
"""

import json
import re
import unicodedata
from typing import Any, Dict, List, Optional

from app.config import settings

PALABRAS_A_NUMEROS = {
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
}

AMENIDADES_CATALOGO = [
    ("balcon", "Balcón"),
    ("balcones", "Balcón"),
    ("piscina", "Piscina"),
    ("ascensor", "Ascensor"),
    ("ascensores", "Ascensor"),
    ("vigilancia", "Vigilancia 24/7"),
    ("porteria", "Portería 24/7"),
    ("seguridad", "Seguridad privada"),
    ("gimnasio", "Gimnasio"),
    ("zona infantil", "Zona infantil"),
    ("parque infantil", "Juegos infantiles"),
    ("cocina integral", "Cocina integral"),
    ("gas natural", "Red de gas natural"),
    ("calentador", "Calentador de agua"),
    ("terraza", "Terraza"),
    ("vista panoramica", "Vista panorámica"),
    ("vista a la ciudad", "Vista a la ciudad"),
    ("patio", "Patio"),
    ("zona de ropas", "Zona de ropas"),
    ("closet", "Closets"),
    ("vestier", "Vestier"),
    ("jacuzzi", "Jacuzzi"),
    ("sauna", "Sauna / Turco"),
    ("salon comunal", "Salón social"),
    ("salon social", "Salón social"),
    ("cancha", "Cancha deportiva"),
    ("zonas verdes", "Zonas verdes"),
    ("parqueadero visitantes", "Parqueadero de visitantes"),
]


def normalizar_texto(texto: str) -> str:
    """Quita acentos y pasa a minúsculas."""
    if not texto:
        return ""
    texto = texto.lower()
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")


class ExtractorInmueble:
    """Extrae atributos normalizados a partir de texto en lenguaje natural."""

    def __init__(self, recomendador=None):
        self.recomendador = recomendador

    def extraer(self, texto: str, datos_previos: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extrae características del mensaje actual."""
        extraidos: Dict[str, Any] = {}
        t_norm = normalizar_texto(texto)

        # El modelo solo extrae lo declarado explícitamente; la validación y
        # la política de campos faltantes siguen siendo deterministas.
        extraidos.update(self._extraer_con_modelo(texto, datos_previos or {}))

        # ── 1. Tipo de inmueble ──────────────────────────────────────────────
        if "apartaestudio" in t_norm:
            extraidos["tipo"] = "apartamento"
            if "habitaciones" not in (datos_previos or {}):
                extraidos["habitaciones"] = 1
        elif "apartamento" in t_norm or "apto" in t_norm:
            extraidos["tipo"] = "apartamento"
        elif "casa" in t_norm:
            extraidos["tipo"] = "casa"
        elif "habitacion" in t_norm or "cuarto solo" in t_norm or "pieza" in t_norm:
            extraidos["tipo"] = "habitacion"
        elif "finca" in t_norm:
            extraidos["tipo"] = "finca"

        # ── 2. Habitaciones / Alcobas ────────────────────────────────────────
        # Buscar patrones tipo "3 habitaciones", "dos alcobas", "1 cuarto"
        patron_hab = re.search(
            r"(\b\d+\b|un|uno|una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s*(?:habitaci[oó]n(?:es)?|alcoba(?:s)?|cuarto(?:s)?|dormitorio(?:s)?|pieza(?:s)?)",
            t_norm,
        )
        if patron_hab:
            val = patron_hab.group(1)
            extraidos["habitaciones"] = PALABRAS_A_NUMEROS.get(val, int(val) if val.isdigit() else 1)
        elif "monoambiente" in t_norm or "apartaestudio" in t_norm:
            extraidos["habitaciones"] = 1

        # ── 3. Baños ────────────────────────────────────────────────────────
        patron_banos = re.search(
            r"(\b\d+\b|un|uno|una|dos|tres|cuatro|cinco|seis)\s*(?:ba[nñ]o(?:s)?)",
            t_norm,
        )
        if patron_banos:
            val = patron_banos.group(1)
            extraidos["banos"] = PALABRAS_A_NUMEROS.get(val, int(val) if val.isdigit() else 1)

        # ── 4. Estrato ──────────────────────────────────────────────────────
        patron_estrato = re.search(r"estrato\s*([1-6])\b", t_norm)
        if patron_estrato:
            extraidos["estrato"] = int(patron_estrato.group(1))

        # ── 5. Área m2 ──────────────────────────────────────────────────────
        patron_area = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:m2|metros|m²|mts2|mts)\b", t_norm)
        if patron_area:
            area_val = float(patron_area.group(1).replace(",", "."))
            if 10 <= area_val <= 1000:
                extraidos["area_m2"] = area_val

        # ── 6. Parqueadero ──────────────────────────────────────────────────
        if re.search(r"(sin|no\s+tiene)\s+(parqueadero|garaje|cochera)", t_norm):
            extraidos["parqueadero"] = False
        elif re.search(r"(con\s+parqueadero|incluye\s+parqueadero|tiene\s+parqueadero|parqueadero\s+privado|garaje|parqueadero)", t_norm):
            extraidos["parqueadero"] = True

        # ── 7. Barrio / Ubicación ────────────────────────────────────────────
        # Si el recomendador está disponible, buscar coincidencias de nombres conocidos
        barrio_encontrado = None
        if self.recomendador:
            # Buscar en patrones "en <barrio>", "ubicado en <barrio>", "sector <barrio>"
            patron_en = re.findall(r"(?:en|barrio|sector|ubicado en|zona)\s+([a-záéíóúñ\s]{3,30})", t_norm)
            for candidato in patron_en:
                candidato_limpio = candidato.split(",")[0].split(".")[0].strip()
                # Cortar palabras de enlace comunes
                candidato_limpio = re.split(r"\b(con|tiene|de|para|estrato|cerca)\b", candidato_limpio)[0].strip()
                match = self.recomendador.buscar_barrio(candidato_limpio)
                if match:
                    barrio_encontrado = match["nombre"]
                    break

            # Si aún no se encontró, buscar directamente nombres de barrios en el texto completo
            if not barrio_encontrado:
                # Comprobar barrios populares primero
                barrios_populares = [
                    "el poblado", "poblado", "laureles", "conquistadores", "estadio",
                    "castropol", "el tesoro", "san lucas", "patio bonito", "ciudad del rio",
                    "los balsos", "altos del poblado", "calasanz", "belen", "san joaquin",
                    "floresta", "robledo", "boston", "prado", "san diego", "guayabal",
                    "envigado", "sabaneta", "itagui", "la america", "buenos aires",
                ]
                for bp in barrios_populares:
                    if re.search(r"\b" + re.escape(bp) + r"\b", t_norm):
                        match = self.recomendador.buscar_barrio(bp)
                        if match:
                            barrio_encontrado = match["nombre"]
                            break

        if barrio_encontrado:
            extraidos["barrio"] = barrio_encontrado

        # ── 8. Características / Amenidades ─────────────────────────────────
        caracs_detectadas = []
        for kw, nombre_formal in AMENIDADES_CATALOGO:
            if re.search(r"\b" + re.escape(kw) + r"\b", t_norm):
                if nombre_formal not in caracs_detectadas:
                    caracs_detectadas.append(nombre_formal)

        if caracs_detectadas:
            extraidos["caracteristicas"] = caracs_detectadas

        return extraidos

    @staticmethod
    def _extraer_con_modelo(texto: str, datos_previos: Dict[str, Any]) -> Dict[str, Any]:
        if settings.AI_PROVIDER != "openai" or not settings.AI_API_KEY:
            return {}
        try:
            from openai import OpenAI

            cliente = OpenAI(api_key=settings.AI_API_KEY)
            respuesta = cliente.chat.completions.create(
                model=settings.AI_MODEL,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extrae únicamente características inmobiliarias que el usuario haya dicho "
                            "explícitamente. No infieras ni completes valores desconocidos. Devuelve JSON "
                            "con las claves tipo, barrio, habitaciones, banos, area_m2, estrato, "
                            "parqueadero y caracteristicas. Omite las claves no mencionadas. "
                            "tipo debe ser casa, apartamento, habitacion o finca."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps({"mensaje": texto, "datos_previos": datos_previos}, ensure_ascii=False),
                    },
                ],
            )
            data = json.loads(respuesta.choices[0].message.content or "{}")
            permitidos = {"tipo", "barrio", "habitaciones", "banos", "area_m2", "estrato", "parqueadero", "caracteristicas"}
            return {k: v for k, v in data.items() if k in permitidos and v is not None}
        except Exception:
            return {}

    @staticmethod
    def combinar_y_validar(datos_previos: Dict[str, Any], datos_nuevos: Dict[str, Any]) -> Dict[str, Any]:
        """Combina datos previos con datos nuevos preservando y deduplicando características."""
        resultado = dict(datos_previos or {})

        for clave, valor in datos_nuevos.items():
            if clave == "caracteristicas":
                previas = resultado.get("caracteristicas", [])
                nuevas = list(previas)
                for item in valor:
                    if item not in nuevas:
                        nuevas.append(item)
                resultado["caracteristicas"] = nuevas
            elif valor is not None:
                resultado[clave] = valor

        # Validaciones de integridad
        if "habitaciones" in resultado:
            try:
                h = int(resultado["habitaciones"])
                if not 1 <= h <= 20:
                    raise ValueError
                resultado["habitaciones"] = h
            except (ValueError, TypeError):
                resultado.pop("habitaciones", None)

        if "banos" in resultado:
            try:
                b = int(resultado["banos"])
                if not 1 <= b <= 20:
                    raise ValueError
                resultado["banos"] = b
            except (ValueError, TypeError):
                resultado.pop("banos", None)

        if "estrato" in resultado:
            try:
                e = int(resultado["estrato"])
                if not 1 <= e <= 6:
                    raise ValueError
                resultado["estrato"] = e
            except (ValueError, TypeError):
                resultado.pop("estrato", None)

        if "area_m2" in resultado:
            try:
                a = float(resultado["area_m2"])
                if not 10 <= a <= 1000:
                    raise ValueError
                resultado["area_m2"] = round(a, 2)
            except (ValueError, TypeError):
                resultado.pop("area_m2", None)

        if resultado.get("tipo") not in {"casa", "apartamento", "habitacion", "finca"}:
            resultado.pop("tipo", None)
        if not isinstance(resultado.get("barrio"), str) or not resultado.get("barrio", "").strip():
            resultado.pop("barrio", None)
        if "parqueadero" in resultado and not isinstance(resultado["parqueadero"], bool):
            resultado.pop("parqueadero", None)
        if not isinstance(resultado.get("caracteristicas", []), list):
            resultado.pop("caracteristicas", None)
        else:
            resultado["caracteristicas"] = [
                c.strip() for c in resultado.get("caracteristicas", [])
                if isinstance(c, str) and c.strip()
            ]

        return resultado

    @staticmethod
    def obtener_campos_faltantes(datos: Dict[str, Any]) -> List[str]:
        """
        Determina qué campos obligatorios aún no han sido provistos.
        Campos esenciales para descripción y estimación:
        - barrio
        - tipo
        - habitaciones
        - banos
        """
        faltantes = []
        if not datos.get("barrio"):
            faltantes.append("barrio")
        if not datos.get("tipo"):
            faltantes.append("tipo")
        if not datos.get("habitaciones"):
            faltantes.append("habitaciones")
        if not datos.get("banos"):
            faltantes.append("banos")
        return faltantes

    @staticmethod
    def construir_respuesta_asistente(
        datos_actualizados: Dict[str, Any],
        datos_nuevos: Dict[str, Any],
        faltantes: List[str],
        es_completo: bool,
    ) -> str:
        """
        Genera la respuesta del asistente en lenguaje natural, guiando al
        propietario paso a paso y solicitando exclusivamente los datos que faltan.
        """
        # Resumen de lo que se ha reconocido
        partes_reconocidas = []
        if datos_actualizados.get("barrio"):
            partes_reconocidas.append(f"ubicado en **{datos_actualizados['barrio']}**")
        if datos_actualizados.get("tipo"):
            partes_reconocidas.append(f"tipo **{datos_actualizados['tipo']}**")
        if datos_actualizados.get("habitaciones"):
            partes_reconocidas.append(f"con **{datos_actualizados['habitaciones']} habitación(es)**")
        if datos_actualizados.get("banos"):
            partes_reconocidas.append(f"**{datos_actualizados['banos']} baño(s)**")
        if datos_actualizados.get("area_m2"):
            partes_reconocidas.append(f"**{datos_actualizados['area_m2']} m²**")
        if datos_actualizados.get("parqueadero") is True:
            partes_reconocidas.append("con **parqueadero**")
        elif datos_actualizados.get("parqueadero") is False:
            partes_reconocidas.append("sin parqueadero")
        if datos_actualizados.get("estrato"):
            partes_reconocidas.append(f"estrato **{datos_actualizados['estrato']}**")
        if datos_actualizados.get("caracteristicas"):
            caracs_str = ", ".join(datos_actualizados["caracteristicas"])
            partes_reconocidas.append(f"amenidades ({caracs_str})")

        reconocido_texto = ""
        if partes_reconocidas:
            reconocido_texto = "¡Perfecto! Ya registré los siguientes detalles de tu inmueble: " + "; ".join(partes_reconocidas) + ".\n\n"

        if es_completo:
            return (
                f"{reconocido_texto}"
                " ¡Tenemos toda la información necesaria! "
                "A continuación he generado la descripción comercial optimizada para publicación "
                "y la recomendación de canon mensual basada en las medianas y percentiles de avisos de arriendo en tu zona. "
                "Por favor revísala y confírmame si deseas aprobarla para tu propiedad."
            )

        # Mapeo de preguntas específicas según qué campos faltan
        preguntas_faltantes = []
        if "barrio" in faltantes:
            preguntas_faltantes.append("¿En qué **barrio o sector de Medellín** se encuentra ubicado?")
        if "tipo" in faltantes:
            preguntas_faltantes.append("¿Qué **tipo de inmueble** es (apartamento, casa, apartaestudio, etc.)?")
        if "habitaciones" in faltantes:
            preguntas_faltantes.append("¿Cuántas **habitaciones o alcobas** tiene?")
        if "banos" in faltantes:
            preguntas_faltantes.append("¿Cuántos **baños** tiene?")

        preguntas_formateadas = "\n".join(f"- {p}" for p in preguntas_faltantes)

        opcional_tip = ""
        if not datos_actualizados.get("parqueadero") and "parqueadero" not in faltantes:
            opcional_tip = "\n*(Opcional: Si cuenta con parqueadero, área en m² o amenidades específicas, menciónalas también para precisar la estimación)*."

        return (
            f"{reconocido_texto}"
            "Para poder generar la descripción comercial y calcular la recomendación precisa de canon según el mercado, "
            f"aún necesito que me indiques:\n{preguntas_formateadas}{opcional_tip}"
        )
