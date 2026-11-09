import { api } from './client';
import type {
  ApiEnvelope, Barrio, Caracteristica, Contrato, ConversacionMarketing,
  ImagenPropiedad, Propiedad, SolicitudArriendo, Usuario,
} from '../types';

async function data<T>(promise: Promise<{ data: ApiEnvelope<T> }>): Promise<T> {
  const response = await promise;
  return response.data.data;
}

export const authApi = {
  login: (correo: string, contrasena: string) => data<{ token: string; usuario: Usuario }>(
    api.post('/usuarios/login', { correo, contrasena }),
  ),
  register: (payload: { correo: string; contrasena: string; rol: 'arrendatario' | 'propietario'; nombre?: string; apellido?: string }) =>
    data<Usuario>(api.post('/usuarios/registro', payload)),
  profile: () => data<Usuario>(api.get('/usuarios/perfil')),
  updateProfile: (payload: Partial<NonNullable<Usuario['perfil']>>) => data<Usuario>(api.patch('/usuarios/perfil', payload)),
};

export const propertiesApi = {
  listPublic: (params?: Record<string, string | number | undefined>) =>
    data<Propiedad[]>(api.get('/propiedades', { params })),
  mine: () => data<Propiedad[]>(api.get('/propiedades/mis-propiedades')),
  get: (id: number) => data<Propiedad>(api.get(`/propiedades/${id}`)),
  create: (payload: Record<string, unknown>) => data<Propiedad>(api.post('/propiedades', payload)),
  update: (id: number, payload: Record<string, unknown>) => data<Propiedad>(api.patch(`/propiedades/${id}`, payload)),
  remove: (id: number) => data<null>(api.delete(`/propiedades/${id}`)),
  updateFeatures: (id: number, caracteristicas_ids: number[]) => data<Propiedad>(api.patch(`/propiedades/${id}/caracteristicas`, { caracteristicas_ids })),
  uploadImages: async (id: number, files: File[]) => {
    const formData = new FormData();
    files.forEach((file) => formData.append('imagenes', file));
    return data<ImagenPropiedad[]>(api.post(`/propiedades/${id}/imagenes`, formData, {
      headers: { 'Content-Type': undefined },
    }));
  },
  deleteImage: (id: number, imageId: number) => data<ImagenPropiedad[]>(api.delete(`/propiedades/${id}/imagenes/${imageId}`)),
};

export const rentalsApi = {
  mine: () => data<SolicitudArriendo[]>(api.get('/arriendos/mis-solicitudes')),
  received: () => data<SolicitudArriendo[]>(api.get('/arriendos/solicitudes-recibidas')),
  contracts: () => data<Contrato[]>(api.get('/arriendos/contratos')),
  request: (propiedad_id: number, mensaje?: string) => data<SolicitudArriendo>(api.post('/arriendos/solicitar', { propiedad_id, mensaje })),
  respond: (id: number, payload: { estado: 'aceptada' | 'rechazada'; fecha_inicio?: string; fecha_fin?: string; precio_acordado?: number }) =>
    data<SolicitudArriendo>(api.patch(`/arriendos/${id}/responder`, payload)),
};

export const catalogsApi = {
  neighborhoods: () => data<Barrio[]>(api.get('/barrios')),
  createNeighborhood: (payload: { nombre: string; comuna: string; zona: string }) => data<Barrio>(api.post('/barrios', payload)),
  features: () => data<Caracteristica[]>(api.get('/caracteristicas')),
  createFeature: (payload: { nombre: string; icono?: string }) => data<Caracteristica>(api.post('/caracteristicas', payload)),
};

export const adminApi = {
  users: () => data<Usuario[]>(api.get('/admin/usuarios')),
  changeRole: (id: number, rol: Usuario['rol']) => data<Usuario>(api.patch(`/admin/usuarios/${id}/rol`, { rol })),
};

export const marketingApi = {
  conversations: () => data<ConversacionMarketing[]>(api.get('/ia/conversaciones')),
  conversation: (id: number) => data<ConversacionMarketing>(api.get(`/ia/conversaciones/${id}`)),
  createConversation: (propiedad_id?: number) => data<ConversacionMarketing>(api.post('/ia/conversaciones', propiedad_id ? { propiedad_id } : {})),
  createPropertyFromConversation: (id: number, payload: Record<string, unknown>, files: File[] = []) => {
    const formData = new FormData();
    formData.append('datos', JSON.stringify(payload));
    files.forEach((file) => formData.append('imagenes', file));
    return data<Propiedad>(api.post(`/ia/conversaciones/${id}/crear-propiedad`, formData, {
      headers: { 'Content-Type': undefined },
    }));
  },
  sendMessage: (id: number, mensaje: string) => data<{
    conversacion_id: number; datos_actualizados: Record<string, unknown>; datos_faltantes: string[];
    es_completo: boolean; respuesta_asistente: string; resultado_generado: Record<string, unknown> | null;
  }>(api.post(`/ia/conversaciones/${id}/mensajes`, { mensaje }, { timeout: 50000 })),
  apply: async (id: number): Promise<void> => {
    // Este endpoint responde con success/message, sin una propiedad data.
    await api.post(`/ia/conversaciones/${id}/aplicar`);
  },
  generateDescription: (payload: Record<string, unknown>) => data<Record<string, unknown>>(api.post('/ia/generar-descripcion', payload, { timeout: 50000 })),
  suggestPrice: (payload: Record<string, unknown>) => data<Record<string, unknown>>(api.post('/ia/sugerir-precio', payload, { timeout: 50000 })),
  marketAnalysis: (payload: Record<string, unknown>) => data<Record<string, unknown>>(api.post('/ia/analisis-mercado', payload, { timeout: 50000 })),
  improveTitle: (payload: Record<string, unknown>) => data<Record<string, unknown>>(api.post('/ia/mejorar-titulo', payload, { timeout: 50000 })),
  extraerDatosPropiedad: (payload: Record<string, unknown>) => data<Record<string, unknown>>(api.post('/ia/extraer-datos-propiedad', payload)),
  busquedaTexto: (payload: Record<string, unknown>) => data<Record<string, unknown>>(api.post('/ia/busqueda-texto', payload)),
};
