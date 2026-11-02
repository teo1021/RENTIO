"""
Generador de descripciones comerciales de inmuebles para portales inmobiliarios.
"""

from typing import Any, Dict, Optional

from app.config import settings


class GeneradorDescripcion:
    """Genera textos comerciales persuasivos sin inventar características no declaradas."""

    @staticmethod
    def _invocar_llm(prompt_sistema: str, prompt_usuario: str) -> Optional[str]:
        api_key = settings.AI_API_KEY
        if not api_key:
            return None

        provider = settings.AI_PROVIDER
        model = settings.AI_MODEL

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
            return None

        return None

    @classmethod
    def generar(cls, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera una descripción publicable para el inmueble en Medellín.
        No inventa amenidades que no estén en `caracteristicas`.
        """
        barrio = datos.get("barrio", "Medellín")
        tipo = datos.get("tipo", "apartamento")
        habitaciones = datos.get("habitaciones", 1)
        banos = datos.get("banos", 1)
        estrato = datos.get("estrato")
        area = datos.get("area_m2")
        parqueadero = datos.get("parqueadero")
        caracteristicas = datos.get("caracteristicas", [])
        tono = datos.get("tono", "atractivo y moderno")

        # Texto de amenidades strictly from input
        caracs_str = ", ".join(caracteristicas) if caracteristicas else ""

        prompt_sistema = (
            "Eres un redactor inmobiliario profesional en Medellín, Colombia. "
            "Redactas descripciones comerciales atractivas para portales de arriendo. "
            "REGLA OBLIGATORIA: NUNCA inventes características, amenidades o servicios que el usuario no haya mencionado explícitamente."
        )

        detalles_usuario = [
            f"Tipo: {tipo}",
            f"Barrio: {barrio}",
            f"Habitaciones: {habitaciones}",
            f"Baños: {banos}",
        ]
        if estrato:
            detalles_usuario.append(f"Estrato: {estrato}")
        if area:
            detalles_usuario.append(f"Área: {area} m²")
        if parqueadero is True:
            detalles_usuario.append("Parqueadero: Sí incluye parqueadero")
        elif parqueadero is False:
            detalles_usuario.append("Parqueadero: No incluye parqueadero")
        if caracs_str:
            detalles_usuario.append(f"Amenidades confirmadas: {caracs_str}")

        prompt_usuario = (
            f"Crea una descripción comercial para arriendo en Medellín con los siguientes datos confirmados:\n"
            + "\n".join(f"- {d}" for d in detalles_usuario)
            + f"\nTono deseado: {tono}. "
            "Responde únicamente con el texto listo para publicar en el portal, destacando la ubicación y distribución."
        )

        texto_ia = cls._invocar_llm(prompt_sistema, prompt_usuario)

        if not texto_ia:
            # Plantilla determinista contextual sin alucinaciones
            area_frase = f" con un área de {area} m²" if area else ""
            estrato_frase = f" (Estrato {estrato})" if estrato else ""
            parq_frase = " Cuenta con parqueadero privado." if parqueadero is True else ""

            if caracs_str:
                amenidades_frase = f" Entre sus comodidades confirmadas se destacan: {caracs_str}."
            else:
                amenidades_frase = ""

            texto_ia = (
                f"¡Gran oportunidad de arriendo en {barrio}! "
                f"Se arrienda acogedor {tipo}{area_frase}{estrato_frase}, "
                f"distribuido en {habitaciones} habitación(es) y {banos} baño(s). "
                f"{amenidades_frase}{parq_frase} "
                f"¡Contáctanos para obtener más información y agendar una visita!"
            )

        # Puntos destacados
        puntos = [
            f"Ubicación en {barrio}",
            f"{habitaciones} habitación(es) y {banos} baño(s)",
        ]
        if area:
            puntos.append(f"Área de {area} m²")
        if parqueadero is True:
            puntos.append("Parqueadero privado incluido")
        if estrato:
            puntos.append(f"Estrato {estrato}")
        for c in caracteristicas[:4]:
            puntos.append(c)

        return {
            "descripcion": texto_ia,
            "puntos_destacados": puntos,
        }
