"""
Esquemas Pydantic para el servicio de IA Marketing.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MensajeItem(BaseModel):
    rol: str = Field(..., description="usuario, asistente o sistema")
    contenido: str = Field(..., description="Texto del mensaje")


class ConversarRequest(BaseModel):
    mensaje_usuario: str = Field(..., min_length=1, description="Mensaje del propietario en lenguaje natural")
    datos_previos: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Datos ya recopilados en la conversación")
    historial: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Mensajes previos del chat")
    barrios_disponibles: List[str] = Field(default_factory=list, description="Nombres validados del catálogo de Medellín")


class MetadatosCalculo(BaseModel):
    metodo: str
    barrio_id: Optional[str] = None
    barrio_nombre: Optional[str] = None
    habitaciones: int
    avisos_muestra: int
    fuentes: Optional[int] = None
    fecha_datos: str
    version_fuente: str
    p25: Optional[float] = None
    mediana: Optional[float] = None
    p75: Optional[float] = None
    con_parqueadero: Optional[bool] = None
    mediana_con_parqueadero: Optional[float] = None
    limitaciones: List[str]


class ResultadoGeneradoItem(BaseModel):
    descripcion_sugerida: str
    puntos_destacados: List[str]
    precio_estimado: float
    precio_minimo: Optional[float] = None
    precio_maximo: Optional[float] = None
    moneda: str = "COP"
    metadatos_calculo: MetadatosCalculo
    analisis_resumido: str


class ConversarResponse(BaseModel):
    datos_extraidos: Dict[str, Any]
    datos_actualizados: Dict[str, Any]
    datos_faltantes: List[str]
    es_completo: bool
    respuesta_asistente: str
    resultado_generado: Optional[ResultadoGeneradoItem] = None


class GenerarContratoRequest(BaseModel):
    """Solicitud sin datos personales para generar únicamente una plantilla contractual."""

    tipo_contrato: str = Field(default="arrendamiento_vivienda_urbana_colombia")


class GenerarContratoResponse(BaseModel):
    plantilla: str


class EstimarPrecioRequest(BaseModel):
    barrio: str = Field(..., min_length=2, description="Nombre o sector del barrio")
    habitaciones: int = Field(..., ge=1, le=15, description="Cantidad de habitaciones/alcobas")
    parqueadero: Optional[bool] = Field(None, description="Indica si incluye parqueadero")
    tipo: Optional[str] = Field("apartamento", description="Tipo de inmueble (apartamento, casa, habitacion, finca)")
    estrato: Optional[int] = Field(None, ge=1, le=6, description="Estrato socioeconómico opcional")
    area_m2: Optional[float] = Field(None, gt=0, description="Área en metros cuadrados")


class EstimarPrecioResponse(BaseModel):
    precio_sugerido: float
    precio_minimo: Optional[float] = None
    precio_maximo: Optional[float] = None
    moneda: str = "COP"
    metadatos_calculo: MetadatosCalculo
    analisis: str


class GenerarDescripcionRequest(BaseModel):
    barrio: str
    tipo: str = "apartamento"
    habitaciones: int = 1
    banos: int = 1
    area_m2: Optional[float] = None
    estrato: Optional[int] = None
    caracteristicas: Optional[List[str]] = Field(default_factory=list)
    descripcion_actual: Optional[str] = None
    tono: Optional[str] = "atractivo y moderno"


class GenerarDescripcionResponse(BaseModel):
    descripcion: str
    puntos_destacados: List[str]


class AnalisisMercadoRequest(BaseModel):
    barrio: str
    tipo: Optional[str] = "apartamento"
    estrato: Optional[int] = 4


class AnalisisMercadoResponse(BaseModel):
    zona: str
    estrato_predominante: Optional[int] = None
    tipo_inmueble: str
    nivel_demanda: str
    tiempo_promedio_vacancia_dias: Optional[int] = None
    tendencia_mercado: str
    recomendacion: str


class MejorarTituloRequest(BaseModel):
    titulo_actual: str
    barrio: str
    tipo: Optional[str] = "Apartamento"
    caracteristicas_destacadas: Optional[List[str]] = Field(default_factory=list)


class MejorarTituloResponse(BaseModel):
    titulo_original: str
    titulos_sugeridos: List[str]
