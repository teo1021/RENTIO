import { authApi } from '../api/services.js';
import { apiError } from '../api/client.js';
import { setUser } from '../store/auth.js';
import { alert, escapeHtml, listen } from '../utils/dom.js';

let profileUser;
let editMode = false;
let saveTimer;
let saveChain = Promise.resolve();

export async function renderProfile() {
  try {
    profileUser = await authApi.profile();
  } catch (error) {
    return `${alert(apiError(error, 'No fue posible consultar tu perfil.'))}`;
  }
  const profile = profileUser.perfil || {};
  return `<div class="page-stack">
    <div class="page-heading"><div><p class="text-uppercase small fw-semibold text-secondary mb-1">Tu cuenta</p><h1>Mi perfil</h1></div><button class="btn btn-primary" type="button" data-action="edit-profile">Editar perfil</button></div>
    <div data-profile-feedback></div>
    <section class="panel" data-profile-panel>${renderProfileContent(profileUser)}</section>
  </div>`;
}

function renderProfileContent(user) {
  const profile = user.perfil || {};
  if (!editMode) {
    return `<div class="row g-3">
      ${profile.foto_perfil ? `<div class="col-12"><img class="rounded-circle object-fit-cover" src="${escapeHtml(profile.foto_perfil)}" alt="Foto de perfil" width="72" height="72"></div>` : ''}
      ${detail('Nombre', [profile.nombre, profile.apellido].filter(Boolean).join(' ') || 'Sin registrar')}
      ${detail('Correo electrónico', user.correo || 'Sin registrar')}
      ${detail('Teléfono', profile.telefono || 'Sin registrar')}
      ${detail('Documento', profile.cedula || 'Sin registrar')}
    </div>`;
  }
  return `<form id="profile-form" class="vstack gap-3">
    <div class="row g-3">
      <label class="col-md-6 form-label">Nombre<input class="form-control" name="nombre" maxlength="100" value="${escapeHtml(profile.nombre || '')}"></label>
      <label class="col-md-6 form-label">Apellido<input class="form-control" name="apellido" maxlength="100" value="${escapeHtml(profile.apellido || '')}"></label>
      <label class="col-md-6 form-label">Correo electrónico<input class="form-control" value="${escapeHtml(user.correo || '')}" disabled></label>
      <label class="col-md-6 form-label">Teléfono<input class="form-control" name="telefono" maxlength="20" value="${escapeHtml(profile.telefono || '')}"></label>
      <label class="col-md-6 form-label">Documento de identidad<input class="form-control" name="cedula" maxlength="20" value="${escapeHtml(profile.cedula || '')}"></label>
      <label class="col-md-6 form-label">URL de foto<input class="form-control" name="foto_perfil" maxlength="500" type="url" value="${escapeHtml(profile.foto_perfil || '')}"></label>
    </div>
    <div class="d-flex align-items-center gap-3"><button class="btn btn-outline-secondary" type="button" data-action="cancel-profile">Cancelar</button><span class="small text-secondary" data-profile-save-state role="status">Los cambios se guardan automáticamente.</span></div>
  </form>`;
}

function detail(label, value) {
  return `<div class="col-md-6"><div class="small text-secondary">${escapeHtml(label)}</div><div class="fw-semibold">${escapeHtml(value)}</div></div>`;
}

export function mount(root) {
  listen(root, 'click', '[data-action="edit-profile"]', () => {
    editMode = true;
    root.querySelector('[data-profile-panel]').innerHTML = renderProfileContent(profileUser);
    root.querySelector('[data-action="edit-profile"]').classList.add('d-none');
  });
  listen(root, 'click', '[data-action="cancel-profile"]', () => {
    window.clearTimeout(saveTimer);
    editMode = false;
    root.querySelector('[data-profile-panel]').innerHTML = renderProfileContent(profileUser);
    root.querySelector('[data-action="edit-profile"]').classList.remove('d-none');
  });
  listen(root, 'submit', 'form#profile-form', async (event, form) => {
    event.preventDefault();
    await saveProfile(form, root);
  });
  listen(root, 'input', 'form#profile-form', (_event, form) => {
    const state = root.querySelector('[data-profile-save-state]');
    if (state) state.textContent = 'Cambios pendientes…';
    window.clearTimeout(saveTimer);
    saveTimer = window.setTimeout(() => void saveProfile(form, root), 700);
  });
}

function saveProfile(form, root) {
  window.clearTimeout(saveTimer);
  const payload = Object.fromEntries(new FormData(form));
  const state = root.querySelector('[data-profile-save-state]');
  if (state) state.textContent = 'Guardando…';
  saveChain = saveChain.then(async () => {
    try {
      const updated = await authApi.updateProfile(payload);
      profileUser = updated;
      setUser(updated);
      if (state) state.textContent = 'Guardado';
      return true;
    } catch (error) {
      if (state) state.textContent = `Error al guardar: ${apiError(error, 'No fue posible guardar el perfil.')}`;
      return false;
    }
  });
  return saveChain;
}
