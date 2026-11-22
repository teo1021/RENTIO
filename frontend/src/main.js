import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap/dist/js/bootstrap.bundle.min.js';
import './styles.css';
import { initializeRouter } from './router.js';

initializeRouter().catch((error) => {
  const app = document.querySelector('#app');
  if (app) {
    const message = document.createElement('div');
    message.className = 'alert alert-danger';
    message.setAttribute('role', 'alert');
    message.textContent = error.message || 'No se pudo iniciar RENTIO.';
    app.replaceChildren(message);
  }
});
