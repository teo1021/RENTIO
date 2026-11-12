export type Rol = 'arrendatario' | 'propietario' | 'admin';

export interface Perfil {
  id?: number;
  nombre?: string | null;
  apellido?: string | null;
  telefono?: string | null;
  cedula?: string | null;
  foto_perfil?: string | null;
}

export interface Usuario {
  id: number;
  correo: string;
  rol: Rol;
  fecha_creacion?: string;
  perfil?: Perfil | null;
}

export interface Barrio {
  id: number;
  nombre: string;
  comuna: string;
  zona: string;
}

export interface Caracteristica {
  id: number;
  nombre: string;
  icono?: string | null;
}

export type EstadoPropiedad = 'disponible' | 'arrendada' | 'inactiva';
export type TipoPropiedad = 'casa' | 'apartamento' | 'habitacion' | 'finca';

export interface ImagenPropiedad {
  id: number;
  url: string;
  orden: number;
}

export interface Propiedad {
  id: number;
  titulo: string;
  descripcion?: string | null;
  precio_mensual: number;
  direccion: string;
  estrato: number;
  area_m2?: number | null;
  habitaciones: number;
  banos: number;
  tipo: TipoPropiedad;
  estado: EstadoPropiedad;
  barrio_id?: number | null;
  barrio?: Barrio | null;
  propietario_id: number;
  caracteristicas: Caracteristica[];
  imagenes: ImagenPropiedad[];
  fecha_creacion?: string;
}

export interface SolicitudArriendo {
  id: number;
  propiedad_id: number;
  propiedad?: Pick<Propiedad, 'id' | 'titulo' | 'precio_mensual' | 'direccion'> | null;
  arrendatario_id: number;
  arrendatario?: {
    id: number;
    correo: string;
    perfil?: Perfil | null;
  } | null;
  mensaje?: string | null;
  cedula_arrendatario?: string | null;
  telefono_arrendatario?: string | null;
  fecha_visita_propuesta?: string | null;
  fecha_visita_confirmada?: string | null;
  estado: 'pendiente' | 'pendiente_visita' | 'visita_programada' | 'contrato_generado' | 'aceptada' | 'rechazada';
  fecha_solicitud?: string;
  contrato?: Contrato | null;
}

export interface Contrato {
  id: number;
  numero_contrato?: string | null;
  solicitud_id: number;
  fecha_inicio: string;
  fecha_fin: string;
  precio_acordado: number;
  estado: 'activo' | 'finalizado' | 'cancelado';
  fecha_creacion?: string;
  trabaja?: boolean | null;
  empresa?: string | null;
  cargo?: string | null;
  ingreso_mensual?: number | null;
  fiador_nombre?: string | null;
  fiador_cedula?: string | null;
  fiador_telefono?: string | null;
  clausulas_adicionales?: string | null;
}

export interface MensajeMarketing {
  id: number;
  rol: 'usuario' | 'asistente';
  contenido: string;
  datos_extraidos?: Record<string, unknown>;
  fecha_creacion: string;
}

export interface ResultadoMarketing {
  id: number;
  descripcion: string;
  precio_sugerido?: number | null;
  precio_minimo?: number | null;
  precio_maximo?: number | null;
  moneda: string;
  datos_usados?: Record<string, unknown>;
  metadatos_calculo?: Record<string, unknown>;
  fecha_creacion: string;
}

export interface ConversacionMarketing {
  id: number;
  propiedad_id?: number | null;
  estado: 'recopilando' | 'lista' | 'generada' | 'cerrada';
  datos_recopilados: Record<string, unknown>;
  mensajes: MensajeMarketing[];
  resultados: ResultadoMarketing[];
  fecha_creacion: string;
  fecha_actualizacion: string;
}

export interface ApiEnvelope<T> {
  success: boolean;
  message?: string;
  data: T;
  error?: { message?: string; details?: unknown };
}
