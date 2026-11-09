"""
Controladores del dominio de IA Marketing.

Define el blueprint `ia_bp` con endpoints especializados para propietarios.
"""

import unicodedata
import os

from flask import Blueprint, current_app, jsonify, request
from marshmallow import ValidationError

from app import db
from app.dominios.barrios.modelos import Barrio
from app.dominios.caracteristicas.modelos import Caracteristica
from app.dominios.propiedades.archivos import borrar_archivos, guardar_imagenes
from app.dominios.propiedades.dtos import CrearPropiedadDTO
from app.dominios.ia_marketing.cliente import (
    ServicioIAError,
)
from app.dominios.ia_marketing.cliente import (
    conversar as conversar_con_ia,
)
from app.dominios.ia_marketing.cliente import (
    solicitar as solicitar_a_ia,
)
from app.dominios.ia_marketing.dtos import (
    AnalisisMercadoDTO,
    GenerarDescripcionDTO,
    MejorarTituloDTO,
    SugerirPrecioDTO,
)
from app.dominios.ia_marketing.modelos import (
    ConversacionMarketing,
    MensajeMarketing,
    ResultadoMarketing,
)
from app.dominios.propiedades.modelos import Propiedad
from app.dominios.propiedades.servicios import PropiedadServicio
from app.seguridad import requiere_propietario

# â”€â”€ Blueprint â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
ia_bp = Blueprint("ia", __name__)


def _llamar_servicio_ai(endpoint, datos):
    try:
        return solicitar_a_ia(endpoint, datos), None
    except ServicioIAError as exc:
        return None, (
            jsonify({"success": False, "error": {"message": str(exc)}}),
            exc.status_code,
        )


def _mensaje_dict(mensaje):
    return {
        "id": mensaje.id,
        "rol": mensaje.rol,
        "contenido": mensaje.contenido,
        "datos_extraidos": mensaje.datos_extraidos,
        "fecha_creacion": mensaje.fecha_creacion.isoformat(),
    }


def _resultado_dict(resultado):
    return {
        "id": resultado.id,
        "descripcion": resultado.descripcion,
        "precio_sugerido": float(resultado.precio_sugerido) if resultado.precio_sugerido is not None else None,
        "precio_minimo": float(resultado.precio_minimo) if resultado.precio_minimo is not None else None,
        "precio_maximo": float(resultado.precio_maximo) if resultado.precio_maximo is not None else None,
        "moneda": resultado.moneda,
        "datos_usados": resultado.datos_usados,
        "metadatos_calculo": resultado.metadatos_calculo,
        "fecha_creacion": resultado.fecha_creacion.isoformat(),
    }


def _conversacion_dict(conversacion):
    return {
        "id": conversacion.id,
        "propiedad_id": conversacion.propiedad_id,
        "estado": conversacion.estado,
        "datos_recopilados": conversacion.datos_recopilados,
        "mensajes": [_mensaje_dict(m) for m in conversacion.mensajes],
        "resultados": [_resultado_dict(r) for r in conversacion.resultados],
        "fecha_creacion": conversacion.fecha_creacion.isoformat(),
        "fecha_actualizacion": conversacion.fecha_actualizacion.isoformat(),
    }


def _normalizar_texto(valor):
    if valor is None:
        return ""
    texto = str(valor).strip().lower()
    return unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")


def _resolver_barrio_id(nombre_barrio):
    if not nombre_barrio:
        return None
    nombre = _normalizar_texto(nombre_barrio)
    for barrio in Barrio.query.all():
        if _normalizar_texto(barrio.nombre) == nombre:
            return barrio.id
    return None


def _resolver_caracteristicas_ids(caracteristicas):
    if not caracteristicas:
        return []
    ids = []
    for item in caracteristicas:
        if isinstance(item, int):
            ids.append(item)
            continue
        nombre = str(item).strip()
        if not nombre:
            continue
        for caracteristica in Caracteristica.query.all():
            if _normalizar_texto(caracteristica.nombre) == _normalizar_texto(nombre):
                ids.append(caracteristica.id)
                break
    return list(dict.fromkeys(ids))


@ia_bp.route("/conversaciones", methods=["POST"])
@requiere_propietario
def crear_conversacion(usuario_id=None):
    datos = request.get_json(silent=True) or {}
    propiedad_id = datos.get("propiedad_id")
    prellenado = {}
    if propiedad_id is not None:
        propiedad = Propiedad.query.filter_by(id=propiedad_id, propietario_id=usuario_id).first()
        if propiedad is None:
            return jsonify({"success": False, "error": {"message": "Propiedad no encontrada."}}), 404
        prellenado = {
            "tipo": propiedad.tipo,
            "barrio": propiedad.barrio.nombre if propiedad.barrio else None,
            "habitaciones": propiedad.habitaciones,
            "banos": propiedad.banos,
            "area_m2": float(propiedad.area_m2) if propiedad.area_m2 else None,
            "estrato": propiedad.estrato,
            "direccion": propiedad.direccion,
            "precio_mensual": float(propiedad.precio_mensual),
            "descripcion": propiedad.descripcion,
            "parqueadero": any(
                "parqueadero" in _normalizar_texto(caracteristica.nombre)
                for caracteristica in propiedad.caracteristicas
            ),
            "caracteristicas": [c.nombre for c in propiedad.caracteristicas],
        }
        prellenado = {
            k: v
            for k, v in prellenado.items()
            if v is not None or k == "parqueadero"
        }
    conversacion = ConversacionMarketing(
        propietario_id=usuario_id,
        propiedad_id=propiedad_id,
        datos_recopilados=prellenado,
    )
    db.session.add(conversacion)
    db.session.commit()
    return jsonify({"success": True, "data": _conversacion_dict(conversacion)}), 201


@ia_bp.route("/conversaciones", methods=["GET"])
@requiere_propietario
def listar_conversaciones(usuario_id=None):
    items = ConversacionMarketing.query.filter_by(propietario_id=usuario_id).order_by(
        ConversacionMarketing.fecha_actualizacion.desc()
    ).all()
    return jsonify({"success": True, "data": [_conversacion_dict(c) for c in items]}), 200


@ia_bp.route("/conversaciones/<int:conversacion_id>", methods=["GET"])
@requiere_propietario
def obtener_conversacion(conversacion_id, usuario_id=None):
    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id, propietario_id=usuario_id
    ).first()
    if conversacion is None:
        return jsonify({"success": False, "error": {"message": "ConversaciÃ³n no encontrada."}}), 404
    return jsonify({"success": True, "data": _conversacion_dict(conversacion)}), 200


@ia_bp.route("/conversaciones/<int:conversacion_id>/mensajes", methods=["POST"])
@requiere_propietario
def enviar_mensaje(conversacion_id, usuario_id=None):
    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id, propietario_id=usuario_id
    ).first()
    if conversacion is None:
        return jsonify({"success": False, "error": {"message": "ConversaciÃ³n no encontrada."}}), 404
    datos = request.get_json(silent=True) or {}
    mensaje = datos.get("mensaje", "")
    if not isinstance(mensaje, str) or not mensaje.strip() or len(mensaje) > 4000:
        return jsonify({"success": False, "error": {"message": "El mensaje debe tener entre 1 y 4000 caracteres."}}), 400
    historial = [
        {"rol": item.rol, "contenido": item.contenido}
        for item in conversacion.mensajes[-12:]
    ]
    try:
        respuesta = conversar_con_ia(
            mensaje.strip(),
            conversacion.datos_recopilados or {},
            historial=historial,
        )
    except ServicioIAError as exc:
        return jsonify({"success": False, "error": {"message": str(exc)}}), exc.status_code

    conversacion.datos_recopilados = respuesta["datos_actualizados"]
    conversacion.estado = "lista" if respuesta["es_completo"] else "recopilando"
    db.session.add(MensajeMarketing(conversacion_id=conversacion.id, rol="usuario", contenido=mensaje.strip()))
    db.session.add(MensajeMarketing(
        conversacion_id=conversacion.id,
        rol="asistente",
        contenido=respuesta["respuesta_asistente"],
        datos_extraidos=respuesta.get("datos_extraidos", {}),
    ))
    resultado = respuesta.get("resultado_generado")
    if resultado:
        db.session.add(ResultadoMarketing(
            conversacion_id=conversacion.id,
            propiedad_id=conversacion.propiedad_id,
            descripcion=resultado["descripcion_sugerida"],
            precio_sugerido=resultado["precio_estimado"],
            precio_minimo=resultado["precio_minimo"],
            precio_maximo=resultado["precio_maximo"],
            moneda=resultado["moneda"],
            datos_usados=respuesta["datos_actualizados"],
            fuente_datos="datasets de avisos de arriendo MedellÃ­n",
            version_datos=resultado["metadatos_calculo"]["version_fuente"],
            metadatos_calculo=resultado["metadatos_calculo"],
        ))
    db.session.commit()
    return jsonify({"success": True, "data": {
        "conversacion_id": conversacion.id,
        "datos_actualizados": respuesta["datos_actualizados"],
        "datos_faltantes": respuesta["datos_faltantes"],
        "es_completo": respuesta["es_completo"],
        "respuesta_asistente": respuesta["respuesta_asistente"],
        "resultado_generado": resultado,
    }}), 200


@ia_bp.route("/conversaciones/<int:conversacion_id>/aplicar", methods=["POST"])
@requiere_propietario
def aplicar_resultado(conversacion_id, usuario_id=None):
    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id, propietario_id=usuario_id
    ).first()
    if conversacion is None:
        return jsonify({"success": False, "error": {"message": "ConversaciÃ³n no encontrada."}}), 404
    if not conversacion.propiedad_id:
        return jsonify({"success": False, "error": {"message": "La conversaciÃ³n no estÃ¡ asociada a una propiedad."}}), 400
    propiedad = Propiedad.query.filter_by(id=conversacion.propiedad_id, propietario_id=usuario_id).first()
    resultado = ResultadoMarketing.query.filter_by(conversacion_id=conversacion.id).order_by(
        ResultadoMarketing.fecha_creacion.desc(), ResultadoMarketing.id.desc()
    ).first()
    if propiedad is None or resultado is None:
        return jsonify({"success": False, "error": {"message": "No hay un resultado aplicable."}}), 400
    propiedad.descripcion = resultado.descripcion
    if resultado.precio_sugerido is not None:
        propiedad.precio_mensual = resultado.precio_sugerido
    conversacion.estado = "generada"
    db.session.commit()
    return jsonify({"success": True, "message": "DescripciÃ³n y precio aplicados a la propiedad."}), 200


@ia_bp.route("/conversaciones/<int:conversacion_id>/crear-propiedad", methods=["POST"])
@requiere_propietario
def crear_propiedad_desde_conversacion(conversacion_id, usuario_id=None):
    """Confirma y crea la propiedad junto con sus fotografías."""
    conversacion = ConversacionMarketing.query.filter_by(
        id=conversacion_id, propietario_id=usuario_id
    ).first()
    if conversacion is None:
        return jsonify({"success": False, "error": {"message": "Conversación no encontrada."}}), 404

    if conversacion.propiedad_id:
        propiedad_existente = Propiedad.query.filter_by(
            id=conversacion.propiedad_id,
            propietario_id=usuario_id,
        ).first()
        if propiedad_existente:
            return jsonify({
                "success": True,
                "message": "La propiedad ya fue creada desde esta conversación.",
                "data": propiedad_existente.to_dict(),
            }), 200

    if conversacion.estado != "lista":
        return jsonify({
            "success": False,
            "error": {"message": "La conversación aún no ha completado y validado los datos obligatorios."},
        }), 400

    if request.is_json:
        payload = request.get_json(silent=True) or {}
        archivos = []
    else:
        import json

        try:
            payload = json.loads(request.form.get("datos", "{}"))
        except ValueError:
            return jsonify({"success": False, "error": {"message": "Los datos de la propiedad no tienen un formato válido."}}), 400
        if not isinstance(payload, dict):
            return jsonify({"success": False, "error": {"message": "Los datos de la propiedad deben ser un objeto JSON."}}), 400
        archivos = request.files.getlist("imagenes")

    datos = dict(conversacion.datos_recopilados or {})
    datos.update({
        key: value
        for key, value in payload.items()
        if key in {"titulo", "descripcion"}
    })

    campos_requeridos = (
        "barrio",
        "tipo",
        "habitaciones",
        "banos",
        "direccion",
        "estrato",
        "precio_mensual",
    )
    faltantes = [campo for campo in campos_requeridos if datos.get(campo) in (None, "")]
    if faltantes:
        return jsonify({
            "success": False,
            "error": {
                "message": "La conversación todavía no tiene toda la información necesaria.",
                "details": {"faltantes": faltantes},
            },
        }), 400

    if not datos.get("titulo"):
        tipo = str(datos["tipo"]).strip().capitalize()
        datos["titulo"] = f"{tipo} en {str(datos['barrio']).strip()}"

    datos["barrio_id"] = _resolver_barrio_id(datos["barrio"])
    if not datos.get("barrio_id"):
        return jsonify({
            "success": False,
            "error": {"message": "No se pudo validar el barrio en el catálogo de RENTIO. Corrígelo en el chat."},
        }), 400

    if isinstance(datos.get("caracteristicas"), list):
        datos["caracteristicas_ids"] = _resolver_caracteristicas_ids(datos["caracteristicas"])

    propiedad_payload = {
        "titulo": datos["titulo"],
        "descripcion": datos.get("descripcion") or None,
        "precio_mensual": datos["precio_mensual"],
        "direccion": datos["direccion"],
        "estrato": datos["estrato"],
        "area_m2": datos.get("area_m2") or None,
        "habitaciones": datos["habitaciones"],
        "banos": datos["banos"],
        "tipo": datos["tipo"],
        "barrio_id": datos["barrio_id"],
        "caracteristicas_ids": datos.get("caracteristicas_ids") or [],
    }
    try:
        validado = CrearPropiedadDTO().load(propiedad_payload)
    except ValidationError as err:
        return jsonify({
            "success": False,
            "error": {"message": "Los datos de la propiedad no son válidos.", "details": err.messages},
        }), 400
    if validado["precio_mensual"] <= 0:
        return jsonify({"success": False, "error": {"message": "El canon mensual debe ser mayor que cero."}}), 400

    propiedad = PropiedadServicio().crear(validado, usuario_id, commit=False)
    db.session.flush()
    rutas = []
    try:
        if archivos:
            carpeta = current_app.config.get("PROPERTY_IMAGE_FOLDER") or os.path.join(
                current_app.static_folder or "", "uploads", "propiedades"
            )
            _, rutas = guardar_imagenes(
                propiedad,
                archivos,
                carpeta,
                request.host_url,
            )
        conversacion.propiedad_id = propiedad.id
        conversacion.estado = "generada"
        db.session.add(conversacion)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        borrar_archivos(rutas)
        return jsonify({"success": False, "error": {"message": str(exc)}}), 400
    except Exception:
        db.session.rollback()
        borrar_archivos(rutas)
        raise

    return jsonify({
        "success": True,
        "message": "Propiedad creada con éxito desde la conversación.",
        "data": propiedad.to_dict(),
    }), 201


@ia_bp.route("/generar-descripcion", methods=["POST"])
@requiere_propietario
def generar_descripcion(usuario_id=None):
    """Genera una descripciÃ³n atractiva para la propiedad con IA."""
    try:
        datos = GenerarDescripcionDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada invÃ¡lidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/generar-descripcion", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "DescripciÃ³n generada con Ã©xito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/sugerir-precio", methods=["POST"])
@requiere_propietario
def sugerir_precio(usuario_id=None):
    """Estima y sugiere rangos de precios de mercado con IA."""
    try:
        datos = SugerirPrecioDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada invÃ¡lidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/estimar-precio", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "Sugerencia de precio calculada con Ã©xito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/analisis-mercado", methods=["POST"])
@requiere_propietario
def analisis_mercado(usuario_id=None):
    """Genera un anÃ¡lisis de mercado y demanda para la zona."""
    try:
        datos = AnalisisMercadoDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada invÃ¡lidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/analisis-mercado", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "AnÃ¡lisis de mercado generado con Ã©xito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/mejorar-titulo", methods=["POST"])
@requiere_propietario
def mejorar_titulo(usuario_id=None):
    """Propone mejoras llamativas para el tÃ­tulo del anuncio."""
    try:
        datos = MejorarTituloDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada invÃ¡lidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/mejorar-titulo", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "TÃ­tulos mejorados generados con Ã©xito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/extraer-datos-propiedad", methods=["POST"])
@requiere_propietario
def extraer_datos_propiedad(usuario_id=None):
    """
    Extrae los datos estructurados de una propiedad a partir de un texto libre.
    El usuario escribe la descripciÃ³n del inmueble y la IA identifica los campos.
    """
    try:
        datos = ExtraerDatosPropiedadDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada invÃ¡lidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/extraer-datos-propiedad", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "Datos extraÃ­dos con Ã©xito.",
                "data": resultado,
            }
        ),
        200,
    )


@ia_bp.route("/busqueda-texto", methods=["POST"])
@requiere_propietario
def busqueda_texto(usuario_id=None):
    """
    Busca propiedades usando una consulta en texto libre.
    La IA interpreta la consulta y sugiere filtros aplicables.
    """
    try:
        datos = BuscarPropiedadesDTO().load(request.get_json() or {})
    except ValidationError as err:
        return (
            jsonify(
                {
                    "success": False,
                    "error": {
                        "message": "Datos de entrada invÃ¡lidos.",
                        "details": err.messages,
                    },
                }
            ),
            400,
        )

    resultado, error = _llamar_servicio_ai("/api/v1/ia/busqueda-texto", datos)
    if error:
        return error
    return (
        jsonify(
            {
                "success": True,
                "message": "BÃºsqueda procesada con Ã©xito.",
                "data": resultado,
            }
        ),
        200,
    )
