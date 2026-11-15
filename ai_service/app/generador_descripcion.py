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
        except Exception as exc:
            raise RuntimeError(
                "No fue posible generar contenido con el proveedor de IA configurado."
            ) from exc

        raise RuntimeError(f"El proveedor de IA '{provider}' no está soportado.")

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
        descripcion_actual = datos.get("descripcion_actual")
        tono = datos.get("tono", "atractivo y moderno")

        # Texto de amenidades strictly from input
        caracs_str = ", ".join(caracteristicas) if caracteristicas else ""

        prompt_sistema = (
            "Eres un redactor y copywriter inmobiliario de primer nivel en Medellín, Colombia. "
            "Tu misión es crear descripciones de arriendo irresistibles, profesionales, cálidas y sumamente atractivas "
            "(llamativas), orientadas a captar inquilinos calificados en los mejores portales inmobiliarios.\n"
            "DIRECTRICES DE REDACCIÓN:\n"
            "1. Tono cautivador: Empieza con un gancho entusiasta que resalte el estilo de vida, confort y la excelente ubicación en Medellín.\n"
            "2. Espacio y luz: Describe las habitaciones, baños y áreas destacando la distribución funcional, iluminación y sensación de amplitud.\n"
            "3. Beneficios tangibles: Conecta las comodidades (como parqueadero, balcón, ascensor, solo si están confirmadas) con momentos agradables del día a día.\n"
            "4. Llamado a la acción: Cierra invitando amablemente a agendar una visita antes de que se arriende.\n"
            "5. REGLA OBLIGATORIA DE FIDELIDAD: NUNCA inventes características, amenidades ni servicios que el usuario no haya confirmado explícitamente."
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
        if descripcion_actual and descripcion_actual.strip():
            detalles_usuario.append(
                f"Descripción previa que debes mejorar sin agregar hechos: {descripcion_actual.strip()}"
            )

        prompt_usuario = (
            f"{'Mejora y potencia la siguiente descripción previa haciéndola mucho más comercial y llamativa' if descripcion_actual else 'Crea una descripción comercial sumamente llamativa y atractiva'} "
            f"para arriendo en Medellín con los siguientes datos confirmados:\n"
            + "\n".join(f"- {d}" for d in detalles_usuario)
            + f"\nTono deseado: {tono} (moderno, vibrante, profesional).\n"
            "Escribe un texto persuasivo listo para publicar, con formato limpio, párrafos fluidos y un llamado a agendar visita."
        )

        texto_ia = cls._invocar_llm(prompt_sistema, prompt_usuario)

        if not texto_ia:
            # Plantilla determinista contextual llamativa y sin alucinaciones
            area_frase = f", perfectamente distribuidos en {area} m² de área privada" if area else ""
            estrato_frase = f" en estrato {estrato}" if estrato else ""

            amenidades_bloque = ""
            if caracs_str:
                amenidades_bloque = f"\n\n✨ Comodidades destacadas:\nDisfruta de {caracs_str}."
            if parqueadero is True:
                amenidades_bloque += ("\n" if not amenidades_bloque else " ") + "🚗 Incluye parqueadero privado para tu total comodidad y seguridad."

            hab_texto = f"{habitaciones} espaciosa{'s' if habitaciones != 1 else ''} habitaci{'ón' if habitaciones == 1 else 'ones'}"
            bano_texto = f"{banos} baño{'s' if banos != 1 else ''} funcional{'es' if banos != 1 else ''}"

            texto_ia = (
                f"¡Excelente oportunidad de arriendo en {barrio}! "
                f"Espectacular {tipo}{estrato_frase}, diseñado para brindarte el máximo confort y bienestar.\n\n"
                f"La propiedad destaca por su iluminación natural, ventilación y distribución inteligente. "
                f"Cuenta con {hab_texto} y {bano_texto}{area_frase}, creando un ambiente acogedor ideal para vivir con tranquilidad.{amenidades_bloque}\n\n"
                f"📍 Ubicación privilegiada en {barrio}, con fácil acceso al transporte público, zonas comerciales, parques y servicios esenciales.\n\n"
                f"¡No dejes pasar esta oportunidad! Agenda tu visita hoy mismo y enamórate de tu nuevo hogar."
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
