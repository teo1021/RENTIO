import { authApi } from '../api/services.js';
import { apiError } from '../api/client.js';
import { setSession } from '../store/auth.js';
import { alert, escapeHtml, listen, setBusy } from '../utils/dom.js';
import { navigate } from '../router.js';

export function renderLogin() {
  const expired = new URLSearchParams(location.search).has('expired');
  return `<section id="auth-page">
    <h2 class="h3 fw-bold">Iniciar sesión</h2>
    <p class="text-secondary mb-4">Ingresa para continuar en tu espacio RENTIO.</p>
    ${expired ? alert('Tu sesión terminó. Inicia sesión nuevamente.', 'warning') : ''}
    <div data-auth-feedback></div>
    <form id="login-form" class="vstack gap-3">
      <label class="form-label">Correo electrónico<input class="form-control mt-1" name="correo" type="email" autocomplete="email" required></label>
      <label class="form-label">Contraseña<input class="form-control mt-1" name="contrasena" type="password" autocomplete="current-password" required></label>
      <button class="btn btn-primary" type="submit">Iniciar sesión</button>
    </form>
    <p class="text-center mt-4 mb-0">¿No tienes cuenta? <a href="/register" data-link>Crear cuenta</a></p>
  </section>`;
}

export function renderRegister() {
  return `<section id="auth-page">
    <h2 class="h3 fw-bold">Crear cuenta</h2>
    <p class="text-secondary mb-4">Elige cómo utilizarás RENTIO.</p>
    <div data-auth-feedback></div>
    <form id="register-form" class="vstack gap-3">
      <div class="row g-2">
        <label class="col form-label">Nombre<input class="form-control mt-1" name="nombre" maxlength="100" required></label>
        <label class="col form-label">Apellido<input class="form-control mt-1" name="apellido" maxlength="100"></label>
      </div>
      <label class="form-label">Correo electrónico<input class="form-control mt-1" name="correo" type="email" autocomplete="email" required></label>
      <label class="form-label">Contraseña<input class="form-control mt-1" name="contrasena" type="password" minlength="8" autocomplete="new-password" required><span class="form-text">Mínimo 8 caracteres.</span></label>
      <label class="form-label">Tipo de cuenta
        <select class="form-select mt-1" name="rol" required>
          <option value="arrendatario">Busco arriendo</option>
          <option value="propietario">Ofrezco propiedades</option>
        </select>
      </label>
      <button class="btn btn-primary" type="submit">Crear cuenta</button>
    </form>
    <p class="text-center mt-4 mb-0">¿Ya tienes cuenta? <a href="/login" data-link>Iniciar sesión</a></p>
  </section>`;
}

export function mount(root) {
  listen(root, 'submit', 'form#login-form', async (event, form) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    setBusy(button, true, 'Ingresando…');
    root.querySelector('[data-auth-feedback]').innerHTML = '';
    try {
      const data = Object.fromEntries(new FormData(form));
      const session = await authApi.login(data.correo.trim().toLowerCase(), data.contrasena);
      setSession(session.usuario, session.token);
      navigate('/dashboard', true);
    } catch (error) {
      root.querySelector('[data-auth-feedback]').innerHTML = alert(apiError(error, 'No fue posible iniciar sesión.'));
      setBusy(button, false);
    }
  });

  listen(root, 'submit', 'form#register-form', async (event, form) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    setBusy(button, true, 'Creando cuenta…');
    root.querySelector('[data-auth-feedback]').innerHTML = '';
    const data = Object.fromEntries(new FormData(form));
    data.correo = data.correo.trim().toLowerCase();
    try {
      await authApi.register(data);
      const session = await authApi.login(data.correo, data.contrasena);
      setSession(session.usuario, session.token);
      navigate('/dashboard', true);
    } catch (error) {
      root.querySelector('[data-auth-feedback]').innerHTML = alert(apiError(error, 'No fue posible crear la cuenta.'));
      setBusy(button, false);
    }
  });
}
