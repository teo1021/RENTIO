export function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

export function money(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return 'Sin definir';
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(amount);
}

export function dateLabel(value) {
  if (!value) return 'Sin fecha';
  const date = /^\d{4}-\d{2}-\d{2}$/.test(value)
    ? new Date(`${value}T12:00:00`)
    : new Date(value);
  return Number.isNaN(date.getTime())
    ? escapeHtml(value)
    : new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' }).format(date);
}

export function fullName(user) {
  const profile = user?.perfil || {};
  return [profile.nombre, profile.apellido].filter(Boolean).join(' ').trim()
    || user?.correo
    || 'Usuario';
}

export function roleLabel(role) {
  return ({
    admin: 'Administrador',
    propietario: 'Propietario',
    arrendatario: 'Arrendatario',
  })[role] || role || 'Sin rol';
}

export function statusBadge(value) {
  const labels = {
    disponible: 'Disponible',
    arrendada: 'Arrendada',
    inactiva: 'Inactiva',
    pendiente: 'Pendiente',
    pendiente_visita: 'Esperando visita',
    visita_programada: 'Visita programada',
    contrato_generado: 'Contrato generado',
    aceptada: 'Aceptada',
    rechazada: 'Rechazada',
    activo: 'Activo',
    finalizado: 'Finalizado',
    cancelado: 'Cancelado',
    recopilando: 'En progreso',
    lista: 'Lista para publicar',
    generada: 'Publicada',
    cerrada: 'Cerrada',
  };
  const tone = ({
    disponible: 'success',
    visita_programada: 'primary',
    contrato_generado: 'success',
    aceptada: 'success',
    activo: 'success',
    lista: 'success',
    generada: 'info',
    pendiente: 'warning',
    pendiente_visita: 'warning',
    rechazada: 'danger',
    cancelado: 'danger',
  })[value] || 'secondary';
  return `<span class="badge text-bg-${tone}">${escapeHtml(labels[value] || value || 'Sin estado')}</span>`;
}

export function alert(message, variant = 'danger', id = '') {
  if (!message) return '';
  return `<div${id ? ` id="${escapeHtml(id)}"` : ''} class="alert alert-${variant} alert-dismissible fade show" role="alert">
    ${escapeHtml(message)}
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
  </div>`;
}

export function emptyState(message) {
  return `<div class="empty-state text-center py-5"><p class="text-secondary mb-0">${escapeHtml(message)}</p></div>`;
}

export function tomorrowDate() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export function listen(container, eventName, selector, handler) {
  const listener = (event) => {
    const target = event.target.closest(selector);
    if (target && container.contains(target)) handler(event, target);
  };
  container.addEventListener(eventName, listener);
  return () => container.removeEventListener(eventName, listener);
}

export function formObject(form) {
  return Object.fromEntries(new FormData(form).entries());
}

export function setBusy(button, busy, label) {
  if (!button) return;
  button.disabled = busy;
  if (busy) {
    button.dataset.label = button.innerHTML;
    button.innerHTML = `<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>${escapeHtml(label)}`;
  } else if (button.dataset.label) {
    button.innerHTML = button.dataset.label;
    delete button.dataset.label;
  }
}
