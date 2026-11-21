import { adminApi } from '../api/services.js';
import { apiError } from '../api/client.js';
import { alert, escapeHtml, fullName, listen } from '../utils/dom.js';

let users = [];
let currentError = '';
let currentSuccess = '';

export async function renderUsers() {
  try {
    users = await adminApi.users();
    currentError = '';
  } catch (error) {
    currentError = apiError(error, 'No fue posible cargar los usuarios.');
  }
  return `<div class="page-stack">
    <div class="page-heading"><div><p class="text-uppercase small fw-semibold text-secondary mb-1">Administración</p><h1>Usuarios</h1></div></div>
    <div data-user-feedback>${alert(currentError)}${alert(currentSuccess, 'success')}</div>
    <section class="panel">
      ${users.length ? `<ul class="list-group list-group-flush">${users.map((item) => `<li class="list-group-item px-0">${escapeHtml(fullName(item))}</li>`).join('')}</ul>` : '<p class="text-secondary mb-0">No hay usuarios registrados.</p>'}
    </section>
  </div>`;
}

export function mount() {}
