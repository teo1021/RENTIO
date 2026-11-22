import { Modal } from 'bootstrap';
import { catalogsApi } from '../api/services.js';
import { apiError } from '../api/client.js';
import { alert, escapeHtml, listen } from '../utils/dom.js';

let barrios = [];
let features = [];
let activeTab = 'barrios';

export async function renderCatalogs() {
  let error = '';
  try {
    [barrios, features] = await Promise.all([catalogsApi.neighborhoods(), catalogsApi.features()]);
  } catch (cause) {
    error = apiError(cause, 'No fue posible cargar los catálogos.');
  }
  return `<div class="page-stack">
    <div class="page-heading"><div><p class="text-uppercase small fw-semibold text-secondary mb-1">Configuración</p><h1>Barrios y características</h1></div></div>
    ${alert(error)}
    <ul class="nav nav-tabs" role="tablist">
      <li class="nav-item"><button class="nav-link ${activeTab === 'barrios' ? 'active' : ''}" type="button" data-tab="barrios">Barrios (${barrios.length})</button></li>
      <li class="nav-item"><button class="nav-link ${activeTab === 'caracteristicas' ? 'active' : ''}" type="button" data-tab="caracteristicas">Características (${features.length})</button></li>
    </ul>
    <div class="panel" data-catalog-panel>${renderActivePanel()}</div>
    <div data-catalog-feedback></div>
    ${neighborhoodModal()}
  </div>`;
}

function renderActivePanel() {
  if (activeTab === 'barrios') {
    return `<div class="d-flex justify-content-between align-items-center gap-2 mb-3"><h2 class="h5 mb-0">Barrios disponibles</h2><button class="btn btn-primary btn-sm" data-bs-toggle="modal" data-bs-target="#neighborhood-modal">Registrar barrio</button></div>
      ${barrios.length ? barrios.map((item) => `<div class="catalog-row"><div><strong>${escapeHtml(item.nombre)}</strong><div class="small text-secondary">${escapeHtml(item.comuna)} · ${escapeHtml(item.zona)}</div></div><button class="btn btn-outline-secondary btn-sm" data-edit-neighborhood="${item.id}">Editar</button></div>`).join('') : '<p class="text-secondary">No hay barrios disponibles.</p>'}`;
  }
  return `<div class="mb-3"><h2 class="h5 mb-1">Características</h2><p class="small text-secondary">Amenidades que pueden asociarse a las propiedades.</p></div>
    <form id="feature-form" class="row g-2 mb-4"><div class="col-md-6"><label class="form-label">Nombre<input class="form-control" name="nombre" required minlength="2" maxlength="100"></label></div><div class="col-md-4"><label class="form-label">Icono (opcional)<input class="form-control" name="icono" maxlength="100"></label></div><div class="col-md-2 d-flex align-items-end"><button class="btn btn-primary w-100" type="submit">Agregar</button></div></form>
    <div class="d-flex flex-wrap gap-2">${features.map((item) => `<span class="badge rounded-pill text-bg-light border text-dark p-2">${escapeHtml(item.nombre)}</span>`).join('') || '<span class="text-secondary">No hay características.</span>'}</div>`;
}

function neighborhoodModal(item = null) {
  return `<div class="modal fade" id="neighborhood-modal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog"><div class="modal-content">
      <form id="neighborhood-form" data-id="${item?.id || ''}">
        <div class="modal-header"><h2 class="modal-title fs-5">${item ? 'Editar barrio' : 'Registrar barrio'}</h2><button class="btn-close" type="button" data-bs-dismiss="modal" aria-label="Cerrar"></button></div>
        <div class="modal-body vstack gap-3">
          <label class="form-label">Nombre<input class="form-control" name="nombre" required minlength="2" maxlength="100" value="${escapeHtml(item?.nombre || '')}"></label>
          <label class="form-label">Comuna<input class="form-control" name="comuna" required minlength="2" maxlength="100" value="${escapeHtml(item?.comuna || '')}"></label>
          <label class="form-label">Zona<input class="form-control" name="zona" required minlength="2" maxlength="100" value="${escapeHtml(item?.zona || '')}"></label>
        </div>
        <div class="modal-footer"><button class="btn btn-outline-secondary" type="button" data-bs-dismiss="modal">Cancelar</button><button class="btn btn-primary" type="submit">Guardar</button></div>
      </form>
    </div></div>
  </div>`;
}

function normalize(value) {
  return value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').trim().toLowerCase();
}

export function mount(root) {
  listen(root, 'click', 'button[data-tab]', (_event, button) => {
    activeTab = button.dataset.tab;
    root.querySelector('[data-catalog-panel]').innerHTML = renderActivePanel();
    root.querySelectorAll('button[data-tab]').forEach((tab) => tab.classList.toggle('active', tab.dataset.tab === activeTab));
  });

  listen(root, 'click', 'button[data-edit-neighborhood]', (_event, button) => {
    const item = barrios.find((entry) => entry.id === Number(button.dataset.editNeighborhood));
    if (!item) return;
    const old = root.querySelector('#neighborhood-modal');
    old.remove();
    root.insertAdjacentHTML('beforeend', neighborhoodModal(item));
    Modal.getOrCreateInstance(root.querySelector('#neighborhood-modal')).show();
  });

  listen(root, 'submit', 'form#neighborhood-form', async (event, form) => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(form));
    if (barrios.some((item) => item.id !== Number(form.dataset.id) && normalize(item.nombre) === normalize(values.nombre) && normalize(item.comuna) === normalize(values.comuna))) {
      root.querySelector('[data-catalog-feedback]').innerHTML = alert('Ya existe un barrio con ese nombre en la comuna indicada.');
      return;
    }
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      const saved = form.dataset.id
        ? await catalogsApi.updateNeighborhood(Number(form.dataset.id), values)
        : await catalogsApi.createNeighborhood(values);
      barrios = form.dataset.id
        ? barrios.map((item) => item.id === saved.id ? saved : item)
        : [...barrios, saved].sort((a, b) => a.comuna.localeCompare(b.comuna) || a.nombre.localeCompare(b.nombre));
      root.querySelector('[data-catalog-panel]').innerHTML = renderActivePanel();
      root.querySelector('[data-catalog-feedback]').innerHTML = alert('Barrio guardado.', 'success');
      Modal.getInstance(root.querySelector('#neighborhood-modal'))?.hide();
    } catch (error) {
      root.querySelector('[data-catalog-feedback]').innerHTML = alert(apiError(error, 'No fue posible guardar el barrio.'));
    } finally {
      button.disabled = false;
    }
  });

  listen(root, 'submit', 'form#feature-form', async (event, form) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    if (features.some((item) => normalize(item.nombre) === normalize(data.nombre))) {
      root.querySelector('[data-catalog-feedback]').innerHTML = alert('Esa característica ya está registrada.');
      return;
    }
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    try {
      const item = await catalogsApi.createFeature({ nombre: data.nombre.trim(), icono: data.icono.trim() || undefined });
      features = [...features, item].sort((a, b) => a.nombre.localeCompare(b.nombre));
      root.querySelector('[data-catalog-panel]').innerHTML = renderActivePanel();
      root.querySelector('[data-catalog-feedback]').innerHTML = alert('Característica agregada.', 'success');
    } catch (error) {
      root.querySelector('[data-catalog-feedback]').innerHTML = alert(apiError(error, 'No fue posible guardar la característica.'));
    } finally {
      button.disabled = false;
    }
  });
}
