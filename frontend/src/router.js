import { authLayout, dashboardLayout } from './components/layout.js';
import { getUser, hasSession, logout } from './store/auth.js';
import { escapeHtml } from './utils/dom.js';

const routes = [
  { pattern: /^\/login\/?$/, module: () => import('./pages/auth.js'), method: 'renderLogin', guest: true },
  { pattern: /^\/register\/?$/, module: () => import('./pages/auth.js'), method: 'renderRegister', guest: true },
  { pattern: /^\/dashboard\/?$/, module: () => import('./pages/dashboard.js'), method: 'renderDashboard', roles: ['admin', 'propietario', 'arrendatario'] },
  { pattern: /^\/propiedades\/?$/, module: () => import('./pages/properties.js'), method: 'renderProperties', roles: ['admin', 'propietario', 'arrendatario'] },
  { pattern: /^\/propiedades\/(\d+)\/?$/, module: () => import('./pages/properties.js'), method: 'renderPropertyDetail', roles: ['admin', 'propietario', 'arrendatario'] },
  { pattern: /^\/solicitudes\/?$/, module: () => import('./pages/rentals.js'), method: 'renderRentals', roles: ['propietario', 'arrendatario'] },
  { pattern: /^\/arriendos\/?$/, redirect: '/solicitudes' },
  { pattern: /^\/usuarios\/?$/, module: () => import('./pages/users.js'), method: 'renderUsers', roles: ['admin'] },
  { pattern: /^\/catalogos\/?$/, module: () => import('./pages/catalogs.js'), method: 'renderCatalogs', roles: ['admin'] },
  { pattern: /^\/asistente-ia\/?$/, module: () => import('./pages/assistant.js'), method: 'renderAssistant', roles: ['propietario'] },
  { pattern: /^\/perfil\/?$/, module: () => import('./pages/profile.js'), method: 'renderProfile', roles: ['admin', 'propietario', 'arrendatario'] },
];

let app;
let bootError = '';
let activeCleanup;
let renderSequence = 0;

export function navigate(path, replace = false) {
  if (replace) history.replaceState({}, '', path);
  else history.pushState({}, '', path);
  void renderRoute();
}

export async function initializeRouter() {
  app = document.querySelector('#app');
  if (!app) throw new Error('No se encontró el contenedor #app.');
  document.addEventListener('click', handleDocumentClick);
  window.addEventListener('popstate', () => void renderRoute());
  window.addEventListener('rentio:unauthorized', () => {
    const login = `/login?expired=1`;
    history.replaceState({}, '', login);
    void renderRoute();
  });
  window.addEventListener('rentio:auth-change', () => void renderRoute());
  if (localStorage.getItem('rentio_token')) {
    try {
      const { authApi } = await import('./api/services.js');
      const sessionUser = await authApi.profile();
      const { setUser } = await import('./store/auth.js');
      setUser(sessionUser);
    } catch (error) {
      bootError = error.message || 'No se pudo validar la sesión.';
      if (!localStorage.getItem('rentio_token')) bootError = '';
    }
  }
  await renderRoute();
}

async function renderRoute() {
  const sequence = ++renderSequence;
  if (activeCleanup) {
    const cleanup = activeCleanup;
    activeCleanup = null;
    await cleanup();
  }
  if (sequence !== renderSequence) return;
  const path = location.pathname;
  if (path === '/') {
    navigate(hasSession() ? '/dashboard' : '/login', true);
    return;
  }
  const match = routes.map((route) => ({ route, result: path.match(route.pattern) })).find((item) => item.result);
  if (!match) {
    navigate(hasSession() ? '/dashboard' : '/login', true);
    return;
  }
  const { route, result } = match;
  if (route.redirect) {
    navigate(route.redirect, true);
    return;
  }
  const user = getUser();
  if (route.guest && hasSession()) {
    navigate('/dashboard', true);
    return;
  }
  if (route.roles && !hasSession()) {
    navigate('/login', true);
    return;
  }
  if (route.roles && !route.roles.includes(user?.rol)) {
    navigate('/dashboard', true);
    return;
  }

  const params = result.slice(1);
  try {
    const page = await route.module();
    if (sequence !== renderSequence) return;
    const content = await page[route.method](...params);
    if (sequence !== renderSequence) return;
    const layout = route.guest
      ? authLayout(content)
      : dashboardLayout(content, path === '/arriendos' ? '/solicitudes' : path.replace(/\/$/, ''), user);
    app.innerHTML = `${bootError ? `<div class="global-error alert alert-warning">${escapeHtml(bootError)}</div>` : ''}${layout}`;
    if (!route.guest) {
      app.querySelector('#app-sidebar')?.classList.remove('sidebar-open');
    }
    activeCleanup = page.mount?.(
      route.guest ? app.querySelector('#auth-page') : app.querySelector('#page-container'),
    ) || null;
  } catch (error) {
    app.innerHTML = `<main class="container py-5">${escapeHtml(error.message || 'No se pudo cargar esta pantalla.')}</main>`;
  }
}

function handleDocumentClick(event) {
  const link = event.target.closest('a[data-link]');
  if (link) {
    event.preventDefault();
    navigate(link.getAttribute('href'));
    return;
  }
  const action = event.target.closest('[data-action]')?.dataset.action;
  if (action === 'logout') {
    logout();
    navigate('/login', true);
  } else if (action === 'toggle-menu') {
    document.querySelector('#app-sidebar')?.classList.toggle('sidebar-open');
  }
}
