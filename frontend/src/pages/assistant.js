import { authApi, catalogsApi, marketingApi } from '../api/services.js';
import { apiError } from '../api/client.js';
import { getUser } from '../store/auth.js';
import { alert, dateLabel, escapeHtml, listen, money, statusBadge } from '../utils/dom.js';
import { navigate } from '../router.js';

let conversation;
let conversations = [];
let neighborhoods = [];
let selectedFiles = [];
let debounceTimer;
let savePromise;
let pendingSnapshot;
let savedSnapshot = '';
let lastSaveError = '';

const required = ['barrio', 'tipo', 'habitaciones', 'banos', 'direccion', 'estrato', 'precio_mensual'];
const labels = {
  barrio: 'Barrio',
  tipo: 'Tipo de inmueble',
  habitaciones: 'Habitaciones',
  banos: 'Baños',
  direccion: 'Dirección',
  estrato: 'Estrato',
  precio_mensual: 'Canon mensual',
};

export async function renderAssistant() {
  selectedFiles = [];
  pendingSnapshot = null;
  savedSnapshot = '';
  lastSaveError = '';
  try {
    const [existing, catalog] = await Promise.all([
      marketingApi.conversations(),
      catalogsApi.neighborhoods(),
    ]);
    conversations = existing;
    neighborhoods = catalog;
    conversation = existing.find((item) => !item.propiedad_id && ['recopilando', 'lista'].includes(item.estado));
    if (!conversation) {
      conversation = await marketingApi.createConversation();
      conversations = [conversation, ...existing];
    } else {
      conversation = await marketingApi.conversation(conversation.id);
    }
    return `<div class="page-stack">
      <div class="page-heading"><div><p class="text-uppercase small fw-semibold text-secondary mb-1">Asistente RENTIO</p><h1>Registro de propiedad con IA</h1><p>Completa la información, revisa las sugerencias y confirma antes de publicar.</p></div></div>
      <div data-assistant-feedback></div>
      <div class="d-flex flex-wrap justify-content-between align-items-center gap-2"><div>${statusBadge(conversation.estado)} <span class="small text-secondary ms-2">Borrador #${conversation.id}</span></div><div class="save-state" data-save-state role="status">Guardado en RENTIO</div></div>
      <div data-assistant-area>${renderAssistantArea(conversation)}</div>
    </div>`;
  } catch (error) {
    return `<div class="page-stack">${alert(apiError(error, 'No fue posible preparar el asistente de IA.'))}<button class="btn btn-primary" data-action="retry-assistant">Reintentar</button></div>`;
  }
}

function draftFromConversation(source) {
  const data = source?.datos_recopilados || {};
  const latestResult = source?.resultados?.[source.resultados.length - 1];
  return {
    barrio: data.barrio || '',
    barrio_comuna: data.barrio_comuna || '',
    tipo: data.tipo || '',
    habitaciones: data.habitaciones ?? '',
    banos: data.banos ?? '',
    direccion: data.direccion || '',
    estrato: data.estrato ?? '',
    area_m2: data.area_m2 ?? '',
    precio_mensual: data.precio_mensual ?? '',
    parqueadero: typeof data.parqueadero === 'boolean' ? String(data.parqueadero) : '',
    caracteristicas: Array.isArray(data.caracteristicas) ? data.caracteristicas.join(', ') : '',
    titulo: data.titulo || defaultTitle(data),
    descripcion: data.descripcion || latestResult?.descripcion || '',
    canon_confirmado: data.canon_confirmado === true,
    mensaje_borrador: data.mensaje_borrador || '',
  };
}

function defaultTitle(data) {
  return data?.tipo && data?.barrio ? `${capitalize(data.tipo)} en ${data.barrio}` : '';
}

function capitalize(value) {
  const text = String(value || '');
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function renderAssistantArea(source) {
  const data = draftFromConversation(source);
  const messages = source?.mensajes || [];
  const suggested = source?.datos_recopilados?.canon_sugerido;
  const allPresent = required.every((field) => data[field] !== '' && data[field] !== null);
  const confirmed = data.canon_confirmado && Number(data.precio_mensual) > 0;
  const summary = [
    ['Ubicación', Boolean(data.barrio && data.direccion)],
    ['Características', Boolean(data.tipo && data.habitaciones !== '' && data.banos !== '' && data.estrato !== '')],
    ['Canon', Number(data.precio_mensual) > 0 && confirmed],
    ['Publicación', Boolean(data.titulo && data.descripcion)],
  ];
  return `<div class="chat-panel">
    <section class="panel">
      <div class="d-flex justify-content-between align-items-start gap-2 mb-3"><div><h2 class="h5 mb-1">Conversación</h2><p class="small text-secondary mb-0">Cuéntale al asistente cómo es el inmueble.</p></div><span class="badge text-bg-light border text-dark">Registro asistido</span></div>
      <div class="chat-messages mb-3" id="assistant-messages">
        ${messages.length ? messages.map((message) => `<div class="chat-message ${message.rol === 'usuario' ? 'user' : ''}"><div>${escapeHtml(message.contenido)}</div><small class="${message.rol === 'usuario' ? 'text-white-50' : 'text-secondary'}">${dateLabel(message.fecha_creacion)}</small></div>`).join('') : '<p class="text-secondary my-auto">Describe tu propiedad en tus palabras; también puedes completar los campos editables.</p>'}
      </div>
      <form id="assistant-chat-form" class="vstack gap-2">
        <label class="form-label">Mensaje para la IA<textarea class="form-control" rows="2" name="mensaje_borrador" maxlength="4000" placeholder="Ej. Apartamento en Laureles, dos habitaciones...">${escapeHtml(data.mensaje_borrador)}</textarea></label>
        <div class="small text-secondary">El texto sin enviar también se guarda en tu borrador.</div>
        <button class="btn btn-primary align-self-end" type="submit">Enviar a la IA</button>
      </form>
    </section>

    <section class="panel">
      <h2 class="h5 mb-1">Información editable</h2>
      <p class="small text-secondary">Los cambios se guardan automáticamente en el borrador de tu cuenta.</p>
      <div class="row g-2 mb-3">${summary.map(([label, complete]) => `<div class="col-6"><div class="info-block h-100 ${complete ? 'complete' : ''}"><span class="small">${escapeHtml(label)}</span><div class="small fw-semibold">${complete ? 'Completo' : 'Pendiente'}</div></div></div>`).join('')}</div>
      ${suggested ? `<div class="alert alert-info"><div>Referencia del mercado: <strong>${money(suggested)}</strong></div><div class="d-flex gap-2 mt-2"><button class="btn btn-sm btn-primary" type="button" data-accept-canon="${escapeHtml(suggested)}">Aceptar</button><button class="btn btn-sm btn-outline-primary" type="button" data-modify-canon>Modificar</button></div></div>` : ''}
      <form id="assistant-draft-form" class="vstack gap-2">
        <div class="row g-2">
          <label class="col-md-6 form-label">Barrio<input class="form-control" name="barrio" list="neighborhood-list" maxlength="100" value="${escapeHtml(data.barrio)}"><datalist id="neighborhood-list">${neighborhoods.map((item) => `<option value="${escapeHtml(item.nombre)}"></option>`).join('')}</datalist></label>
          <label class="col-md-6 form-label">Comuna (opcional)<input class="form-control" name="barrio_comuna" maxlength="100" value="${escapeHtml(data.barrio_comuna)}"></label>
          <label class="col-md-6 form-label">Tipo<select class="form-select" name="tipo"><option value="">Selecciona</option>${propertyTypes().map(([value, name]) => `<option value="${value}" ${data.tipo === value ? 'selected' : ''}>${name}</option>`).join('')}</select></label>
          <label class="col-md-6 form-label">Dirección<input class="form-control" name="direccion" minlength="5" maxlength="500" value="${escapeHtml(data.direccion)}"></label>
          <label class="col-md-4 form-label">Habitaciones<input class="form-control" type="number" min="0" max="50" name="habitaciones" value="${escapeHtml(data.habitaciones)}"></label>
          <label class="col-md-4 form-label">Baños<input class="form-control" type="number" min="0" max="50" name="banos" value="${escapeHtml(data.banos)}"></label>
          <label class="col-md-4 form-label">Estrato<select class="form-select" name="estrato"><option value="">Selecciona</option>${[1, 2, 3, 4, 5, 6].map((value) => `<option value="${value}" ${Number(data.estrato) === value ? 'selected' : ''}>${value}</option>`).join('')}</select></label>
          <label class="col-md-6 form-label">Área (m²)<input class="form-control" type="number" min="1" step=".1" name="area_m2" value="${escapeHtml(data.area_m2)}"></label>
          <label class="col-md-6 form-label">Parqueadero<select class="form-select" name="parqueadero"><option value="">Sin especificar</option><option value="true" ${data.parqueadero === 'true' ? 'selected' : ''}>Sí</option><option value="false" ${data.parqueadero === 'false' ? 'selected' : ''}>No</option></select></label>
          <label class="col-md-6 form-label">Canon mensual (COP)<input class="form-control" type="number" min="1" step="1000" name="precio_mensual" value="${escapeHtml(data.precio_mensual)}"></label>
          <label class="col-md-6 form-label">Características separadas por coma<input class="form-control" name="caracteristicas" maxlength="1000" value="${escapeHtml(data.caracteristicas)}"></label>
          <label class="col-12 form-label">Título de publicación<input class="form-control" name="titulo" minlength="5" maxlength="255" value="${escapeHtml(data.titulo)}"></label>
          <label class="col-12 form-label">Descripción generada/editable<textarea class="form-control" name="descripcion" rows="4" maxlength="5000">${escapeHtml(data.descripcion)}</textarea></label>
          <input type="hidden" name="canon_confirmado" value="${data.canon_confirmado ? 'true' : 'false'}">
          <input type="hidden" name="mensaje_borrador" value="${escapeHtml(data.mensaje_borrador)}">
        </div>
        <div class="d-flex flex-wrap align-items-center gap-2">
          <button class="btn btn-outline-primary btn-sm" type="button" data-confirm-canon>Confirmar canon modificado</button>
          <span class="small text-secondary" data-canon-status>${confirmed ? 'Canon confirmado' : 'Confirma el canon para poder publicar.'}</span>
        </div>
        <label class="form-label mt-2">Fotografías (hasta 10, JPG/PNG/WEBP, máx. 5 MB c/u)<input class="form-control" type="file" accept="image/jpeg,image/png,image/webp" multiple data-property-images></label>
        <div class="small text-secondary" data-file-list>${selectedFiles.length ? `${selectedFiles.length} archivo(s) listos para enviar` : 'Las imágenes se guardan al confirmar la publicación.'}</div>
        <button class="btn btn-success" type="button" data-publish-property ${allPresent && confirmed && source.estado === 'lista' ? '' : 'disabled'}>Confirmar y publicar propiedad</button>
      </form>
    </section>
  </div>`;
}

function propertyTypes() {
  return [
    ['casa', 'Casa'], ['apartamento', 'Apartamento'], ['habitacion', 'Habitación'],
    ['apartaestudio', 'Apartaestudio'], ['local_comercial', 'Local comercial'],
    ['oficina', 'Oficina'], ['bodega', 'Bodega'], ['finca', 'Finca'],
  ];
}

function readSnapshot(root) {
  const form = root.querySelector('#assistant-draft-form');
  if (!form) return {};
  const fields = Object.fromEntries(new FormData(form));
  const toNumber = (value) => value === '' ? null : Number(value);
  return {
    barrio: fields.barrio.trim() || null,
    barrio_comuna: fields.barrio_comuna.trim() || null,
    tipo: fields.tipo || null,
    habitaciones: toNumber(fields.habitaciones),
    banos: toNumber(fields.banos),
    direccion: fields.direccion.trim() || null,
    estrato: toNumber(fields.estrato),
    area_m2: toNumber(fields.area_m2),
    precio_mensual: toNumber(fields.precio_mensual),
    ...(fields.parqueadero === '' ? {} : { parqueadero: fields.parqueadero === 'true' }),
    caracteristicas: fields.caracteristicas.split(',').map((item) => item.trim()).filter(Boolean),
    titulo: fields.titulo.trim() || null,
    descripcion: fields.descripcion.trim() || null,
    canon_confirmado: fields.canon_confirmado === 'true',
    mensaje_borrador: fields.mensaje_borrador || null,
  };
}

function completeValue(field, value) {
  return field === 'precio_mensual' ? Number(value) > 0 : value !== null && value !== undefined && value !== '';
}

function updateVisualState(root) {
  const draft = readSnapshot(root);
  const checks = [
    ['Ubicación', Boolean(draft.barrio && draft.direccion)],
    ['Características', Boolean(draft.tipo && draft.habitaciones !== null && draft.banos !== null && draft.estrato !== null)],
    ['Canon', Number(draft.precio_mensual) > 0 && draft.canon_confirmado],
    ['Publicación', Boolean(draft.titulo && draft.descripcion)],
  ];
  root.querySelectorAll('.info-block').forEach((block, index) => {
    block.classList.toggle('complete', Boolean(checks[index]?.[1]));
    const value = block.querySelector('.fw-semibold');
    if (value) value.textContent = checks[index]?.[1] ? 'Completo' : 'Pendiente';
  });
  const complete = required.every((field) => completeValue(field, draft[field]));
  const ready = complete && draft.canon_confirmado && draft.titulo && draft.descripcion && conversation.estado === 'lista';
  const publish = root.querySelector('[data-publish-property]');
  if (publish) publish.disabled = !ready;
  const canonStatus = root.querySelector('[data-canon-status]');
  if (canonStatus) canonStatus.textContent = draft.canon_confirmado && Number(draft.precio_mensual) > 0
    ? 'Canon confirmado'
    : 'Confirma el canon para poder publicar.';
}

function formDraftSnapshot(root) {
  const snapshot = readSnapshot(root);
  const chat = root.querySelector('textarea[name="mensaje_borrador"]');
  if (chat) snapshot.mensaje_borrador = chat.value || null;
  return snapshot;
}

function scheduleSave(root) {
  const status = root.querySelector('[data-save-state]');
  if (status) {
    status.className = 'save-state';
    status.textContent = 'Cambios pendientes…';
  }
  updateVisualState(root);
  window.clearTimeout(debounceTimer);
  debounceTimer = window.setTimeout(() => {
    void persistDraft(root);
  }, 750);
}

async function persistDraft(root) {
  window.clearTimeout(debounceTimer);
  const snapshot = formDraftSnapshot(root);
  const key = JSON.stringify(snapshot);
  if (key === savedSnapshot && !lastSaveError) return true;
  pendingSnapshot = { snapshot, key };
  if (savePromise) return savePromise;
  savePromise = (async () => {
    let success = true;
    while (pendingSnapshot) {
      const current = pendingSnapshot;
      pendingSnapshot = null;
      const status = root.querySelector('[data-save-state]');
      if (status) {
        status.className = 'save-state';
        status.textContent = 'Guardando…';
      }
      try {
        conversation = await marketingApi.updateDraft(conversation.id, current.snapshot);
        savedSnapshot = current.key;
        lastSaveError = '';
        const latest = root.querySelector('[data-save-state]');
        if (latest && JSON.stringify(formDraftSnapshot(root)) === current.key) {
          latest.className = 'save-state saved';
          latest.textContent = 'Guardado';
        }
      } catch (error) {
        lastSaveError = apiError(error, 'Error al guardar el borrador.');
        success = false;
        const latest = root.querySelector('[data-save-state]');
        if (latest) {
          latest.className = 'save-state error';
          latest.textContent = `Error al guardar: ${lastSaveError}`;
        }
      }
    }
    return success;
  })().finally(() => {
    savePromise = null;
  });
  return savePromise;
}

async function refreshAssistant(root, updatedConversation) {
  conversation = updatedConversation;
  root.querySelector('[data-assistant-area]').innerHTML = renderAssistantArea(conversation);
  root.querySelector('#assistant-messages')?.scrollTo({ top: 999999, behavior: 'smooth' });
  updateVisualState(root);
}

export function mount(root) {
  const initialSnapshot = formDraftSnapshot(root);
  savedSnapshot = JSON.stringify(initialSnapshot);
  updateVisualState(root);

  root.addEventListener('input', (event) => {
    if (event.target.name === 'precio_mensual') {
      const confirmed = root.querySelector('input[name="canon_confirmado"]');
      if (confirmed) confirmed.value = 'false';
    }
    if (event.target.closest('#assistant-draft-form') || event.target.name === 'mensaje_borrador') {
      scheduleSave(root);
    }
  });
  root.addEventListener('change', (event) => {
    if (event.target.closest('#assistant-draft-form')) scheduleSave(root);
    if (event.target.matches('[data-property-images]')) {
      const newFiles = [...event.target.files];
      const invalid = newFiles.find((file) => !['image/jpeg', 'image/png', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024);
      if (selectedFiles.length + newFiles.length > 10 || invalid) {
        event.target.value = '';
        root.querySelector('[data-assistant-feedback]').innerHTML = alert(invalid ? 'Usa imágenes JPG, PNG o WEBP de máximo 5 MB cada una.' : 'Puedes adjuntar máximo 10 fotografías.');
        return;
      }
      selectedFiles.push(...newFiles);
      root.querySelector('[data-file-list]').textContent = `${selectedFiles.length} archivo(s) listos para enviar. ${selectedFiles.map((file) => file.name).join(', ')}`;
      event.target.value = '';
    }
  });

  listen(root, 'click', 'button[data-action="retry-assistant"]', () => navigate('/asistente-ia', true));
  listen(root, 'click', '[data-accept-canon]', (event, button) => {
    const amount = Number(button.dataset.acceptCanon);
    root.querySelector('[name="precio_mensual"]').value = String(amount);
    root.querySelector('[name="canon_confirmado"]').value = 'true';
    scheduleSave(root);
  });
  listen(root, 'click', '[data-modify-canon]', () => {
    root.querySelector('[name="canon_confirmado"]').value = 'false';
    root.querySelector('[name="precio_mensual"]').focus();
    scheduleSave(root);
  });
  listen(root, 'click', '[data-confirm-canon]', () => {
    const price = Number(root.querySelector('[name="precio_mensual"]').value);
    if (!(price > 0)) {
      root.querySelector('[data-assistant-feedback]').innerHTML = alert('Ingresa un canon mayor que cero antes de confirmarlo.');
      return;
    }
    root.querySelector('[name="canon_confirmado"]').value = 'true';
    scheduleSave(root);
  });
  listen(root, 'submit', 'form#assistant-chat-form', async (event, form) => {
    event.preventDefault();
    const textarea = form.querySelector('textarea[name="mensaje_borrador"]');
    const message = textarea.value.trim();
    if (!message) return;
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    root.querySelector('[data-assistant-feedback]').innerHTML = '';
    root.querySelector('[data-save-state]').textContent = 'Guardando…';
    const persisted = await persistDraft(root);
    if (!persisted) {
      button.disabled = false;
      root.querySelector('[data-assistant-feedback]').innerHTML = alert('No se envió el mensaje porque el borrador no pudo guardarse.');
      return;
    }
    try {
      const response = await marketingApi.sendMessage(conversation.id, message);
      conversation = await marketingApi.conversation(conversation.id);
      await refreshAssistant(root, conversation);
      const chatDraft = root.querySelector('textarea[name="mensaje_borrador"]');
      if (chatDraft) chatDraft.value = '';
      const snapshot = formDraftSnapshot(root);
      savedSnapshot = JSON.stringify(snapshot);
      if (conversation.datos_recopilados?.mensaje_borrador) {
        conversation = await marketingApi.updateDraft(conversation.id, { mensaje_borrador: null });
        savedSnapshot = JSON.stringify(formDraftSnapshot(root));
      }
      root.querySelector('[data-save-state]').className = 'save-state saved';
      root.querySelector('[data-save-state]').textContent = 'Guardado';
      if (response.resultado_generado?.descripcion) {
        root.querySelector('[name="descripcion"]').value = response.resultado_generado.descripcion;
        root.querySelector('[name="titulo"]').value ||= defaultTitle(conversation.datos_recopilados);
        scheduleSave(root);
      }
    } catch (error) {
      root.querySelector('[data-assistant-feedback]').innerHTML = alert(apiError(error, 'No fue posible procesar el mensaje de IA.'));
    } finally {
      const currentButton = root.querySelector('#assistant-chat-form button[type="submit"]');
      if (currentButton) currentButton.disabled = false;
    }
  });
  listen(root, 'click', 'button[data-publish-property]', async (_event, button) => {
    const saved = await persistDraft(root);
    if (!saved) return;
    const draft = formDraftSnapshot(root);
    const complete = required.every((field) => completeValue(field, draft[field]));
    if (!complete || !draft.canon_confirmado) {
      root.querySelector('[data-assistant-feedback]').innerHTML = alert('Completa todos los campos y confirma el canon antes de publicar.');
      updateVisualState(root);
      return;
    }
    if (!window.confirm('La propiedad se guardará en RENTIO y será visible según su estado. ¿Confirmas la publicación?')) return;
    button.disabled = true;
    button.textContent = 'Publicando…';
    try {
      const created = await marketingApi.createProperty(conversation.id, {
        titulo: draft.titulo,
        descripcion: draft.descripcion,
      }, selectedFiles);
      selectedFiles = [];
      navigate(`/propiedades/${created.id}`);
    } catch (error) {
      root.querySelector('[data-assistant-feedback]').innerHTML = alert(apiError(error, 'No fue posible publicar la propiedad.'));
      button.disabled = false;
      button.textContent = 'Confirmar y publicar propiedad';
    }
  });

  return async () => {
    window.clearTimeout(debounceTimer);
    await persistDraft(root);
  };
}
