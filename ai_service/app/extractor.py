
"""
Extractor de entidades y gestor de dialogo para la recopilacion de datos de inmuebles.
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
    ("balcon", "BalcÃ³n"),
    ("balcones", "BalcÃ³n"),
    ("piscina", "Piscina"),
    ("ascensor", "Ascensor"),
    ("ascensores", "Ascensor"),
    ("vigilancia", "Vigilancia 24/7"),
    ("porteria", "PorterÃ­a 24/7"),
    ("seguridad", "Seguridad privada"),
    ("gimnasio", "Gimnasio"),
    ("zona infantil", "Zona infantil"),
    ("parque infantil", "Juegos infantiles"),
    ("cocina integral", "Cocina integral"),
    ("gas natural", "Red de gas natural"),
    ("calentador", "Calentador de agua"),
    ("terraza", "Terraza"),
    ("vista panoramica", "Vista panorÃ¡mica"),
    ("vista a la ciudad", "Vista a la ciudad"),
    ("patio", "Patio"),
    ("zona de ropas", "Zona de ropas"),
    ("closet", "Closets"),
    ("vestier", "Vestier"),
    ("jacuzzi", "Jacuzzi"),
    ("sauna", "Sauna / Turco"),
    ("salon comunal", "SalÃ³n social"),
    ("salon social", "SalÃ³n social"),
    ("cancha", "Cancha deportiva"),
    ("zonas verdes", "Zonas verdes"),
    ("parqueadero visitantes", "Parqueadero de visitantes"),
]


def normalizar_texto(texto: str) -> str:
    """Quita acentos y pasa el texto a minusculas."""
    if not texto:
        return ""

    texto = texto.lower()
    return unicodedata.normalize("NFKD", texto).encode(
        "ASCII", "ignore"
    ).decode("utf-8")


class ExtractorInmueble:
    """Extrae atributos normalizados a partir de texto en lenguaje natural."""

    def __init__(self, recomendador=None):
        self.recomendador = recomendador

    def extraer(
        self,
        texto: str,
        datos_previos: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        extraidos: Dict[str, Any] = {}
        t_norm = normalizar_texto(texto)

        # Extraccion mediante el modelo de IA, si esta configurado.
        extraidos.update(
            self._extraer_con_modelo(texto, datos_previos or {})
        )

        # 1. Direccion del inmueble.
        direccion = self._extraer_direccion(texto)

        if direccion:
            extraidos["direccion"] = direccion

        # 2. Tipo de inmueble.
        if "apartaestudio" in t_norm:
            extraidos["tipo"] = "apartamento"

            if "habitaciones" not in (datos_previos or {}):
                extraidos["habitaciones"] = 1

        elif "apartamento" in t_norm or "apto" in t_norm:
            extraidos["tipo"] = "apartamento"

        elif "casa" in t_norm:
            extraidos["tipo"] = "casa"

        elif (
            "habitacion" in t_norm
            or "cuarto solo" in t_norm
            or "pieza" in t_norm
        ):
            extraidos["tipo"] = "habitacion"

        elif "finca" in t_norm:
            extraidos["tipo"] = "finca"

        # 3. Habitaciones.
        patron_hab = re.search(
            r"(\b\d+\b|un|uno|una|dos|tres|cuatro|cinco|"
            r"seis|siete|ocho|nueve|diez)\s*"
            r"(?:habitaciones?|alcobas?|cuartos?|dormitorios?|piezas?)",
            t_norm,
        )

        if patron_hab:
            valor = patron_hab.group(1)
            extraidos["habitaciones"] = PALABRAS_A_NUMEROS.get(
                valor,
                int(valor) if valor.isdigit() else 1
            )

        elif "monoambiente" in t_norm or "apartaestudio" in t_norm:
            extraidos["habitaciones"] = 1

        # 4. BaÃ±os.
        patron_banos = re.search(
            r"(\b\d+\b|un|uno|una|dos|tres|cuatro|cinco|seis)\s*"
            r"banos?",
            t_norm,
        )

        if patron_banos:
            valor = patron_banos.group(1)
            extraidos["banos"] = PALABRAS_A_NUMEROS.get(
                valor,
                int(valor) if valor.isdigit() else 1
            )

        # 5. Estrato.
        patron_estrato = re.search(
            r"estrato\s*([1-6])\b",
            t_norm
        )

        if patron_estrato:
            extraidos["estrato"] = int(patron_estrato.group(1))

        # 6. Area en metros cuadrados.
        patron_area = re.search(
            r"(\d+(?:[.,]\d+)?)\s*"
            r"(?:m2|metros(?: cuadrados)?|mÂ²|mts2|mts)\b",
            t_norm,
        )

        if patron_area:
            area_valor = float(
                patron_area.group(1).replace(",", ".")
            )

            if 10 <= area_valor <= 1000:
                extraidos["area_m2"] = area_valor

        # 7. Parqueadero.
        if re.search(
            r"(sin|no\s+tiene)\s+(parqueadero|garaje|cochera)",
            t_norm
        ):
            extraidos["parqueadero"] = False

        elif re.search(
            r"(con\s+parqueadero|incluye\s+parqueadero|"
            r"tiene\s+parqueadero|parqueadero\s+privado|"
            r"garaje|parqueadero)",
            t_norm
        ):
            extraidos["parqueadero"] = True

        # 8. Barrio.
        barrio_encontrado = None

        if self.recomendador:
            patron_en = re.findall(
                r"(?:en|barrio|sector|ubicado en|zona)\s+"
                r"([a-z\s]{3,30})",
                t_norm
            )

            for candidato in patron_en:
                candidato_limpio = (
                    candidato.split(",")[0]
                    .split(".")[0]
                    .strip()
                )

                candidato_limpio = re.split(
                    r"\b(con|tiene|de|para|estrato|cerca)\b",
                    candidato_limpio
                )[0].strip()

                coincidencia = self.recomendador.buscar_barrio(
                    candidato_limpio
                )

                if coincidencia:
                    barrio_encontrado = coincidencia["nombre"]
                    break

            if not barrio_encontrado:
                barrios_populares = [
                    "el poblado",
                    "poblado",
                    "laureles",
                    "conquistadores",
                    "estadio",
                    "castropol",
                    "el tesoro",
                    "san lucas",
                    "patio bonito",
                    "ciudad del rio",
                    "los balsos",
                    "altos del poblado",
                    "calasanz",
                    "belen",
                    "san joaquin",
                    "floresta",
                    "robledo",
                    "boston",
                    "prado",
                    "san diego",
                    "guayabal",
                    "envigado",
                    "sabaneta",
                    "itagui",
                    "la america",
                    "buenos aires",
                ]

                for barrio in barrios_populares:
                    if re.search(
                        r"\b" + re.escape(barrio) + r"\b",
                        t_norm
                    ):
                        coincidencia = self.recomendador.buscar_barrio(
                            barrio
                        )

                        if coincidencia:
                            barrio_encontrado = coincidencia["nombre"]
                            break

        if barrio_encontrado:
            extraidos["barrio"] = barrio_encontrado

        # 9. Caracteristicas y amenidades.
        caracteristicas_detectadas = []

        for palabra, nombre_formal in AMENIDADES_CATALOGO:
            if re.search(
                r"\b" + re.escape(palabra) + r"\b",
                t_norm
            ):
                if nombre_formal not in caracteristicas_detectadas:
                    caracteristicas_detectadas.append(nombre_formal)

        if caracteristicas_detectadas:
            extraidos["caracteristicas"] = caracteristicas_detectadas

        return extraidos

    @staticmethod
    def _extraer_direccion(texto: str) -> Optional[str]:
        """Busca direcciones inmobiliarias escritas por el usuario."""

        patron = re.search(
            r"\b(?:direcci[oó]n|ubicaci[oó]n exacta|nomenclatura)\s*"
            r"(?:es|:|-)?\s*"
            r"((?:calle|cl|carrera|cra|cr|avenida|av|"
            r"transversal|tv|diagonal|dg)\s*"
            r"[\w\s#.-]{2,35})",
            texto,
            re.IGNORECASE
        )

        if not patron:
            return None

        direccion = patron.group(1)

        # Evitar que la direccion capture otros datos del mensaje.
        direccion = re.split(
            r"[,;\n]|\b(?:estrato|barrio|habitaciones?|"
            r"alcobas?|banos?|area|metros|con|sin)\b",
            direccion,
            flags=re.IGNORECASE
        )[0]

        direccion = direccion.strip(" .,:;-")

        # Una direccion debe contener al menos un numero.
        if not re.search(r"\d", direccion):
            return None

        return direccion

    @staticmethod
    def _extraer_con_modelo(
        texto: str,
        datos_previos: Dict[str, Any]
    ) -> Dict[str, Any]:

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
                            "Extrae unicamente caracteristicas inmobiliarias "
                            "que el usuario haya dicho explicitamente. "
                            "No infieras ni completes valores desconocidos. "
                            "Devuelve JSON con las claves tipo, barrio, "
                            "habitaciones, banos, area_m2, estrato, "
                            "direccion, parqueadero y caracteristicas. "
                            "Omite las claves no mencionadas. "
                            "tipo debe ser casa, apartamento, habitacion o finca. "
                            "La direccion debe conservar la nomenclatura "
                            "escrita por el usuario."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "mensaje": texto,
                                "datos_previos": datos_previos
                            },
                            ensure_ascii=False
                        ),
                    },
                ],
            )

            datos = json.loads(
                respuesta.choices[0].message.content or "{}"
            )

            permitidos = {
                "tipo",
                "barrio",
                "habitaciones",
                "banos",
                "area_m2",
                "estrato",
                "direccion",
                "parqueadero",
                "caracteristicas",
            }

            return {
                clave: valor
                for clave, valor in datos.items()
                if clave in permitidos and valor is not None
            }

        except Exception:
            return {}

    @staticmethod
    def combinar_y_validar(
        datos_previos: Dict[str, Any],
        datos_nuevos: Dict[str, Any]
    ) -> Dict[str, Any]:

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

        # Validar habitaciones.
        if "habitaciones" in resultado:
            try:
                habitaciones = int(resultado["habitaciones"])

                if not 1 <= habitaciones <= 20:
                    raise ValueError

                resultado["habitaciones"] = habitaciones

            except (ValueError, TypeError):
                resultado.pop("habitaciones", None)

        # Validar baÃ±os.
        if "banos" in resultado:
            try:
                banos = int(resultado["banos"])

                if not 1 <= banos <= 20:
                    raise ValueError

                resultado["banos"] = banos

            except (ValueError, TypeError):
                resultado.pop("banos", None)

        # Validar estrato.
        if "estrato" in resultado:
            try:
                estrato = int(resultado["estrato"])

                if not 1 <= estrato <= 6:
                    raise ValueError

                resultado["estrato"] = estrato

            except (ValueError, TypeError):
                resultado.pop("estrato", None)

        # Validar area.
        if "area_m2" in resultado:
            try:
                area = float(resultado["area_m2"])

                if not 10 <= area <= 1000:
                    raise ValueError

                resultado["area_m2"] = round(area, 2)

            except (ValueError, TypeError):
                resultado.pop("area_m2", None)

        # Validar tipo.
        if resultado.get("tipo") not in {
            "casa",
            "apartamento",
            "habitacion",
            "finca"
        }:
            resultado.pop("tipo", None)

        # Validar barrio.
        if (
            not isinstance(resultado.get("barrio"), str)
            or not resultado.get("barrio", "").strip()
        ):
            resultado.pop("barrio", None)

        # Validar direccion.
        if (
            not isinstance(resultado.get("direccion"), str)
            or not resultado.get("direccion", "").strip()
        ):
            resultado.pop("direccion", None)

        # Validar parqueadero.
        if (
            "parqueadero" in resultado
            and not isinstance(resultado["parqueadero"], bool)
        ):
            resultado.pop("parqueadero", None)

        # Validar caracteristicas.
        if not isinstance(resultado.get("caracteristicas", []), list):
            resultado.pop("caracteristicas", None)

        else:
            resultado["caracteristicas"] = [
                caracteristica.strip()
                for caracteristica in resultado.get("caracteristicas", [])
                if isinstance(caracteristica, str)
                and caracteristica.strip()
            ]

        return resultado

    @staticmethod
    def obtener_campos_faltantes(datos: Dict[str, Any]) -> List[str]:
        """Determina los datos obligatorios que aun faltan."""

        faltantes = []

        if not datos.get("barrio"):
            faltantes.append("barrio")

        if not datos.get("tipo"):
            faltantes.append("tipo")

        if not datos.get("habitaciones"):
            faltantes.append("habitaciones")

        if not datos.get("banos"):
            faltantes.append("banos")

        if not datos.get("direccion"):
            faltantes.append("direccion")

        if not datos.get("estrato"):
            faltantes.append("estrato")

        return faltantes

    @staticmethod
    def construir_respuesta_asistente(
        datos_actualizados: Dict[str, Any],
        datos_nuevos: Dict[str, Any],
        faltantes: List[str],
        es_completo: bool,
    ) -> str:

        partes_reconocidas = []

        if datos_actualizados.get("barrio"):
            partes_reconocidas.append(
                f"ubicado en **{datos_actualizados['barrio']}**"
            )

        if datos_actualizados.get("direccion"):
            partes_reconocidas.append(
                f"direcciÃ³n **{datos_actualizados['direccion']}**"
            )

        if datos_actualizados.get("tipo"):
            partes_reconocidas.append(
                f"tipo **{datos_actualizados['tipo']}**"
            )

        if datos_actualizados.get("habitaciones"):
            partes_reconocidas.append(
                f"con **{datos_actualizados['habitaciones']} habitaciÃ³n(es)**"
            )

        if datos_actualizados.get("banos"):
            partes_reconocidas.append(
                f"**{datos_actualizados['banos']} baÃ±o(s)**"
            )

        if datos_actualizados.get("area_m2"):
            partes_reconocidas.append(
                f"**{datos_actualizados['area_m2']} mÂ²**"
            )

        if datos_actualizados.get("parqueadero") is True:
            partes_reconocidas.append("con **parqueadero**")

        elif datos_actualizados.get("parqueadero") is False:
            partes_reconocidas.append("sin parqueadero")

        if datos_actualizados.get("estrato"):
            partes_reconocidas.append(
                f"estrato **{datos_actualizados['estrato']}**"
            )

        if datos_actualizados.get("caracteristicas"):
            caracteristicas = ", ".join(
                datos_actualizados["caracteristicas"]
            )

            partes_reconocidas.append(
                f"amenidades ({caracteristicas})"
            )

        reconocido_texto = ""

        if partes_reconocidas:
            reconocido_texto = (
                "Â¡Perfecto! Ya registrÃ© los siguientes detalles "
                "de tu inmueble: "
                + "; ".join(partes_reconocidas)
                + ".\n\n"
            )

        if es_completo:
            return (
                f"{reconocido_texto}"
                "Â¡Tenemos toda la informaciÃ³n necesaria! "
                "A continuaciÃ³n he generado una descripciÃ³n comercial "
                "y una recomendaciÃ³n de canon mensual. "
                "Por favor revisa los resultados antes de confirmar "
                "el registro de tu propiedad."
            )

        preguntas = []

        if "barrio" in faltantes:
            preguntas.append(
                "Â¿En quÃ© **barrio o sector** se encuentra ubicado?"
            )

        if "tipo" in faltantes:
            preguntas.append(
                "Â¿QuÃ© **tipo de inmueble** es "
                "(apartamento, casa, habitaciÃ³n o finca)?"
            )

        if "habitaciones" in faltantes:
            preguntas.append(
                "Â¿CuÃ¡ntas **habitaciones o alcobas** tiene?"
            )

        if "banos" in faltantes:
            preguntas.append(
                "Â¿CuÃ¡ntos **baÃ±os** tiene?"
            )

        if "direccion" in faltantes:
            preguntas.append(
                "Â¿CuÃ¡l es la **direcciÃ³n exacta** del inmueble? "
                "Por ejemplo: Carrera 45 # 12-30."
            )

        if "estrato" in faltantes:
            preguntas.append(
                "Â¿QuÃ© **estrato** tiene la propiedad?"
            )

        preguntas_formateadas = "\n".join(
            f"- {pregunta}" for pregunta in preguntas
        )

        opcional_tip = ""

        if (
            "area_m2" not in datos_actualizados
            or "parqueadero" not in datos_actualizados
        ):
            opcional_tip = (
                "\n\n*(TambiÃ©n puedes indicar el Ã¡rea en metros "
                "cuadrados, si tiene parqueadero y otras amenidades. "
                "Estos datos son opcionales.)*"
            )

        return (
            f"{reconocido_texto}"
            "Para continuar con el registro de tu propiedad, "
            f"aÃºn necesito que me indiques:\n{preguntas_formateadas}"
            f"{opcional_tip}"
        )

