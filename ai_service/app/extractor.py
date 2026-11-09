
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
    """Quita acentos y pasa el texto a minúsculas."""
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
        datos_previos: Optional[Dict[str, Any]] = None,
        historial: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Extrae características del mensaje actual."""

        extraidos: Dict[str, Any] = {}
        datos_previos = datos_previos or {}
        historial = historial or []
        t_norm = normalizar_texto(texto)

        # El modelo solo extrae información declarada explícitamente.
        extraidos.update(
            self._extraer_con_modelo(texto, datos_previos, historial)
        )

        # 1. Tipo de inmueble
        if "apartaestudio" in t_norm:
            extraidos["tipo"] = "apartamento"

            if "habitaciones" not in datos_previos:
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

        # 2. Habitaciones
        patron_hab = re.search(
            r"(\b\d+\b|un|uno|una|dos|tres|cuatro|cinco|seis|"
            r"siete|ocho|nueve|diez)\s*"
            r"(?:habitacion(?:es)?|alcoba(?:s)?|cuarto(?:s)?|"
            r"dormitorio(?:s)?|pieza(?:s)?)",
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

        # 3. Baños
        patron_banos = re.search(
            r"(\b\d+\b|un|uno|una|dos|tres|cuatro|cinco|seis)\s*"
            r"(?:banos?)",
            t_norm,
        )

        if patron_banos:
            valor = patron_banos.group(1)
            extraidos["banos"] = PALABRAS_A_NUMEROS.get(
                valor,
                int(valor) if valor.isdigit() else 1
            )

        # 4. Estrato
        patron_estrato = re.search(
            r"estrato\s*(?:numero\s*)?([1-6])\b",
            t_norm,
        )

        if patron_estrato:
            extraidos["estrato"] = int(patron_estrato.group(1))

        # 5. Área en metros cuadrados
        patron_area = re.search(
            r"(\d+(?:[.,]\d+)?)\s*"
            r"(?:m2|metros(?:\s+cuadrados)?|mts2|mts)\b",
            t_norm,
        )

        if patron_area:
            area_valor = float(
                patron_area.group(1).replace(",", ".")
            )

            if 10 <= area_valor <= 1000:
                extraidos["area_m2"] = area_valor

        precio = self._extraer_precio(texto)
        if precio is not None:
            extraidos["precio_mensual"] = precio

        respuesta_contextual = self._extraer_respuesta_contextual(
            texto,
            historial,
        )
        for campo, valor in respuesta_contextual.items():
            extraidos.setdefault(campo, valor)

        # 6. Parqueadero
        if re.search(
            r"(sin|no\s+tiene|no\s+cuenta\s+con)\s+"
            r"(parqueadero|garaje|cochera)",
            t_norm,
        ):
            extraidos["parqueadero"] = False

        elif re.search(
            r"(con\s+parqueadero|incluye\s+parqueadero|"
            r"tiene\s+parqueadero|parqueadero\s+privado|"
            r"garaje|parqueadero)",
            t_norm,
        ):
            extraidos["parqueadero"] = True

        # 7. Dirección exacta
        direccion = self._extraer_direccion(texto)

        if direccion:
            extraidos["direccion"] = direccion

        # 8. Barrio
        barrio_encontrado = None

        if self.recomendador:
            patron_en = re.findall(
                r"(?:en|barrio|sector|ubicado en|zona)\s+"
                r"([a-záéíóúñ\s]{3,30})",
                texto.lower(),
            )

            for candidato in patron_en:
                candidato_limpio = (
                    normalizar_texto(candidato)
                    .split(",")[0]
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

        # 9. Características y amenidades
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
        """
        Extrae una dirección cuando el usuario la identifica explícitamente.
        No intenta inventar una dirección a partir del barrio.
        """

        patron_etiqueta = re.search(
            r"(?:direccion|ubicacion exacta|nomenclatura)"
            r"\s*(?:del inmueble)?\s*(?:es|:|=)?\s*(.+)",
            texto,
            flags=re.IGNORECASE,
        )

        if patron_etiqueta:
            direccion = patron_etiqueta.group(1).strip()

            direccion = re.sub(
                r"[,;]?\s*(?:barrio|sector|estrato)\s+.*$",
                "",
                direccion,
                flags=re.IGNORECASE,
            ).strip()

            direccion = direccion.strip(" .,:;-")

            if len(direccion) >= 5:
                return direccion[:500]

        # También reconoce nomenclaturas escritas directamente,
        # por ejemplo: Cra 45 # 12-30 o Calle 10 # 20-15.
        patron_nomenclatura = re.search(
            r"\b(?:calle|carrera|cra|cr|avenida|av|diagonal|diag|"
            r"transversal|tv)\.?\s*"
            r"\d+[a-zA-Z]?"
            r"(?:\s*#\s*\d+[a-zA-Z]?)?"
            r"(?:\s*-\s*\d+[a-zA-Z]?)?",
            texto,
            flags=re.IGNORECASE,
        )

        if patron_nomenclatura:
            return patron_nomenclatura.group(0).strip()[:500]

        return None

    @staticmethod
    def _extraer_con_modelo(
        texto: str,
        datos_previos: Dict[str, Any],
        historial: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Usa el modelo únicamente para extraer datos explícitos."""

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
                            "Extrae únicamente características inmobiliarias "
                            "que el usuario haya dicho explícitamente. "
                            "No infieras ni completes valores desconocidos. "
                            "Devuelve un JSON con las claves: tipo, barrio, "
                            "habitaciones, banos, area_m2, estrato, precio_mensual, "
                            "direccion, parqueadero y caracteristicas. "
                            "Omite las claves no mencionadas. "
                            "La dirección debe ser la nomenclatura exacta "
                            "si el usuario la proporciona. "
                            "No confundas el barrio con la dirección. "
                            "tipo debe ser casa, apartamento, habitacion "
                            "o finca."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "mensaje": texto,
                                "datos_previos": datos_previos,
                                "historial": historial or [],
                            },
                            ensure_ascii=False,
                        ),
                    },
                ],
            )

            data = json.loads(
                respuesta.choices[0].message.content or "{}"
            )

            permitidos = {
                "tipo",
                "barrio",
                "habitaciones",
                "banos",
                "area_m2",
                "estrato",
                "precio_mensual",
                "direccion",
                "parqueadero",
                "caracteristicas",
            }

            return {
                clave: valor
                for clave, valor in data.items()
                if clave in permitidos and valor is not None
            }

        except Exception as exc:
            raise RuntimeError(
                "No fue posible extraer los datos con el proveedor de IA configurado."
            ) from exc

    @staticmethod
    def _extraer_precio(texto: str) -> Optional[float]:
        texto_normalizado = normalizar_texto(texto)
        patron = re.compile(
            r"(?P<simbolo>\$\s*)?"
            r"(?P<cifra>\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{1,2})?"
            r"|\d+(?:[.,]\d+)?|un|uno|una|dos|tres|cuatro|cinco|"
            r"seis|siete|ocho|nueve|diez)"
            r"\s*(?P<unidad>millones?|millon|mil)?"
            r"\s*(?P<moneda>pesos?|cop)?",
            re.IGNORECASE,
        )
        menciones_precio = [
            match.start()
            for match in re.finditer(
                r"\b(?:canon|arriendo|arrendar|alquiler|precio|renta|"
                r"cobro|pido|cuesta|vale|mensual|al mes)\b",
                texto_normalizado,
            )
        ]
        candidatos = []
        for match in patron.finditer(texto_normalizado):
            prefijo = texto_normalizado[max(0, match.start() - 45):match.start()]
            sufijo = texto_normalizado[match.end():match.end() + 24]
            unidad = (match.group("unidad") or "").lower()
            moneda_explicita = bool(
                match.group("simbolo")
                or match.group("moneda")
                or unidad
            )
            distancia_pista = min(
                (
                    min(abs(match.start() - posicion), abs(match.end() - posicion))
                    for posicion in menciones_precio
                ),
                default=10_000,
            )
            pista_cercana = distancia_pista <= 35 or any(
                pista in sufijo for pista in ("mensual", "al mes")
            )
            if not moneda_explicita and not pista_cercana:
                continue

            cifra = match.group("cifra").lower()
            if cifra in PALABRAS_A_NUMEROS:
                valor = float(PALABRAS_A_NUMEROS[cifra])
            else:
                cifra = re.sub(r"\s+", "", cifra)
                if "." in cifra and "," in cifra:
                    separador_decimal = max(cifra.rfind("."), cifra.rfind(","))
                    parte_entera = re.sub(r"[.,]", "", cifra[:separador_decimal])
                    parte_decimal = cifra[separador_decimal + 1:]
                    cifra = f"{parte_entera}.{parte_decimal}"
                elif "." in cifra or "," in cifra:
                    separador = "." if "." in cifra else ","
                    partes = cifra.split(separador)
                    if len(partes) > 2 or len(partes[-1]) == 3:
                        cifra = "".join(partes)
                    else:
                        cifra = f"{partes[0]}.{partes[1]}"
                try:
                    valor = float(cifra)
                except ValueError:
                    continue

            if unidad.startswith("millon"):
                valor *= 1_000_000
            elif unidad == "mil":
                valor *= 1_000
            elif valor < 100_000:
                continue

            if 100_000 <= valor <= 99_999_999:
                candidatos.append(
                    (moneda_explicita, distancia_pista, match.start(), round(valor, 2))
                )

        if not candidatos:
            return None
        mejor = max(candidatos, key=lambda candidato: (
            candidato[0],
            -candidato[1],
            candidato[2],
        ))
        return mejor[3]

    @staticmethod
    def _extraer_respuesta_contextual(
        texto: str,
        historial: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        contenido = texto.strip()
        if not re.fullmatch(
            r"\d{1,3}(?:[.,\s]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d+)?",
            contenido,
        ):
            return {}
        pregunta = next(
            (
                normalizar_texto(mensaje.get("contenido", ""))
                for mensaje in reversed(historial)
                if mensaje.get("rol") == "asistente"
            ),
            "",
        )
        if any(palabra in pregunta for palabra in ("canon", "precio", "arriendo")):
            precio = ExtractorInmueble._extraer_precio(
                f"canon de {contenido}"
            )
            return {"precio_mensual": precio} if precio is not None else {}
        try:
            valor = float(contenido.replace(",", "."))
        except ValueError:
            return {}
        if any(palabra in pregunta for palabra in ("area", "metros cuadrados")):
            return {"area_m2": valor} if 10 <= valor <= 1000 else {}
        if "estrato" in pregunta:
            return {"estrato": int(valor)} if valor.is_integer() and 1 <= valor <= 6 else {}
        if any(palabra in pregunta for palabra in ("habitacion", "alcoba")):
            return {"habitaciones": int(valor)} if valor.is_integer() and 1 <= valor <= 20 else {}
        if "bano" in pregunta:
            return {"banos": int(valor)} if valor.is_integer() and 1 <= valor <= 20 else {}
        return {}

    @staticmethod
    def combinar_y_validar(
        datos_previos: Dict[str, Any],
        datos_nuevos: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combina datos previos con nuevos y valida sus valores."""

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

        # Habitaciones
        if "habitaciones" in resultado:
            try:
                habitaciones = int(resultado["habitaciones"])

                if not 1 <= habitaciones <= 20:
                    raise ValueError

                resultado["habitaciones"] = habitaciones

            except (ValueError, TypeError):
                resultado.pop("habitaciones", None)

        # Baños
        if "banos" in resultado:
            try:
                banos = int(resultado["banos"])

                if not 1 <= banos <= 20:
                    raise ValueError

                resultado["banos"] = banos

            except (ValueError, TypeError):
                resultado.pop("banos", None)

        # Estrato
        if "estrato" in resultado:
            try:
                estrato = int(resultado["estrato"])

                if not 1 <= estrato <= 6:
                    raise ValueError

                resultado["estrato"] = estrato

            except (ValueError, TypeError):
                resultado.pop("estrato", None)

        # Área
        if "area_m2" in resultado:
            try:
                area = float(resultado["area_m2"])

                if not 10 <= area <= 1000:
                    raise ValueError

                resultado["area_m2"] = round(area, 2)

            except (ValueError, TypeError):
                resultado.pop("area_m2", None)

        # Canon mensual
        if "precio_mensual" in resultado:
            try:
                precio = float(resultado["precio_mensual"])
                if not 100_000 <= precio <= 99_999_999:
                    raise ValueError
                resultado["precio_mensual"] = round(precio, 2)
            except (ValueError, TypeError):
                resultado.pop("precio_mensual", None)

        # Tipo
        if resultado.get("tipo") not in {
            "casa",
            "apartamento",
            "habitacion",
            "finca",
        }:
            resultado.pop("tipo", None)

        # Barrio
        if (
            not isinstance(resultado.get("barrio"), str)
            or not resultado.get("barrio", "").strip()
        ):
            resultado.pop("barrio", None)

        # Dirección
        if "direccion" in resultado:
            if not isinstance(resultado["direccion"], str):
                resultado.pop("direccion", None)
            else:
                direccion = resultado["direccion"].strip()

                if len(direccion) < 5 or len(direccion) > 500:
                    resultado.pop("direccion", None)
                else:
                    resultado["direccion"] = direccion

        # Parqueadero
        if (
            "parqueadero" in resultado
            and not isinstance(resultado["parqueadero"], bool)
        ):
            resultado.pop("parqueadero", None)

        # Características
        if not isinstance(resultado.get("caracteristicas", []), list):
            resultado.pop("caracteristicas", None)
        else:
            resultado["caracteristicas"] = [
                caracteristica.strip()
                for caracteristica in resultado.get(
                    "caracteristicas", []
                )
                if isinstance(caracteristica, str)
                and caracteristica.strip()
            ]

        return resultado

    @staticmethod
    def obtener_campos_faltantes(
        datos: Dict[str, Any]
    ) -> List[str]:
        """
        Determina los datos obligatorios para registrar una propiedad.

        Se requieren:
        - barrio
        - tipo
        - habitaciones
        - banos
        - direccion
        - estrato
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

        if not datos.get("direccion"):
            faltantes.append("direccion")

        if not datos.get("estrato"):
            faltantes.append("estrato")

        if not datos.get("precio_mensual"):
            faltantes.append("precio_mensual")

        return faltantes

    @staticmethod
    def construir_respuesta_asistente(
        datos_actualizados: Dict[str, Any],
        datos_nuevos: Dict[str, Any],
        faltantes: List[str],
        es_completo: bool,
    ) -> str:
        """Construye la respuesta y las preguntas del asistente."""

        partes_reconocidas = []

        if datos_actualizados.get("barrio"):
            partes_reconocidas.append(
                f"ubicado en **{datos_actualizados['barrio']}**"
            )

        if datos_actualizados.get("direccion"):
            partes_reconocidas.append(
                f"dirección **{datos_actualizados['direccion']}**"
            )

        if datos_actualizados.get("tipo"):
            partes_reconocidas.append(
                f"tipo **{datos_actualizados['tipo']}**"
            )

        if datos_actualizados.get("habitaciones"):
            partes_reconocidas.append(
                f"con **{datos_actualizados['habitaciones']} habitación(es)**"
            )

        if datos_actualizados.get("banos"):
            partes_reconocidas.append(
                f"**{datos_actualizados['banos']} baño(s)**"
            )

        if datos_actualizados.get("area_m2"):
            partes_reconocidas.append(
                f"**{datos_actualizados['area_m2']} m²**"
            )

        if datos_actualizados.get("parqueadero") is True:
            partes_reconocidas.append("con **parqueadero**")

        elif datos_actualizados.get("parqueadero") is False:
            partes_reconocidas.append("sin parqueadero")

        if datos_actualizados.get("estrato"):
            partes_reconocidas.append(
                f"estrato **{datos_actualizados['estrato']}**"
            )

        if datos_actualizados.get("precio_mensual"):
            partes_reconocidas.append(
                f"canon mensual de **${datos_actualizados['precio_mensual']:,.0f} COP**"
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
                "¡Perfecto! Ya registré los siguientes detalles "
                "de tu inmueble: "
                + "; ".join(partes_reconocidas)
                + ".\n\n"
            )

        if es_completo:
            return (
                f"{reconocido_texto}"
                "¡Tenemos toda la información obligatoria! "
                "Ahora he generado una descripción comercial y una "
                "recomendación de canon mensual basada en la información "
                "disponible del mercado. "
                "Revisa los resultados y ajusta los datos que necesites "
                "antes de registrar tu propiedad."
            )

        preguntas_faltantes = []

        if "barrio" in faltantes:
            preguntas_faltantes.append(
                "¿En qué **barrio o sector** se encuentra ubicado?"
            )

        if "tipo" in faltantes:
            preguntas_faltantes.append(
                "¿Qué **tipo de inmueble** es "
                "(apartamento, casa, habitación o finca)?"
            )

        if "habitaciones" in faltantes:
            preguntas_faltantes.append(
                "¿Cuántas **habitaciones o alcobas** tiene?"
            )

        if "banos" in faltantes:
            preguntas_faltantes.append(
                "¿Cuántos **baños** tiene?"
            )

        if "direccion" in faltantes:
            preguntas_faltantes.append(
                "¿Cuál es la **dirección exacta** del inmueble? "
                "Por ejemplo: Calle 10 # 20-30."
            )

        if "estrato" in faltantes:
            preguntas_faltantes.append(
                "¿Qué **estrato socioeconómico** tiene? "
                "Indícame un número del 1 al 6."
            )

        if "precio_mensual" in faltantes:
            preguntas_faltantes.append(
                "¿Cuál es el **canon mensual de arriendo** que quieres cobrar? "
                "Puedes escribirlo, por ejemplo, como $1.800.000."
            )

        preguntas_formateadas = "\n".join(
            f"- {pregunta}"
            for pregunta in preguntas_faltantes
        )

        opcional_tip = ""

        if (
            "area_m2" not in datos_actualizados
            or "parqueadero" not in datos_actualizados
            or not datos_actualizados.get("caracteristicas")
        ):
            opcional_tip = (
                "\n\n*(También puedes mencionar, si lo deseas, "
                "el área en metros cuadrados, si tiene parqueadero "
                "y sus características especiales.)*"
            )

        return (
            f"{reconocido_texto}"
            "¡Vamos muy bien! Para completar el registro de tu inmueble "
            "todavía necesito estos datos:\n"
            f"{preguntas_formateadas}"
            f"{opcional_tip}"
        )
