import { escapeHtml, fullName, roleLabel } from '../utils/dom.js';

const links = [
  ['/dashboard', 'Resumen', ['admin', 'propietario', 'arrendatario']],
  ['/propiedades', 'Propiedades', ['admin', 'propietario', 'arrendatario']],
  ['/solicitudes', 'Solicitudes', ['propietario', 'arrendatario']],
  ['/asistente-ia', 'Asistente IA', ['propietario']],
  ['/usuarios', 'Usuarios', ['admin']],
  ['/catalogos', 'Barrios y características', ['admin']],
];

export function authLayout(content) {
  return `<main class="auth-page container-fluid">
    <section class="auth-brand d-none d-lg-flex">
      <a class="brand" href="/login" data-link>RENTIO</a>
      <div><p class="text-uppercase small fw-semibold text-info">Gestión inmobiliaria</p><h1>Tu patrimonio,<br>en buenas manos.</h1><p class="text-white-50">Administra propiedades, solicitudes y contratos desde un solo lugar.</p></div>
      <span class="small text-white-50">Medellín, Colombia</span>
    </section>
    <section class="auth-panel"><div class="auth-panel-inner" id="auth-page">
      <a class="brand d-lg-none mb-4" href="/login" data-link>RENTIO</a>
      ${content}
      <p class="small text-secondary text-center mt-4">Al continuar, aceptas utilizar RENTIO de forma responsable y segura.</p>
    </div></section>
  </main>`;
}

export function dashboardLayout(content, route, user) {
  const currentRole = user?.rol;
  const nav = links
    .filter(([, , roles]) => roles.includes(currentRole))
    .map(([path, label]) => `<a class="nav-link ${route === path ? 'active' : ''}" href="${path}" data-link>${label}</a>`)
    .join('');
  const displayName = escapeHtml(fullName(user));
  return `<div class="app-shell">
    <aside class="sidebar" id="app-sidebar">
      <a class="brand" href="/dashboard" data-link>RENTIO</a>
      <span class="sidebar-caption">ESPACIO DE TRABAJO</span>
      <nav class="nav flex-column">${nav}</nav>
      <div class="sidebar-account">
        <div class="small text-white-50 mb-1">${displayName}</div>
        <div class="small text-white-50 mb-3">${escapeHtml(roleLabel(currentRole))}</div>
        <a class="nav-link" href="/perfil" data-link>Mi perfil</a>
        <button class="nav-link text-start w-100" type="button" data-action="logout">Cerrar sesión</button>
      </div>
    </aside>
    <div class="workspace">
      <header class="topbar">
        <button class="btn btn-outline-secondary btn-sm d-lg-none" type="button" data-action="toggle-menu" aria-label="Abrir menú">Menú</button>
        <div><span class="small text-secondary">RENTIO / </span><strong>${escapeHtml(routeTitle(route))}</strong></div>
        <span class="small text-secondary d-none d-sm-inline">Medellín, Colombia</span>
      </header>
      <main class="page-container" id="page-container">${content}</main>
      <footer class="app-footer">© ${new Date().getFullYear()} RENTIO <span>Gestión de arriendos · Medellín</span></footer>
    </div>
  </div>`;
}

function routeTitle(route) {
  return links.find(([path]) => path === route)?.[1]
    || (route === '/perfil' ? 'Mi perfil' : 'Panel');
}
