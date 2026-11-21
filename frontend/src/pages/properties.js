import { Modal } from 'bootstrap';
import { adminApi, catalogsApi, propertiesApi, rentalsApi } from '../api/services.js';
import { apiError } from '../api/client.js';
import { getUser } from '../store/auth.js';
import { alert, emptyState, escapeHtml, listen, money, statusBadge, tomorrowDate } from '../utils/dom.js';
import { navigate } from '../router.js';

let items = [];
let neighborhoods = [];
let features = [];
let search = '';
let statusFilter = 'todos';
let typeFilter = 'todos';

export async function renderProperties() {
  const user = getUser();
  let error = '';
  try {
    const propertyRequest = user.rol === 'propietario'
      ? propertiesApi.mine()
      : user.rol === 'admin'
        ? adminApi.properties()
        : propertiesApi.listPublic();
    [items, neighborhoods, features] = await Promise.all([
      propertyRequest, catalogsApi.neighborhoods(), catalogsApi.features(),
    ]);
  } catch (cause) {
    error = apiError(cause, 'No fue posible cargar el inventario.');
    items = [];
  }
  search = '';
  statusFilter = 'todos';
  typeFilter = 'todos';
  const owner = user.rol === 'propietario';
  return `<div class="page-stack">
    <div class="page-heading"><div><p class="text-uppercase small fw-semibold text-secondary mb-1">${user.rol === 'arrendatario' ? 'Explorar inmuebles' : 'Gestión inmobiliaria'}</p><h1>${owner ? 'Mis propiedades' : user.rol === 'admin' ? 'Inventario de propiedades' : 'Encuentra tu próximo lugar'}</h1><p>${owner ? 'Consulta y administra tus inmuebles.' : 'Explora opciones disponibles y consulta su información completa.'}</p></div>${owner ? '<button class="btn btn-primary" type="button" data-action="new-property">Nueva propiedad</button>' : ''}</div>
    <div data-property-feedback>${alert(error)}</div>
    <section class="panel">
      <div class="row g-2 align-items-end">
        <label class="col-md-6 form-label">Buscar inmueble<input class="form-control" id="property-search" placeholder="Título, dirección o barrio"></label>
        <label class="col-md-3 form-label">Tipo<select class="form-select" id="property-type"><option value="todos">Todos los tipos</option>${propertyTypes().map(([value, label]) => `<option value="${value}">${label}</option>`).join('')}</select></label>
        ${user.rol !== 'arrendatario' ? `<label class="col-md-3 form-label">Estado<select class="form-select" id="property-status"><option value="todos">Todos</option><option value="disponible">Disponible</option><option value="arrendada">Arrendada</option><option value="inactiva">Inactiva</option></select></label>` : ''}
      </div>
    </section>
    <div class="small text-secondary" id="property-count"></div>
    <div class="property-grid" id="property-list"></div>
    <div id="property-modal-host"></div>
  </div>`;
}

function propertyTypes() {
  return [
    ['apartamento', 'Apartamento'], ['casa', 'Casa'], ['habitacion', 'Habitación'],
    ['apartaestudio', 'Apartaestudio'], ['local_comercial', 'Local comercial'],
    ['oficina', 'Oficina'], ['bodega', 'Bodega'], ['finca', 'Finca'],
  ];
}

function visibleItems() {
  const user = getUser();
  const query = search.trim().toLocaleLowerCase();
  return items.filter((item) => {
    const searchable = [item.titulo, item.direccion, item.barrio?.nombre, item.descripcion]
      .filter(Boolean).join(' ').toLocaleLowerCase();
    return (!query || searchable.includes(query))
      && (typeFilter === 'todos' || item.tipo === typeFilter)
      && (user.rol === 'arrendatario' ? item.estado === 'disponible' : statusFilter === 'todos' || item.estado === statusFilter);
  });
}

function drawList(root) {
  const list = root.querySelector('#property-list');
  if (!list) return;
  const visible = visibleItems();
  root.querySelector('#property-count').textContent = `${visible.length} inmueble${visible.length === 1 ? '' : 's'}`;
  if (!visible.length) {
    list.innerHTML = `<div class="panel w-100">${emptyState('No hay propiedades para los filtros seleccionados.')}${getUser().rol === 'propietario' ? '<div class="text-center pb-3"><button class="btn btn-primary" data-action="new-property">Registrar propiedad</button></div>' : ''}</div>`;
    return;
  }
  const canManage = ['propietario', 'admin'].includes(getUser().rol);
  list.innerHTML = visible.map((item) => {
    const image = item.imagenes?.[0]?.url;
    return `<article class="property-card">
      ${image ? `<img class="property-photo" src="${escapeHtml(image)}" alt="${escapeHtml(item.titulo)}">` : '<div class="property-placeholder" aria-hidden="true">⌂</div>'}
      <div class="property-card-body">
        ${canManage ? `<div class="property-actions-top"><button class="btn btn-outline-secondary btn-sm" data-edit-property="${item.id}">Editar</button><button class="btn btn-outline-danger btn-sm" data-delete-property="${item.id}">Eliminar</button></div>` : ''}
        <div class="d-flex justify-content-between align-items-center gap-2 mb-2"><span class="small text-secondary text-capitalize">${escapeHtml(item.tipo)}</span>${statusBadge(item.estado)}</div>
        <h2 class="h5 mb-1">${escapeHtml(item.titulo)}</h2>
        <p class="small text-secondary mb-2">${escapeHtml(item.barrio?.nombre || item.direccion)}</p>
        <div class="property-facts mb-3"><span>${escapeHtml(item.habitaciones)} hab.</span><span>${escapeHtml(item.banos)} baños</span><span>${item.area_m2 ? `${escapeHtml(item.area_m2)} m²` : 'Área no reportada'}</span></div>
        <div class="d-flex justify-content-between align-items-center"><strong>${money(item.precio_mensual)} <span class="small fw-normal text-secondary">/ mes</span></strong><a class="btn btn-primary btn-sm" href="/propiedades/${item.id}" data-link>Ver detalle</a></div>
      </div>
    </article>`;
  }).join('');
}

export async function renderPropertyDetail(id) {
  let property;
  let error = '';
  try {
    [property, neighborhoods, features] = await Promise.all([
      propertiesApi.get(Number(id)),
      catalogsApi.neighborhoods(),
      catalogsApi.features(),
    ]);
  } catch (cause) {
    error = apiError(cause, 'No fue posible consultar el inmueble.');
  }
  if (!property) return `<div class="page-stack">${alert(error)}<a href="/propiedades" data-link>Volver a propiedades</a></div>`;
  const gallery = property.imagenes?.length
    ? `<div class="property-gallery mb-3">${property.imagenes.map((image) => `<a href="${escapeHtml(image.url)}" target="_blank" rel="noopener"><img src="${escapeHtml(image.url)}" alt="Fotografía de ${escapeHtml(property.titulo)}"></a>`).join('')}</div>`
    : '';
  const canManage = ['propietario', 'admin'].includes(getUser()?.rol);
  const isTenant = getUser()?.rol === 'arrendatario';
  return `<div class="page-stack">
    <a class="link-secondary" href="/propiedades" data-link>← Volver a propiedades</a>
    ${alert(error)}
    <section class="panel">
      <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3">
        <div><p class="small text-secondary mb-1">${escapeHtml(property.barrio?.nombre || 'Medellín')} · <span class="text-capitalize">${escapeHtml(property.tipo)}</span></p><h1 class="h3 mb-2">${escapeHtml(property.titulo)}</h1><p class="mb-0 text-secondary">${escapeHtml(property.direccion)}</p></div>
        ${canManage ? `<div class="d-flex gap-2"><button class="btn btn-outline-primary" data-edit-property="${property.id}">Editar</button><button class="btn btn-outline-danger" data-delete-property="${property.id}">Eliminar</button></div>` : ''}
      </div>
      ${property.imagenes?.[0] ? `<img class="property-detail-photo mb-3" src="${escapeHtml(property.imagenes[0].url)}" alt="${escapeHtml(property.titulo)}">` : '<div class="property-placeholder rounded mb-3">⌂</div>'}
      ${gallery}
      <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3"><strong class="h4 mb-0">${money(property.precio_mensual)} <span class="fs-6 fw-normal text-secondary">mensuales</span></strong>${statusBadge(property.estado)}</div>
      <p>${escapeHtml(property.descripcion || 'Sin descripción disponible.')}</p>
      <div class="row g-3 mb-3"><div class="col-sm-3"><span class="small text-secondary">Habitaciones</span><div class="fw-semibold">${escapeHtml(property.habitaciones)}</div></div><div class="col-sm-3"><span class="small text-secondary">Baños</span><div class="fw-semibold">${escapeHtml(property.banos)}</div></div><div class="col-sm-3"><span class="small text-secondary">Área</span><div class="fw-semibold">${property.area_m2 ? `${escapeHtml(property.area_m2)} m²` : 'No reportada'}</div></div><div class="col-sm-3"><span class="small text-secondary">Estrato</span><div class="fw-semibold">${escapeHtml(property.estrato)}</div></div></div>
      <div class="mb-3"><span class="small text-secondary">Características</span><div class="d-flex flex-wrap gap-2 mt-1">${property.caracteristicas?.map((feature) => `<span class="badge text-bg-light border">${escapeHtml(feature.nombre)}</span>`).join('') || '<span class="text-secondary">Sin características adicionales</span>'}</div></div>
      ${isTenant && property.estado === 'disponible' ? requestForm(property) : ''}
      <div data-detail-feedback></div>
      <div id="property-modal-host"></div>
    </section>
  </div>`;
}

function requestForm(property) {
  return `<form id="request-form" class="vstack gap-3 mt-4">
    <h2 class="h5">Enviar solicitud</h2>
    <input type="hidden" name="propiedad_id" value="${property.id}">
    <div class="row g-2"><label class="col-md-6 form-label">Cédula<input class="form-control" name="cedula_arrendatario" required minlength="5" maxlength="20"></label><label class="col-md-6 form-label">Teléfono<input class="form-control" name="telefono_arrendatario" required minlength="7" maxlength="20"></label></div>
    <label class="form-label">Fecha propuesta para la visita<input class="form-control" type="date" name="fecha_visita_propuesta" min="${tomorrowDate()}" required></label>
    <label class="form-label">Mensaje (opcional)<textarea class="form-control" name="mensaje" rows="3" maxlength="1000"></textarea></label>
    <button class="btn btn-primary align-self-start" type="submit">Enviar solicitud</button>
  </form>`;
}

function editModal(property) {
  const form = {
    titulo: property.titulo || '',
    descripcion: property.descripcion || '',
    precio_mensual: property.precio_mensual ?? '',
    direccion: property.direccion || '',
    estrato: property.estrato ?? 4,
    area_m2: property.area_m2 ?? '',
    habitaciones: property.habitaciones ?? 1,
    banos: property.banos ?? 1,
    tipo: property.tipo || 'apartamento',
    barrio_id: property.barrio_id || '',
  };
  return `<div class="modal fade" id="property-edit-modal" tabindex="-1" aria-hidden="true"><div class="modal-dialog modal-lg modal-dialog-scrollable"><div class="modal-content">
    <form id="property-edit-form" data-id="${property.id}">
      <div class="modal-header"><h2 class="modal-title fs-5">Editar propiedad</h2><button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Cerrar"></button></div>
      <div class="modal-body vstack gap-3">
        <label class="form-label">Título<input class="form-control" name="titulo" required minlength="5" maxlength="255" value="${escapeHtml(form.titulo)}"></label>
        <label class="form-label">Descripción<textarea class="form-control" name="descripcion" rows="3" maxlength="5000">${escapeHtml(form.descripcion)}</textarea></label>
        <div class="row g-2">
          <label class="col-md-6 form-label">Canon mensual<input class="form-control" name="precio_mensual" type="number" min="0" required value="${escapeHtml(form.precio_mensual)}"></label>
          <label class="col-md-6 form-label">Dirección<input class="form-control" name="direccion" minlength="5" maxlength="500" required value="${escapeHtml(form.direccion)}"></label>
          <label class="col-md-4 form-label">Tipo<select class="form-select" name="tipo">${propertyTypes().map(([value, label]) => `<option value="${value}" ${form.tipo === value ? 'selected' : ''}>${label}</option>`).join('')}</select></label>
          <label class="col-md-4 form-label">Estrato<select class="form-select" name="estrato">${[1, 2, 3, 4, 5, 6].map((value) => `<option value="${value}" ${Number(form.estrato) === value ? 'selected' : ''}>${value}</option>`).join('')}</select></label>
          <label class="col-md-4 form-label">Barrio<select class="form-select" name="barrio_id"><option value="">Sin especificar</option>${neighborhoods.map((item) => `<option value="${item.id}" ${String(form.barrio_id) === String(item.id) ? 'selected' : ''}>${escapeHtml(item.nombre)} · ${escapeHtml(item.comuna)}</option>`).join('')}</select></label>
          <label class="col-md-4 form-label">Habitaciones<input class="form-control" name="habitaciones" type="number" min="0" max="50" value="${escapeHtml(form.habitaciones)}"></label>
          <label class="col-md-4 form-label">Baños<input class="form-control" name="banos" type="number" min="0" max="50" value="${escapeHtml(form.banos)}"></label>
          <label class="col-md-4 form-label">Área (m²)<input class="form-control" name="area_m2" type="number" min="1" step=".1" value="${escapeHtml(form.area_m2)}"></label>
          <label class="col-md-4 form-label">Estado<select class="form-select" name="estado">${['disponible', 'arrendada', 'inactiva'].map((value) => `<option value="${value}" ${property.estado === value ? 'selected' : ''}>${value}</option>`).join('')}</select></label>
        </div>
        <div><div class="form-label">Características</div><div class="d-flex flex-wrap gap-2">${features.map((feature) => `<label class="form-check form-check-inline"><input class="form-check-input" type="checkbox" name="caracteristicas_ids" value="${feature.id}" ${property.caracteristicas?.some((selected) => selected.id === feature.id) ? 'checked' : ''}><span class="form-check-label">${escapeHtml(feature.nombre)}</span></label>`).join('')}</div></div>
        <label class="form-label">Agregar fotografías (JPG, PNG o WEBP; hasta 10 en total)<input class="form-control" name="imagenes" type="file" accept="image/jpeg,image/png,image/webp" multiple></label>
        <div class="row g-2">${property.imagenes?.map((image) => `<div class="col-4 col-md-3"><img class="w-100 rounded object-fit-cover" height="90" src="${escapeHtml(image.url)}" alt="Fotografía"><button type="button" class="btn btn-sm btn-outline-danger w-100 mt-1" data-delete-image="${image.id}" data-property-id="${property.id}">Quitar</button></div>`).join('') || ''}</div>
        <div data-edit-feedback></div>
      </div>
      <div class="modal-footer"><button class="btn btn-outline-secondary" type="button" data-bs-dismiss="modal">Cancelar</button><button class="btn btn-primary" type="submit">Guardar cambios</button></div>
    </form>
  </div></div></div>`;
}

async function openEdit(root, propertyId) {
  const property = await propertiesApi.get(Number(propertyId));
  const host = root.querySelector('#property-modal-host');
  host.innerHTML = editModal(property);
  Modal.getOrCreateInstance(host.querySelector('#property-edit-modal')).show();
}

export function mount(root) {
  const detailId = location.pathname.match(/^\/propiedades\/(\d+)/)?.[1];
  if (!detailId) drawList(root);
  root.addEventListener('input', (event) => {
    if (event.target.id === 'property-search') {
      search = event.target.value;
      drawList(root);
    }
  });
  root.addEventListener('change', (event) => {
    if (event.target.id === 'property-status') statusFilter = event.target.value;
    if (event.target.id === 'property-type') typeFilter = event.target.value;
    if (['property-status', 'property-type'].includes(event.target.id)) drawList(root);
  });

  listen(root, 'click', '[data-action="new-property"]', () => navigate('/asistente-ia'));
  listen(root, 'click', '[data-edit-property]', async (_event, button) => {
    try { await openEdit(root, button.dataset.editProperty); }
    catch (error) { root.querySelector('[data-property-feedback],[data-detail-feedback]').innerHTML = alert(apiError(error)); }
  });
  listen(root, 'click', '[data-delete-property]', async (_event, button) => {
    const property = items.find((item) => item.id === Number(button.dataset.deleteProperty));
    if (!window.confirm(`¿Eliminar "${property?.titulo || 'esta propiedad'}"? Esta acción no se puede deshacer.`)) return;
    button.disabled = true;
    try {
      await propertiesApi.remove(button.dataset.deleteProperty);
      if (detailId) navigate('/propiedades', true);
      else {
        items = items.filter((item) => item.id !== Number(button.dataset.deleteProperty));
        drawList(root);
        root.querySelector('[data-property-feedback]').innerHTML = alert('Propiedad eliminada.', 'success');
      }
    } catch (error) {
      button.disabled = false;
      const feedback = root.querySelector('[data-property-feedback],[data-detail-feedback]');
      if (feedback) feedback.innerHTML = alert(apiError(error, 'No fue posible eliminar la propiedad.'));
    }
  });
  listen(root, 'submit', 'form#property-edit-form', async (event, form) => {
    event.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    const data = Object.fromEntries(new FormData(form));
    const featureIds = [...form.querySelectorAll('input[name="caracteristicas_ids"]:checked')].map((input) => Number(input.value));
    const files = [...form.querySelector('input[name="imagenes"]').files];
    if (files.some((file) => !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024)) {
      form.querySelector('[data-edit-feedback]').innerHTML = alert('Usa imágenes JPG, PNG o WEBP de máximo 5 MB cada una.');
      submit.disabled = false;
      return;
    }
    try {
      const current = await propertiesApi.get(Number(form.dataset.id));
      if ((current.imagenes?.length || 0) + files.length > 10) throw new Error('Puedes guardar máximo 10 fotografías por propiedad.');
      const payload = {
        titulo: data.titulo.trim(),
        descripcion: data.descripcion.trim() || null,
        precio_mensual: Number(data.precio_mensual),
        direccion: data.direccion.trim(),
        estrato: Number(data.estrato),
        area_m2: data.area_m2 ? Number(data.area_m2) : null,
        habitaciones: Number(data.habitaciones),
        banos: Number(data.banos),
        tipo: data.tipo,
        estado: data.estado,
        barrio_id: data.barrio_id ? Number(data.barrio_id) : null,
      };
      await propertiesApi.update(Number(form.dataset.id), payload);
      await propertiesApi.updateFeatures(Number(form.dataset.id), featureIds);
      if (files.length) await propertiesApi.uploadImages(Number(form.dataset.id), files);
      Modal.getInstance(root.querySelector('#property-edit-modal'))?.hide();
      if (detailId) navigate(`/propiedades/${detailId}`, true);
      else {
        items = await (getUser().rol === 'admin' ? adminApi.properties() : propertiesApi.mine());
        drawList(root);
        root.querySelector('[data-property-feedback]').innerHTML = alert('Propiedad actualizada.', 'success');
      }
    } catch (error) {
      form.querySelector('[data-edit-feedback]').innerHTML = alert(apiError(error, 'No fue posible guardar los cambios.'));
      submit.disabled = false;
    }
  });
  listen(root, 'click', '[data-delete-image]', async (_event, button) => {
    button.disabled = true;
    try {
      await propertiesApi.deleteImage(button.dataset.propertyId, button.dataset.deleteImage);
      button.closest('.col-4').remove();
    } catch (error) {
      button.disabled = false;
      root.querySelector('[data-edit-feedback]').innerHTML = alert(apiError(error, 'No fue posible quitar la fotografía.'));
    }
  });
  listen(root, 'submit', 'form#request-form', async (event, form) => {
    event.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    const data = Object.fromEntries(new FormData(form));
    data.propiedad_id = Number(data.propiedad_id);
    data.mensaje = data.mensaje.trim() || undefined;
    try {
      await rentalsApi.request(data);
      form.reset();
      root.querySelector('[data-detail-feedback]').innerHTML = alert('Solicitud enviada. Puedes seguir su estado en Solicitudes.', 'success');
    } catch (error) {
      root.querySelector('[data-detail-feedback]').innerHTML = alert(apiError(error, 'No fue posible enviar la solicitud.'));
    } finally {
      submit.disabled = false;
    }
  });
}
