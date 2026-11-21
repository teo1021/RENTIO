import { Modal } from 'bootstrap';
import { jsPDF } from 'jspdf';
import { authApi, rentalsApi } from '../api/services.js';
import { apiError } from '../api/client.js';
import { getUser } from '../store/auth.js';
import { alert, dateLabel, escapeHtml, fullName, listen, money, statusBadge } from '../utils/dom.js';

let requests = [];
let contracts = [];
let profile = null;
let tab = 'solicitudes';

export async function renderRentals() {
  const owner = getUser().rol === 'propietario';
  let error = '';
  try {
    [requests, contracts, profile] = await Promise.all([
      owner ? rentalsApi.received() : rentalsApi.mine(),
      rentalsApi.contracts(),
      authApi.profile(),
    ]);
  } catch (cause) {
    error = apiError(cause, 'No fue posible consultar las solicitudes y contratos.');
    requests = [];
    contracts = [];
  }
  tab = new URLSearchParams(location.search).get('tab') === 'contratos' ? 'contratos' : 'solicitudes';
  return `<div class="page-stack">
    <div class="page-heading"><div><p class="text-uppercase small fw-semibold text-secondary mb-1">Relaciones contractuales</p><h1>${owner ? 'Solicitudes y contratos' : 'Mis solicitudes'}</h1><p>${owner ? 'Revisa solicitudes, confirma visitas y formaliza contratos.' : 'Consulta las solicitudes enviadas y los contratos asociados.'}</p></div></div>
    <div data-rental-feedback>${alert(error)}</div>
    <div class="d-flex gap-2"><button class="btn ${tab === 'solicitudes' ? 'btn-primary' : 'btn-outline-primary'}" data-rental-tab="solicitudes">Solicitudes (${requests.length})</button><button class="btn ${tab === 'contratos' ? 'btn-primary' : 'btn-outline-primary'}" data-rental-tab="contratos">Contratos (${contracts.length})</button></div>
    <section id="rental-table"></section>
    <div id="rental-modal-host"></div>
  </div>`;
}

function requestTable() {
  const owner = getUser().rol === 'propietario';
  if (!requests.length) return '<div class="panel text-secondary">Todavía no hay solicitudes.</div>';
  const rows = requests.map((item) => {
    const actions = owner
      ? item.estado === 'pendiente' || item.estado === 'pendiente_visita'
        ? `<button class="btn btn-sm btn-outline-primary" data-visit="${item.id}" data-decision="visita_programada">Confirmar visita</button> <button class="btn btn-sm btn-outline-danger" data-visit="${item.id}" data-decision="rechazada">Rechazar</button>`
        : item.estado === 'visita_programada' && !item.contrato
          ? `<button class="btn btn-sm btn-primary" data-contract="${item.id}">Generar contrato</button> <button class="btn btn-sm btn-outline-danger" data-visit="${item.id}" data-decision="rechazada">Rechazar</button>`
          : '—'
      : '—';
    const interested = owner
      ? `${escapeHtml(fullName(item.arrendatario))}${item.cedula_arrendatario ? `<br><small>CC ${escapeHtml(item.cedula_arrendatario)}</small>` : ''}${item.telefono_arrendatario ? `<br><small>${escapeHtml(item.telefono_arrendatario)}</small>` : ''}`
      : dateLabel(item.fecha_solicitud);
    return `<tr>
      <td>${escapeHtml(item.propiedad?.titulo || `Propiedad #${item.propiedad_id}`)}<div class="small text-secondary">${escapeHtml(item.propiedad?.direccion || '')}</div></td>
      <td>${interested}</td>
      <td>${item.fecha_visita_propuesta ? dateLabel(item.fecha_visita_propuesta) : 'Sin fecha'}</td>
      <td>${item.fecha_visita_confirmada ? dateLabel(item.fecha_visita_confirmada) : '—'}</td>
      <td>${statusBadge(item.estado)}</td>
      <td>${actions}</td>
    </tr>`;
  }).join('');
  return `<div class="table-responsive"><table class="table table-compact"><thead><tr><th>Propiedad</th><th>${owner ? 'Solicitante' : 'Enviada'}</th><th>Visita propuesta</th><th>Visita confirmada</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function contractTable() {
  if (!contracts.length) return '<div class="panel text-secondary">Aún no hay contratos registrados.</div>';
  const rows = contracts.map((contract) => {
    const request = requests.find((item) => item.id === contract.solicitud_id);
    const ready = canGeneratePDF(contract, request);
    return `<tr>
      <td>${escapeHtml(contract.numero_contrato || `#${contract.id}`)}</td>
      <td>${escapeHtml(request?.propiedad?.titulo || `Solicitud #${contract.solicitud_id}`)}<div class="small text-secondary">${escapeHtml(request?.propiedad?.direccion || '')}</div></td>
      <td>${escapeHtml(request ? fullName(request.arrendatario) : 'No disponible')}</td>
      <td>${dateLabel(contract.fecha_inicio)}</td><td>${dateLabel(contract.fecha_fin)}</td>
      <td>${money(contract.precio_acordado)}</td><td>${statusBadge(contract.estado)}</td>
      <td>${contract.trabaja === null || contract.trabaja === undefined ? 'Sin especificar' : contract.trabaja ? 'Sí' : 'No'}</td>
      <td>${escapeHtml(contract.empresa || '—')}</td><td>${escapeHtml(contract.cargo || '—')}</td>
      <td>${contract.ingreso_mensual ? money(contract.ingreso_mensual) : '—'}</td>
      <td>${escapeHtml(contract.fiador_nombre || '—')}</td>
      <td>${escapeHtml(contract.fiador_cedula || '—')}</td>
      <td>${escapeHtml(contract.fiador_telefono || '—')}</td>
      <td>${contract.clausulas_adicionales ? `<details><summary>Ver condiciones</summary><span>${escapeHtml(contract.clausulas_adicionales)}</span></details>` : '—'}</td>
      <td><button class="btn btn-sm btn-outline-primary" data-download-contract="${contract.id}" ${ready ? '' : 'disabled'} title="${ready ? 'Descargar PDF' : escapeHtml(pdfBlockReason(contract, request))}">PDF</button></td>
    </tr>`;
  }).join('');
  return `<div class="table-responsive"><table class="table table-compact"><thead><tr><th>Número</th><th>Propiedad</th><th>Arrendatario</th><th>Inicio</th><th>Fin</th><th>Canon</th><th>Estado</th><th>Trabaja</th><th>Empresa</th><th>Cargo</th><th>Ingreso mensual</th><th>Fiador</th><th>CC fiador</th><th>Teléfono fiador</th><th>Condiciones pactadas</th><th>Documento</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function canGeneratePDF(contract, request) {
  return !pdfBlockReason(contract, request);
}

function pdfBlockReason(contract, request) {
  const tenant = request?.arrendatario || {};
  const tenantProfile = tenant.perfil || {};
  const ownerProfile = profile?.perfil || {};
  const missing = [];
  if (getUser()?.rol !== 'propietario') missing.push('identificación del propietario no disponible para tu rol');
  if (!contract?.numero_contrato) missing.push('número');
  if (!contract?.fecha_inicio || !contract?.fecha_fin) missing.push('vigencia');
  if (!(Number(contract?.precio_acordado) > 0)) missing.push('canon');
  if (!request?.propiedad?.titulo || !request?.propiedad?.direccion) missing.push('inmueble');
  if (!tenantProfile.nombre || !tenantProfile.apellido || !request?.cedula_arrendatario) missing.push('identificación del arrendatario');
  if (!ownerProfile.nombre || !ownerProfile.apellido || !ownerProfile.cedula) missing.push('identificación del propietario');
  return missing.length ? `Falta información: ${missing.join(', ')}.` : '';
}

function visitModal(request, decision) {
  return `<div class="modal fade" id="visit-modal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><form id="visit-form" data-id="${request.id}" data-decision="${decision}">
    <div class="modal-header"><h2 class="modal-title fs-5">${decision === 'visita_programada' ? 'Confirmar visita' : 'Rechazar solicitud'}</h2><button class="btn-close" type="button" data-bs-dismiss="modal"></button></div>
    <div class="modal-body vstack gap-3"><p>${decision === 'visita_programada' ? `Fecha propuesta: ${dateLabel(request.fecha_visita_propuesta)}` : `¿Confirmas que deseas rechazar la solicitud de ${escapeHtml(fullName(request.arrendatario))}?`}</p>
      ${decision === 'visita_programada' ? `<label class="form-label">Fecha confirmada<input class="form-control" type="date" name="fecha_visita_confirmada" value="${escapeHtml(request.fecha_visita_propuesta || '')}" required></label>` : ''}
      ${request.cedula_arrendatario ? `<div class="small text-secondary">Documento: ${escapeHtml(request.cedula_arrendatario)}</div>` : ''}
    </div>
    <div class="modal-footer"><button class="btn btn-outline-secondary" type="button" data-bs-dismiss="modal">Cancelar</button><button class="btn ${decision === 'rechazada' ? 'btn-danger' : 'btn-primary'}" type="submit">Confirmar</button></div>
  </form></div></div></div>`;
}

function contractModal(request) {
  const date = new Date();
  const today = localDate(date);
  date.setFullYear(date.getFullYear() + 1);
  const nextYear = localDate(date);
  return `<div class="modal fade" id="contract-modal" tabindex="-1"><div class="modal-dialog modal-lg modal-dialog-scrollable"><div class="modal-content"><form id="contract-form" data-id="${request.id}">
    <div class="modal-header"><h2 class="modal-title fs-5">Formalizar contrato</h2><button class="btn-close" type="button" data-bs-dismiss="modal"></button></div>
    <div class="modal-body vstack gap-3">
      <p class="text-secondary">Solicitante: <strong>${escapeHtml(fullName(request.arrendatario))}</strong> · ${escapeHtml(request.propiedad?.titulo || '')}</p>
      <div class="row g-2">
        <label class="col-md-6 form-label">Fecha de inicio<input class="form-control" type="date" name="fecha_inicio" value="${today}" required></label>
        <label class="col-md-6 form-label">Fecha de finalización<input class="form-control" type="date" name="fecha_fin" value="${nextYear}" min="${today}" required></label>
        <label class="col-md-6 form-label">Canon acordado<input class="form-control" type="number" min="1" name="precio_acordado" value="${escapeHtml(request.propiedad?.precio_mensual || '')}" required></label>
        <label class="col-md-6 form-label">¿Trabaja actualmente?<select class="form-select" name="trabaja"><option value="">Sin especificar</option><option value="true">Sí</option><option value="false">No</option></select></label>
        <label class="col-md-4 form-label">Empresa<input class="form-control" name="empresa" maxlength="200"></label>
        <label class="col-md-4 form-label">Cargo<input class="form-control" name="cargo" maxlength="200"></label>
        <label class="col-md-4 form-label">Ingreso mensual<input class="form-control" type="number" min="0" name="ingreso_mensual"></label>
        <label class="col-md-4 form-label">Fiador<input class="form-control" name="fiador_nombre" maxlength="200"></label>
        <label class="col-md-4 form-label">Documento del fiador<input class="form-control" name="fiador_cedula" maxlength="20"></label>
        <label class="col-md-4 form-label">Teléfono del fiador<input class="form-control" name="fiador_telefono" maxlength="20"></label>
        <label class="col-12 form-label">Condiciones pactadas<textarea class="form-control" name="clausulas_adicionales" rows="3" maxlength="5000"></textarea></label>
      </div>
      <div data-contract-feedback></div>
    </div>
    <div class="modal-footer"><button class="btn btn-outline-secondary" type="button" data-bs-dismiss="modal">Cancelar</button><button class="btn btn-primary" type="submit">Guardar contrato</button></div>
  </form></div></div></div>`;
}

function localDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export function mount(root) {
  const table = root.querySelector('#rental-table');
  const feedback = root.querySelector('[data-rental-feedback]');
  function draw() {
    table.innerHTML = tab === 'solicitudes' ? requestTable() : contractTable();
  }
  draw();

  listen(root, 'click', 'button[data-rental-tab]', (_event, button) => {
    tab = button.dataset.rentalTab;
    root.querySelectorAll('[data-rental-tab]').forEach((item) => item.classList.toggle('btn-primary', item === button));
    root.querySelectorAll('[data-rental-tab]').forEach((item) => item.classList.toggle('btn-outline-primary', item !== button));
    draw();
  });
  listen(root, 'click', 'button[data-visit]', (_event, button) => {
    const request = requests.find((item) => item.id === Number(button.dataset.visit));
    if (!request) return;
    const host = root.querySelector('#rental-modal-host');
    host.innerHTML = visitModal(request, button.dataset.decision);
    Modal.getOrCreateInstance(host.querySelector('#visit-modal')).show();
  });
  listen(root, 'click', 'button[data-contract]', (_event, button) => {
    const request = requests.find((item) => item.id === Number(button.dataset.contract));
    if (!request) return;
    const host = root.querySelector('#rental-modal-host');
    host.innerHTML = contractModal(request);
    Modal.getOrCreateInstance(host.querySelector('#contract-modal')).show();
  });
  listen(root, 'submit', 'form#visit-form', async (event, form) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    const payload = { estado: form.dataset.decision };
    const date = new FormData(form).get('fecha_visita_confirmada');
    if (date) payload.fecha_visita_confirmada = date;
    try {
      await rentalsApi.respondVisit(Number(form.dataset.id), payload);
      requests = getUser().rol === 'propietario' ? await rentalsApi.received() : await rentalsApi.mine();
      Modal.getInstance(root.querySelector('#visit-modal'))?.hide();
      feedback.innerHTML = alert('Solicitud actualizada.', 'success');
      draw();
    } catch (error) {
      form.querySelector('.modal-body').insertAdjacentHTML('beforeend', alert(apiError(error, 'No fue posible responder la solicitud.')));
      button.disabled = false;
    }
  });
  listen(root, 'submit', 'form#contract-form', async (event, form) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    const raw = Object.fromEntries(new FormData(form));
    const payload = {
      fecha_inicio: raw.fecha_inicio,
      fecha_fin: raw.fecha_fin,
      precio_acordado: Number(raw.precio_acordado),
      trabaja: raw.trabaja === '' ? undefined : raw.trabaja === 'true',
      empresa: raw.empresa.trim() || undefined,
      cargo: raw.cargo.trim() || undefined,
      ingreso_mensual: raw.ingreso_mensual ? Number(raw.ingreso_mensual) : undefined,
      fiador_nombre: raw.fiador_nombre.trim() || undefined,
      fiador_cedula: raw.fiador_cedula.trim() || undefined,
      fiador_telefono: raw.fiador_telefono.trim() || undefined,
      clausulas_adicionales: raw.clausulas_adicionales.trim() || undefined,
    };
    try {
      await rentalsApi.createContract(Number(form.dataset.id), payload);
      requests = await rentalsApi.received();
      contracts = await rentalsApi.contracts();
      Modal.getInstance(root.querySelector('#contract-modal'))?.hide();
      tab = 'contratos';
      root.querySelectorAll('[data-rental-tab]').forEach((item) => {
        const active = item.dataset.rentalTab === tab;
        item.classList.toggle('btn-primary', active);
        item.classList.toggle('btn-outline-primary', !active);
      });
      draw();
      feedback.innerHTML = alert('Contrato guardado. Usa el botón PDF de la tabla para generar el documento.', 'success');
    } catch (error) {
      form.querySelector('[data-contract-feedback]').innerHTML = alert(apiError(error, 'No fue posible guardar el contrato.'));
      button.disabled = false;
    }
  });
  listen(root, 'click', 'button[data-download-contract]', async (_event, button) => {
    const contract = contracts.find((item) => item.id === Number(button.dataset.downloadContract));
    const request = requests.find((item) => item.id === contract?.solicitud_id);
    if (!contract || !canGeneratePDF(contract, request)) {
      feedback.innerHTML = alert(pdfBlockReason(contract, request));
      return;
    }
    try {
      createContractPDF(contract, request);
    } catch (error) {
      feedback.innerHTML = alert(error.message || 'No fue posible generar el PDF.');
    }
  });
}

function createContractPDF(contract, request) {
  if (!canGeneratePDF(contract, request)) throw new Error(pdfBlockReason(contract, request));
  const doc = new jsPDF({ unit: 'mm', format: 'a4' });
  const margin = 18;
  const pageWidth = doc.internal.pageSize.getWidth();
  let y = 22;
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  doc.setTextColor(20, 42, 67);
  doc.text('RENTIO', margin, y);
  doc.setFontSize(13);
  doc.text('REGISTRO DE CONTRATO DE ARRENDAMIENTO', margin, y + 9);
  doc.setDrawColor(19, 139, 128);
  doc.line(margin, y + 13, pageWidth - margin, y + 13);
  y += 22;

  const owner = profile.perfil;
  const tenant = request.arrendatario.perfil;
  const fields = [
    ['Número de contrato', contract.numero_contrato],
    ['Estado', contract.estado],
    ['Propietario', `${owner.nombre} ${owner.apellido}`],
    ['Documento del propietario', owner.cedula],
    ['Arrendatario', `${tenant.nombre} ${tenant.apellido}`],
    ['Documento del arrendatario', request.cedula_arrendatario],
    ['Teléfono del arrendatario', request.telefono_arrendatario || tenant.telefono || 'No informado'],
    ['Inmueble', request.propiedad.titulo],
    ['Dirección', request.propiedad.direccion],
    ['Fecha de inicio', dateLabel(contract.fecha_inicio)],
    ['Fecha de finalización', dateLabel(contract.fecha_fin)],
    ['Canon mensual', money(contract.precio_acordado)],
    ['Situación laboral', contract.trabaja === null || contract.trabaja === undefined ? 'Sin especificar' : contract.trabaja ? 'Trabaja' : 'No trabaja'],
    ['Empresa', contract.empresa || 'No informada'],
    ['Cargo', contract.cargo || 'No informado'],
    ['Ingreso mensual', contract.ingreso_mensual ? money(contract.ingreso_mensual) : 'No informado'],
    ['Fiador', contract.fiador_nombre || 'No informado'],
    ['Documento del fiador', contract.fiador_cedula || 'No informado'],
    ['Teléfono del fiador', contract.fiador_telefono || 'No informado'],
  ];
  doc.setFontSize(10);
  for (const [label, value] of fields) {
    if (y > 265) {
      doc.addPage();
      y = 20;
    }
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(90, 105, 121);
    doc.text(label, margin, y);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(34, 50, 71);
    const lines = doc.splitTextToSize(String(value), pageWidth - margin * 2 - 62);
    doc.text(lines, margin + 62, y);
    y += Math.max(7, lines.length * 5);
  }
  if (contract.clausulas_adicionales) {
    if (y > 250) { doc.addPage(); y = 20; }
    y += 4;
    doc.setFont('helvetica', 'bold');
    doc.text('Condiciones pactadas', margin, y);
    y += 6;
    doc.setFont('helvetica', 'normal');
    doc.text(doc.splitTextToSize(contract.clausulas_adicionales, pageWidth - margin * 2), margin, y);
  }
  doc.setFontSize(8);
  doc.setTextColor(115, 128, 145);
  doc.text('Documento generado con los datos registrados en RENTIO. Verifique la información antes de usarlo como instrumento contractual.', margin, 285, { maxWidth: pageWidth - margin * 2 });
  doc.save(`${contract.numero_contrato || `contrato-${contract.id}`}.pdf`);
}
