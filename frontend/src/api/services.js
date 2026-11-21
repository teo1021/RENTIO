import { request } from './client.js';

const json = (method, body, timeout) => ({ method, body, timeout });

export const authApi = {
  login: (correo, contrasena) => request('/usuarios/login', json('POST', { correo, contrasena })),
  register: (payload) => request('/usuarios/registro', json('POST', payload)),
  profile: () => request('/usuarios/perfil'),
  updateProfile: (payload) => request('/usuarios/perfil', json('PATCH', payload)),
};

export const propertiesApi = {
  listPublic: (params = {}) => request(`/propiedades${new URLSearchParams(params).size ? `?${new URLSearchParams(params)}` : ''}`),
  mine: () => request('/propiedades/mis-propiedades'),
  get: (id) => request(`/propiedades/${id}`),
  create: (payload) => request('/propiedades', json('POST', payload)),
  update: (id, payload) => request(`/propiedades/${id}`, json('PATCH', payload)),
  remove: (id) => request(`/propiedades/${id}`, { method: 'DELETE' }),
  updateFeatures: (id, caracteristicas_ids) => request(`/propiedades/${id}/caracteristicas`, json('PATCH', { caracteristicas_ids })),
  uploadImages: (id, files) => {
    const form = new FormData();
    files.forEach((file) => form.append('imagenes', file));
    return request(`/propiedades/${id}/imagenes`, { method: 'POST', body: form });
  },
  deleteImage: (id, imageId) => request(`/propiedades/${id}/imagenes/${imageId}`, { method: 'DELETE' }),
};

export const rentalsApi = {
  mine: () => request('/arriendos/mis-solicitudes'),
  received: () => request('/arriendos/solicitudes-recibidas'),
  contracts: () => request('/arriendos/contratos'),
  request: (payload) => request('/arriendos/solicitar', json('POST', payload)),
  respondVisit: (id, payload) => request(`/arriendos/${id}/responder-visita`, json('PATCH', payload)),
  createContract: (id, payload) => request(`/arriendos/${id}/generar-contrato`, json('POST', payload)),
  respond: (id, payload) => request(`/arriendos/${id}/responder`, json('PATCH', payload)),
};

export const catalogsApi = {
  neighborhoods: () => request('/barrios'),
  createNeighborhood: (payload) => request('/barrios', json('POST', payload)),
  updateNeighborhood: (id, payload) => request(`/barrios/${id}`, json('PATCH', payload)),
  features: () => request('/caracteristicas'),
  createFeature: (payload) => request('/caracteristicas', json('POST', payload)),
};

export const adminApi = {
  users: () => request('/admin/usuarios'),
  properties: () => request('/propiedades/administracion'),
  changeRole: (id, rol) => request(`/admin/usuarios/${id}/rol`, json('PATCH', { rol })),
};

export const marketingApi = {
  conversations: () => request('/ia/conversaciones'),
  conversation: (id) => request(`/ia/conversaciones/${id}`),
  createConversation: () => request('/ia/conversaciones', json('POST', {})),
  updateDraft: (id, datos_recopilados) => request(`/ia/conversaciones/${id}`, json('PATCH', { datos_recopilados })),
  sendMessage: (id, mensaje) => request(`/ia/conversaciones/${id}/mensajes`, json('POST', { mensaje }, 50000)),
  createProperty: (id, payload, files = []) => {
    const form = new FormData();
    form.append('datos', JSON.stringify(payload));
    files.forEach((file) => form.append('imagenes', file));
    return request(`/ia/conversaciones/${id}/crear-propiedad`, { method: 'POST', body: form, timeout: 50000 });
  },
  apply: (id) => request(`/ia/conversaciones/${id}/aplicar`, json('POST', {})),
  generateDescription: (payload) => request('/ia/generar-descripcion', json('POST', payload, 50000)),
  suggestPrice: (payload) => request('/ia/sugerir-precio', json('POST', payload, 50000)),
  marketAnalysis: (payload) => request('/ia/analisis-mercado', json('POST', payload, 50000)),
  improveTitle: (payload) => request('/ia/mejorar-titulo', json('POST', payload, 50000)),
  extractPropertyData: (payload) => request('/ia/extraer-datos-propiedad', json('POST', payload, 50000)),
  textSearch: (payload) => request('/ia/busqueda-texto', json('POST', payload, 50000)),
};
