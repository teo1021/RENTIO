import { adminApi, propertiesApi, rentalsApi } from '../api/services.js';
import { apiError } from '../api/client.js';
import { getUser } from '../store/auth.js';
import { alert, escapeHtml, fullName, money, statusBadge } from '../utils/dom.js';

export async function renderDashboard() {
  const user = getUser();
  const role = user.rol;
  let properties = [];
  let requests = [];
  let contracts = [];
  let users = [];
  let error = '';

  try {
    if (role === 'propietario') {
      [properties, requests, contracts] = await Promise.all([
        propertiesApi.mine(), rentalsApi.received(), rentalsApi.contracts(),
      ]);
    } else if (role === 'arrendatario') {
      [properties, requests, contracts] = await Promise.all([
        propertiesApi.listPublic(), rentalsApi.mine(), rentalsApi.contracts(),
      ]);
      properties = properties.filter((item) => item.estado === 'disponible');
    } else {
      [properties, users] = await Promise.all([adminApi.properties(), adminApi.users()]);
    }
  } catch (cause) {
    error = apiError(cause, 'No fue posible cargar el resumen.');
  }

  const pending = requests.filter((item) => ['pendiente', 'pendiente_visita'].includes(item.estado)).length;
  const activeContracts = contracts.filter((item) => item.estado === 'activo');
  const stats = role === 'propietario'
    ? [
      ['Mis propiedades', properties.length],
      ['Solicitudes pendientes', pending],
      ['Contratos activos', activeContracts.length],
      ['Canon activo', money(activeContracts.reduce((sum, item) => sum + Number(item.precio_acordado || 0), 0))],
    ]
    : role === 'arrendatario'
      ? [['Inmuebles disponibles', properties.length], ['Mis solicitudes', requests.length], ['Pendientes', pending], ['Contratos activos', activeContracts.length]]
      : [['Propiedades', properties.length], ['Usuarios', users.length], ['Arrendadas', properties.filter((item) => item.estado === 'arrendada').length], ['Inactivas', properties.filter((item) => item.estado === 'inactiva').length]];

  const recent = role === 'admin'
    ? properties.slice(0, 6).map((property) => `<tr><td>${escapeHtml(property.titulo)}</td><td>${escapeHtml(property.barrio?.nombre || property.direccion)}</td><td>${statusBadge(property.estado)}</td><td>${money(property.precio_mensual)}</td></tr>`).join('')
    : requests.slice(0, 6).map((request) => `<tr><td>${escapeHtml(request.propiedad?.titulo || `Solicitud #${request.id}`)}</td><td>${escapeHtml(role === 'propietario' ? request.arrendatario?.correo : request.fecha_solicitud || '')}</td><td>${statusBadge(request.estado)}</td><td>${money(request.propiedad?.precio_mensual)}</td></tr>`).join('');
  const columns = role === 'admin'
    ? '<th>Propiedad</th><th>Ubicación</th><th>Estado</th><th>Canon</th>'
    : '<th>Propiedad</th><th>Solicitante / fecha</th><th>Estado</th><th>Canon</th>';

  return `<div class="page-stack">
    <div class="page-heading"><div><p class="text-uppercase small fw-semibold text-secondary mb-1">Panel general</p><h1>${role === 'propietario' ? 'Administra con claridad' : role === 'arrendatario' ? 'Encuentra tu próximo hogar' : 'Todo bajo control'}</h1><p>Hola, ${escapeHtml(fullName(user))}. Resumen de tu espacio RENTIO.</p></div></div>
    ${alert(error)}
    <section class="stat-grid">${stats.map(([label, value]) => `<div class="stat-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join('')}</section>
    <section class="panel">
      <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div><h2 class="h5 mb-1">${role === 'admin' ? 'Inventario reciente' : 'Solicitudes recientes'}</h2><p class="small text-secondary mb-0">Datos consultados desde RENTIO.</p></div>
      </div>
      ${recent ? `<div class="table-responsive"><table class="table table-compact"><thead><tr>${columns}</tr></thead><tbody>${recent}</tbody></table></div>` : '<div class="text-secondary py-4">No hay actividad para mostrar.</div>'}
    </section>
  </div>`;
}
