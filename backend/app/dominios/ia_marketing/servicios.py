"""
Servicios del dominio de IA Marketing.

Lógica de integración con modelos de IA (OpenAI, Gemini) especializada
en el mercado inmobiliario de Medellín.
"""

from flask import current_app

# ═══════════════════════════════════════════════════════════════════════════════
# Excepciones de dominio
# ═══════════════════════════════════════════════════════════════════════════════


class IAMarketingError(Exception):
    """Se lanza cuando ocurre un fallo al invocar el proveedor de IA."""

    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Servicio
# ═══════════════════════════════════════════════════════════════════════════════


class IAMarketingServicio:
    """Lógica para generación de marketing y análisis inmobiliario con IA."""

    @staticmethod
    def _invocar_llm(prompt_sistema, prompt_usuario):
        """
        Invoca el proveedor configurado de IA (OpenAI o Gemini).

        Si no hay API KEY configurada, retorna un contenido generado
        localmente basado en reglas para garantizar operatividad y testing.
        """
        api_key = current_app.config.get("AI_API_KEY", "")
        provider = current_app.config.get("AI_PROVIDER", "openai").lower()
        model = current_app.config.get("AI_MODEL", "gpt-4o-mini")

        if not api_key:
            return None

        try:
            if provider == "openai":
                from openai import OpenAI

                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": prompt_usuario},
                    ],
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()

            elif provider == "gemini":
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                g_model = genai.GenerativeModel(model)
                response = g_model.generate_content(f"{prompt_sistema}\n\n{prompt_usuario}")
                return response.text.strip()

        except Exception:
            # Fallback a generador contextual local si falla la red externa
            return None

        return None

    @staticmethod
    def generar_descripcion(datos):
        """
        Genera una descripción comercial persuasiva para arriendo en Medellín.

        Args:
            datos: Diccionario validado por GenerarDescripcionDTO.

        Returns:
            dict: {"descripcion": str, "puntos_destacados": list}
        """
        barrio = datos["barrio"]
        tipo = datos.get("tipo", "apartamento")
        estrato = datos.get("estrato", 4)
        habitaciones = datos.get("habitaciones", 2)
        banos = datos.get("banos", 2)
        area = datos.get("area_m2")
        caracteristicas = ", ".join(datos.get("caracteristicas", [])) or "servicios completos"
        tono = datos.get("tono", "atractivo y moderno")

        prompt_sistema = (
            "Eres un experto redactor inmobiliario especializado en Medellín, Colombia. "
            "Escribes textos comerciales persuasivos, destacando la ubicación, comodidades, "
            "vías de acceso y estilo de vida de la capital antioqueña."
        )
        prompt_usuario = (
            f"Crea una descripción para arrendar un {tipo} en el barrio {barrio} (Estrato {estrato}). "
            f"Cuenta con {habitaciones} habitaciones, {banos} baños, área de {area or 'amplia'} m2. "
            f"Características adicionales: {caracteristicas}. Tono: {tono}. "
            "Responde en formato directo para publicación en portales."
        )

        respuesta_ia = IAMarketingServicio._invocar_llm(prompt_sistema, prompt_usuario)

        if not respuesta_ia:
            area_str = f" con {area} m² construidos" if area else ""
            respuesta_ia = (
                f"¡Excelente oportunidad de arriendo en {barrio}! "
                f"Hermoso {tipo}{area_str}, ubicado en una de las mejores zonas de Medellín (estrato {estrato}). "
                f"Cuenta con {habitaciones} cómodas habitaciones, {banos} baños con finos acabados y espacios llenos de iluminación natural. "
                f"Incluye destacadas comodidades como: {caracteristicas}. "
                f"Cerca a rutas de transporte, centros comerciales y zonas gastronómicas. ¡Agenda tu visita hoy mismo!"
            )

        return {
            "descripcion": respuesta_ia,
            "puntos_destacados": [
                f"Ubicación privilegiada en {barrio}",
                f"{habitaciones} habitaciones y {banos} baños",
                f"Estrato {estrato}",
                f"Comodidades: {caracteristicas}",
            ],
        }

    @staticmethod
    def sugerir_precio(datos):
        """
        Sugiere un rango de precio mensual estimado para una propiedad en Medellín.

        Args:
            datos: Diccionario validado por SugerirPrecioDTO.

        Returns:
            dict: {"precio_sugerido": float, "precio_minimo": float, "precio_maximo": float, "analisis": str}
        """
        barrio = datos["barrio"]
        estrato = datos["estrato"]
        tipo = datos.get("tipo", "apartamento")
        area = datos.get("area_m2") or 70.0
        habitaciones = datos.get("habitaciones", 2)

        # Cálculo estimado base para Medellín por metro cuadrado según estrato
        factor_estrato = {
            1: 15000,
            2: 20000,
            3: 28000,
            4: 38000,
            5: 48000,
            6: 62000,
        }.get(estrato, 35000)

        # Ajuste por barrios cotizados (Poblado, Laureles, Envigado)
        multiplicador_zona = 1.0
        barrio_lower = barrio.lower()
        if "poblado" in barrio_lower:
            multiplicador_zona = 1.35
        elif "laureles" in barrio_lower or "envigado" in barrio_lower:
            multiplicador_zona = 1.2
        elif "sabaneta" in barrio_lower or "belén" in barrio_lower or "belen" in barrio_lower:
            multiplicador_zona = 1.05

        precio_base = area * factor_estrato * multiplicador_zona
        precio_sugerido = round(precio_base / 50000) * 50000
        precio_minimo = round((precio_sugerido * 0.9) / 50000) * 50000
        precio_maximo = round((precio_sugerido * 1.15) / 50000) * 50000

        analisis = (
            f"Para un {tipo} de {habitaciones} habitaciones en {barrio} de {area} m² (estrato {estrato}), "
            f"el promedio de canon en el mercado actual de Medellín oscila entre "
            f"${precio_minimo:,.0f} y ${precio_maximo:,.0f} COP mensuales."
        )

        return {
            "precio_sugerido": float(precio_sugerido),
            "precio_minimo": float(precio_minimo),
            "precio_maximo": float(precio_maximo),
            "moneda": "COP",
            "analisis": analisis,
        }

    @staticmethod
    def analisis_mercado(datos):
        """
        Provee un análisis de demanda, perfil de inquilinos y rentabilidad en Medellín.

        Args:
            datos: Diccionario validado por AnalisisMercadoDTO.

        Returns:
            dict: Indicadores clave de la zona inmobiliaria.
        """
        barrio = datos["barrio"]
        tipo = datos.get("tipo", "apartamento")
        estrato = datos.get("estrato", 4)

        barrio_lower = barrio.lower()
        if "poblado" in barrio_lower:
            demanda = "Muy Alta (perfil nómadas digitales, ejecutivos y extranjeros)"
            tiempo_promedio_dias = 15
            tendencia = "Al alza debido a alta demanda turística y corporativa."
        elif "laureles" in barrio_lower:
            demanda = "Alta (familias, estudiantes de posgrado y profesionales)"
            tiempo_promedio_dias = 20
            tendencia = "Estable con alta valorización por ambiente caminable y gastronomía."
        elif "belén" in barrio_lower or "belen" in barrio_lower:
            demanda = "Alta (familias y jóvenes profesionales)"
            tiempo_promedio_dias = 25
            tendencia = "Excelente conectividad Metroplús y amplia oferta comercial."
        else:
            demanda = "Moderada a Alta"
            tiempo_promedio_dias = 30
            tendencia = "Crecimiento sostenido en el área metropolitana del Valle de Aburrá."

        return {
            "zona": f"{barrio}, Medellín",
            "estrato_predominante": estrato,
            "tipo_inmueble": tipo,
            "nivel_demanda": demanda,
            "tiempo_promedio_vacancia_dias": tiempo_promedio_dias,
            "tendencia_mercado": tendencia,
            "recomendacion": "Publicar con fotografías iluminadas y contrato garantizado.",
        }

    @staticmethod
    def mejorar_titulo(datos):
        """
        Genera variaciones atractivas y optimizadas de título para portales.

        Args:
            datos: Diccionario validado por MejorarTituloDTO.

        Returns:
            dict: {"titulos_sugeridos": list}
        """
        titulo_actual = datos["titulo_actual"]
        barrio = datos["barrio"]
        tipo = datos.get("tipo", "Apartamento")
        caracteristicas = datos.get("caracteristicas_destacadas", [])

        destacado = caracteristicas[0] if caracteristicas else "Excelente Ubicación"

        titulos = [
            f"Hermoso {tipo.title()} en {barrio} | {destacado} y Gran Iluminación",
            f"Arriendo en {barrio} — {tipo.title()} Moderno con {destacado}",
            f"Espectacular {tipo.title()} en {barrio} — Ideal para Vivir Cómodo",
            f"Oportunidad en Medellín: {tipo.title()} en {barrio} | Ubicación Insuperable",
        ]

        return {
            "titulo_original": titulo_actual,
            "titulos_sugeridos": titulos,
        }
