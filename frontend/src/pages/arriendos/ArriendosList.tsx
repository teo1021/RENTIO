import { useEffect, useState, type FormEvent } from 'react';
import { CalendarDays, Check, FileText, User, X } from 'lucide-react';
import { rentalsApi } from '../../api/services';
import { getApiError } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { dateLabel, fullName, money } from '../../lib/format';
import type { Contrato, SolicitudArriendo } from '../../types';
import {
  Alert,
  Button,
  EmptyState,
  Field,
  LoadingState,
  Modal,
  PageHeader,
  Panel,
  StatusBadge,
} from '../../components/ui';

// ── Helpers ──────────────────────────────────────────────────────────────────

function estadoLabel(estado: SolicitudArriendo['estado']): string {
  const labels: Record<SolicitudArriendo['estado'], string> = {
    pendiente: 'Pendiente',
    pendiente_visita: 'Esperando confirmación de visita',
    visita_programada: 'Visita programada',
    contrato_generado: 'Contrato generado',
    aceptada: 'Aceptada',
    rechazada: 'Rechazada',
  };
  return labels[estado] ?? estado;
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function ArriendosList() {
  const user = useAuthStore((state) => state.user);
  const owner = user?.rol === 'propietario';

  const [requests, setRequests] = useState<SolicitudArriendo[]>([]);
  const [contracts, setContracts] = useState<Contrato[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tab, setTab] = useState<'solicitudes' | 'contratos'>('solicitudes');

  // Modal de responder visita
  const [visitaModal, setVisitaModal] = useState<SolicitudArriendo | null>(null);
  const [visitaDecision, setVisitaDecision] = useState<'visita_programada' | 'rechazada'>('visita_programada');
  const [fechaVisitaConfirmada, setFechaVisitaConfirmada] = useState('');
  const [savingVisita, setSavingVisita] = useState(false);

  // Modal de generar contrato
  const [contratoModal, setContratoModal] = useState<SolicitudArriendo | null>(null);
  const [savingContrato, setSavingContrato] = useState(false);

  const toDateInput = (date: Date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  };
  const today = toDateInput(new Date());
  const nextYearDate = new Date(); nextYearDate.setFullYear(nextYearDate.getFullYear() + 1);
  const nextYear = toDateInput(nextYearDate);

  const [contratoForm, setContratoForm] = useState({
    fecha_inicio: today,
    fecha_fin: nextYear,
    precio_acordado: '',
    trabaja: '',          // 'true' | 'false' | ''
    empresa: '',
    cargo: '',
    ingreso_mensual: '',
    fiador_nombre: '',
    fiador_cedula: '',
    fiador_telefono: '',
    clausulas_adicionales: '',
  });

  // ── Carga ──────────────────────────────────────────────────────────────────

  async function loadData() {
    setLoading(true);
    setError('');
    try {
      const [requestData, contractData] = await Promise.all([
        owner ? rentalsApi.received() : rentalsApi.mine(),
        rentalsApi.contracts(),
      ]);
      setRequests(requestData);
      setContracts(contractData);
    } catch (err) {
      setError(getApiError(err, 'No fue posible consultar la información de arriendos.'));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadData(); }, [user?.rol]);

  // ── Responder visita ───────────────────────────────────────────────────────

  function openVisitaModal(request: SolicitudArriendo, decision: 'visita_programada' | 'rechazada') {
    setVisitaModal(request);
    setVisitaDecision(decision);
    setFechaVisitaConfirmada(request.fecha_visita_propuesta ?? '');
    setError('');
  }

  async function submitVisita(event: FormEvent) {
    event.preventDefault();
    if (!visitaModal) return;
    setSavingVisita(true);
    setError('');
    try {
      await rentalsApi.responderVisita(visitaModal.id, {
        estado: visitaDecision,
        fecha_visita_confirmada: visitaDecision === 'visita_programada' ? fechaVisitaConfirmada || undefined : undefined,
      });
      setVisitaModal(null);
      setSuccess(
        visitaDecision === 'visita_programada'
          ? 'Visita confirmada. El interesado será notificado.'
          : 'Solicitud rechazada.'
      );
      await loadData();
    } catch (err) {
      setError(getApiError(err, 'No fue posible responder la solicitud.'));
    } finally {
      setSavingVisita(false);
    }
  }

  // ── Generar contrato ───────────────────────────────────────────────────────

  function openContratoModal(request: SolicitudArriendo) {
    setContratoModal(request);
    setContratoForm({
      fecha_inicio: today,
      fecha_fin: nextYear,
      precio_acordado: String(request.propiedad?.precio_mensual || ''),
      trabaja: '',
      empresa: '',
      cargo: '',
      ingreso_mensual: '',
      fiador_nombre: '',
      fiador_cedula: '',
      fiador_telefono: '',
      clausulas_adicionales: '',
    });
    setError('');
  }

  async function submitContrato(event: FormEvent) {
    event.preventDefault();
    if (!contratoModal) return;
    setSavingContrato(true);
    setError('');
    try {
      const payload: Parameters<typeof rentalsApi.generarContrato>[1] = {
        fecha_inicio: contratoForm.fecha_inicio,
        fecha_fin: contratoForm.fecha_fin,
        precio_acordado: contratoForm.precio_acordado ? Number(contratoForm.precio_acordado) : undefined,
        trabaja: contratoForm.trabaja === 'true' ? true : contratoForm.trabaja === 'false' ? false : undefined,
        empresa: contratoForm.empresa.trim() || undefined,
        cargo: contratoForm.cargo.trim() || undefined,
        ingreso_mensual: contratoForm.ingreso_mensual ? Number(contratoForm.ingreso_mensual) : undefined,
        fiador_nombre: contratoForm.fiador_nombre.trim() || undefined,
        fiador_cedula: contratoForm.fiador_cedula.trim() || undefined,
        fiador_telefono: contratoForm.fiador_telefono.trim() || undefined,
        clausulas_adicionales: contratoForm.clausulas_adicionales.trim() || undefined,
      };
      const result = await rentalsApi.generarContrato(contratoModal.id, payload);
      setContratoModal(null);
      setSuccess(`Contrato ${result.contrato?.numero_contrato ?? ''} generado con éxito. La propiedad quedó marcada como arrendada.`);
      await loadData();
    } catch (err) {
      setError(getApiError(err, 'No fue posible generar el contrato.'));
    } finally {
      setSavingContrato(false);
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  const pendingCount = requests.filter((r) =>
    r.estado === 'pendiente' || r.estado === 'pendiente_visita'
  ).length;

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="RELACIONES CONTRACTUALES"
        title={owner ? 'Solicitudes y contratos' : 'Mis arriendos'}
        description={
          owner
            ? 'Revisa las solicitudes recibidas, confirma visitas y formaliza contratos.'
            : 'Consulta las solicitudes que has enviado y los contratos asociados.'
        }
      />

      {error && !visitaModal && !contratoModal && <Alert>{error}</Alert>}
      {success && <Alert variant="success" onClose={() => setSuccess('')}>{success}</Alert>}

      <div className="rentals-summary">
        <div>
          <span className="eyebrow">SOLICITUDES</span>
          <strong>{requests.length}</strong>
          <small>{pendingCount} esperando respuesta</small>
        </div>
        <div>
          <span className="eyebrow">CONTRATOS</span>
          <strong>{contracts.length}</strong>
          <small>{contracts.filter((c) => c.estado === 'activo').length} activos</small>
        </div>
        <div className="rentals-summary-icon">
          <FileText size={34} strokeWidth={1.2} />
        </div>
      </div>

      <div className="tabs-bar">
        <button className={tab === 'solicitudes' ? 'tab-active' : ''} onClick={() => setTab('solicitudes')}>
          Solicitudes <span>{requests.length}</span>
        </button>
        <button className={tab === 'contratos' ? 'tab-active' : ''} onClick={() => setTab('contratos')}>
          Contratos <span>{contracts.length}</span>
        </button>
      </div>

      {loading ? (
        <LoadingState label="Consultando solicitudes y contratos..." />
      ) : tab === 'solicitudes' ? (
        requests.length === 0 ? (
          <EmptyState
            title="Todavía no hay solicitudes"
            description={
              owner
                ? 'Cuando alguien solicite uno de tus inmuebles, podrás revisar su información aquí.'
                : 'Cuando solicites un inmueble, verás aquí el estado de tu proceso.'
            }
          />
        ) : (
          <div className="request-list">
            {requests.map((request) => (
              <Panel className="request-card" key={request.id}>
                <div className="request-card-top">
                  <div>
                    <span className="eyebrow">SOLICITUD #{request.id}</span>
                    <h3>{request.propiedad?.titulo || `Propiedad #${request.propiedad_id}`}</h3>
                    <p className="request-subline">
                      {request.propiedad?.direccion || 'Dirección no disponible'}
                    </p>
                  </div>
                  <StatusBadge value={request.estado} label={estadoLabel(request.estado)} />
                </div>

                <div className="request-card-details">
                  {/* Columna: solicitante o fecha */}
                  <div>
                    <span>{owner ? 'SOLICITANTE' : 'FECHA DE SOLICITUD'}</span>
                    <strong>
                      {owner ? fullName(request.arrendatario) : dateLabel(request.fecha_solicitud)}
                    </strong>
                    {owner && <small>{request.arrendatario?.correo}</small>}
                  </div>

                  {/* Columna: canon */}
                  <div>
                    <span>CANON MENSUAL</span>
                    <strong>{money(request.propiedad?.precio_mensual)}</strong>
                  </div>

                  {/* Columna: visita */}
                  {request.fecha_visita_propuesta && (
                    <div>
                      <span>VISITA PROPUESTA</span>
                      <strong>{dateLabel(request.fecha_visita_propuesta)}</strong>
                      {request.fecha_visita_confirmada && (
                        <small>Confirmada: {dateLabel(request.fecha_visita_confirmada)}</small>
                      )}
                    </div>
                  )}

                  {/* Datos personales (solo para propietario) */}
                  {owner && (request.cedula_arrendatario || request.telefono_arrendatario) && (
                    <div>
                      <span>DATOS PERSONALES</span>
                      {request.cedula_arrendatario && (
                        <strong>CC {request.cedula_arrendatario}</strong>
                      )}
                      {request.telefono_arrendatario && (
                        <small>📱 {request.telefono_arrendatario}</small>
                      )}
                    </div>
                  )}

                  {/* Mensaje */}
                  <div>
                    <span>MENSAJE</span>
                    <strong className="request-message">
                      {request.mensaje || 'Sin mensaje adicional.'}
                    </strong>
                  </div>
                </div>

                {/* Nota de contrato */}
                {request.contrato && (
                  <div className="request-contract-note">
                    <Check size={15} />
                    {' '}Contrato {request.contrato.numero_contrato ?? `#${request.contrato.id}`} formalizado
                    {' '}· {dateLabel(request.contrato.fecha_inicio)} al {dateLabel(request.contrato.fecha_fin)}
                  </div>
                )}

                {/* Acciones del propietario */}
                {owner && (
                  <div className="request-actions">
                    {/* Paso 1: responder solicitud de visita */}
                    {(request.estado === 'pendiente' || request.estado === 'pendiente_visita') && (
                      <>
                        <Button variant="secondary" onClick={() => openVisitaModal(request, 'rechazada')}>
                          <X size={16} /> Rechazar solicitud
                        </Button>
                        <Button onClick={() => openVisitaModal(request, 'visita_programada')}>
                          <Check size={16} /> Confirmar visita
                        </Button>
                      </>
                    )}

                    {/* Paso 2: generar contrato después de la visita */}
                    {request.estado === 'visita_programada' && !request.contrato && (
                      <>
                        <Button variant="secondary" onClick={() => openVisitaModal(request, 'rechazada')}>
                          <X size={16} /> Rechazar definitivamente
                        </Button>
                        <Button onClick={() => openContratoModal(request)}>
                          <FileText size={16} /> Generar contrato
                        </Button>
                      </>
                    )}
                  </div>
                )}
              </Panel>
            ))}
          </div>
        )
      ) : contracts.length === 0 ? (
        <EmptyState
          title="Aún no tienes contratos"
          description="Los contratos aparecerán aquí cuando se formalice el arriendo de una propiedad."
        />
      ) : (
        <div className="contracts-grid">
          {contracts.map((contract) => (
            <Panel className="contract-card" key={contract.id}>
              <div className="contract-card-head">
                <div className="contract-icon"><FileText size={20} /></div>
                <StatusBadge value={contract.estado} />
              </div>
              <span className="eyebrow">
                {contract.numero_contrato ?? `CONTRATO #${contract.id}`}
              </span>
              <h3>Contrato de arrendamiento</h3>
              <div className="contract-price">
                {money(contract.precio_acordado)}<small>/ mes</small>
              </div>
              <div className="contract-dates">
                <div>
                  <CalendarDays size={15} /><span>Inicio</span>
                  <strong>{dateLabel(contract.fecha_inicio)}</strong>
                </div>
                <div>
                  <CalendarDays size={15} /><span>Finalización</span>
                  <strong>{dateLabel(contract.fecha_fin)}</strong>
                </div>
              </div>

              {/* Info laboral si existe */}
              {contract.trabaja !== null && contract.trabaja !== undefined && (
                <div className="contract-labor">
                  <User size={14} />
                  <span>
                    {contract.trabaja
                      ? `Trabaja${contract.empresa ? ` en ${contract.empresa}` : ''}${contract.cargo ? ` · ${contract.cargo}` : ''}${contract.ingreso_mensual ? ` · ${money(contract.ingreso_mensual)}/mes` : ''}`
                      : 'No trabaja actualmente'}
                  </span>
                </div>
              )}

              {contract.fiador_nombre && (
                <p className="contract-foot">
                  Fiador: {contract.fiador_nombre}
                  {contract.fiador_cedula ? ` · CC ${contract.fiador_cedula}` : ''}
                </p>
              )}

              <p className="contract-foot">Solicitud relacionada #{contract.solicitud_id}</p>
            </Panel>
          ))}
        </div>
      )}

      {/* ── MODAL: Responder visita ─────────────────────────────────────────── */}
      {visitaModal && (
        <Modal
          title={visitaDecision === 'visita_programada' ? 'Confirmar visita' : 'Rechazar solicitud'}
          onClose={() => setVisitaModal(null)}
        >
          <form className="modal-form" onSubmit={submitVisita}>
            {error && <Alert>{error}</Alert>}

            <p className="modal-intro">
              {visitaDecision === 'visita_programada'
                ? `Confirma la visita de ${fullName(visitaModal.arrendatario)} para el inmueble "${visitaModal.propiedad?.titulo}".`
                : `Confirma que deseas rechazar la solicitud de ${fullName(visitaModal.arrendatario)}.`}
            </p>

            {visitaDecision === 'visita_programada' && (
              <Field label="Fecha de visita confirmada" hint="Por defecto se usa la fecha propuesta por el interesado.">
                <input
                  className="text-input"
                  type="date"
                  value={fechaVisitaConfirmada}
                  onChange={(e) => setFechaVisitaConfirmada(e.target.value)}
                />
              </Field>
            )}

            {/* Resumen de datos del solicitante */}
            {(visitaModal.cedula_arrendatario || visitaModal.telefono_arrendatario) && (
              <div className="request-data-summary">
                <span className="eyebrow">DATOS DEL INTERESADO</span>
                {visitaModal.cedula_arrendatario && <p>Cédula: <strong>{visitaModal.cedula_arrendatario}</strong></p>}
                {visitaModal.telefono_arrendatario && <p>Celular: <strong>{visitaModal.telefono_arrendatario}</strong></p>}
                {visitaModal.fecha_visita_propuesta && <p>Fecha propuesta: <strong>{dateLabel(visitaModal.fecha_visita_propuesta)}</strong></p>}
              </div>
            )}

            <div className="modal-actions">
              <Button type="button" variant="secondary" onClick={() => setVisitaModal(null)}>
                Cancelar
              </Button>
              <Button
                type="submit"
                variant={visitaDecision === 'rechazada' ? 'danger' : 'primary'}
                disabled={savingVisita}
              >
                {savingVisita
                  ? 'Procesando...'
                  : visitaDecision === 'visita_programada'
                    ? 'Confirmar visita'
                    : 'Confirmar rechazo'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* ── MODAL: Generar contrato ─────────────────────────────────────────── */}
      {contratoModal && (
        <Modal
          title={`Generar contrato — ${contratoModal.propiedad?.titulo ?? ''}`}
          onClose={() => setContratoModal(null)}
          wide
        >
          <form className="modal-form" onSubmit={submitContrato}>
            {error && <Alert>{error}</Alert>}

            <p className="modal-intro">
              Completa la información para formalizar el contrato con{' '}
              <strong>{fullName(contratoModal.arrendatario)}</strong>.
              La propiedad quedará marcada como <strong>arrendada</strong>.
            </p>

            {/* Resumen del solicitante */}
            {(contratoModal.cedula_arrendatario || contratoModal.telefono_arrendatario) && (
              <div className="request-data-summary">
                <span className="eyebrow">DATOS DEL ARRENDATARIO</span>
                {contratoModal.cedula_arrendatario && <p>Cédula: <strong>{contratoModal.cedula_arrendatario}</strong></p>}
                {contratoModal.telefono_arrendatario && <p>Celular: <strong>{contratoModal.telefono_arrendatario}</strong></p>}
              </div>
            )}

            <div className="form-section-title">Vigencia del contrato</div>

            <div className="form-grid-two">
              <Field label="Fecha de inicio">
                <input
                  className="text-input"
                  type="date"
                  required
                  value={contratoForm.fecha_inicio}
                  onChange={(e) => setContratoForm((v) => ({ ...v, fecha_inicio: e.target.value }))}
                />
              </Field>
              <Field label="Fecha de finalización">
                <input
                  className="text-input"
                  type="date"
                  required
                  min={contratoForm.fecha_inicio}
                  value={contratoForm.fecha_fin}
                  onChange={(e) => setContratoForm((v) => ({ ...v, fecha_fin: e.target.value }))}
                />
              </Field>
            </div>

            <Field label="Precio mensual acordado (COP)">
              <input
                className="text-input"
                type="number"
                min="0"
                step="1000"
                value={contratoForm.precio_acordado}
                onChange={(e) => setContratoForm((v) => ({ ...v, precio_acordado: e.target.value }))}
              />
            </Field>

            <div className="form-section-title">Información laboral del arrendatario</div>

            <Field label="¿Trabaja actualmente?">
              <select
                className="text-input"
                value={contratoForm.trabaja}
                onChange={(e) => setContratoForm((v) => ({ ...v, trabaja: e.target.value }))}
              >
                <option value="">Sin especificar</option>
                <option value="true">Sí, trabaja</option>
                <option value="false">No trabaja actualmente</option>
              </select>
            </Field>

            {contratoForm.trabaja === 'true' && (
              <div className="form-grid-two">
                <Field label="Empresa">
                  <input
                    className="text-input"
                    maxLength={200}
                    value={contratoForm.empresa}
                    onChange={(e) => setContratoForm((v) => ({ ...v, empresa: e.target.value }))}
                    placeholder="Nombre de la empresa"
                  />
                </Field>
                <Field label="Cargo">
                  <input
                    className="text-input"
                    maxLength={200}
                    value={contratoForm.cargo}
                    onChange={(e) => setContratoForm((v) => ({ ...v, cargo: e.target.value }))}
                    placeholder="Cargo o posición"
                  />
                </Field>
                <Field label="Ingreso mensual (COP)">
                  <input
                    className="text-input"
                    type="number"
                    min="0"
                    step="10000"
                    value={contratoForm.ingreso_mensual}
                    onChange={(e) => setContratoForm((v) => ({ ...v, ingreso_mensual: e.target.value }))}
                  />
                </Field>
              </div>
            )}

            <div className="form-section-title">Fiador (opcional)</div>

            <div className="form-grid-two">
              <Field label="Nombre completo del fiador">
                <input
                  className="text-input"
                  maxLength={200}
                  value={contratoForm.fiador_nombre}
                  onChange={(e) => setContratoForm((v) => ({ ...v, fiador_nombre: e.target.value }))}
                  placeholder="Opcional"
                />
              </Field>
              <Field label="Cédula del fiador">
                <input
                  className="text-input"
                  maxLength={20}
                  value={contratoForm.fiador_cedula}
                  onChange={(e) => setContratoForm((v) => ({ ...v, fiador_cedula: e.target.value }))}
                  placeholder="Opcional"
                />
              </Field>
              <Field label="Celular del fiador">
                <input
                  className="text-input"
                  maxLength={20}
                  value={contratoForm.fiador_telefono}
                  onChange={(e) => setContratoForm((v) => ({ ...v, fiador_telefono: e.target.value }))}
                  placeholder="Opcional"
                />
              </Field>
            </div>

            <div className="form-section-title">Cláusulas adicionales (opcional)</div>

            <Field label="Condiciones especiales del contrato" hint="Por ejemplo: mascotas, parqueadero, etc.">
              <textarea
                className="text-input textarea-input"
                rows={3}
                maxLength={5000}
                value={contratoForm.clausulas_adicionales}
                onChange={(e) => setContratoForm((v) => ({ ...v, clausulas_adicionales: e.target.value }))}
                placeholder="Ej: Se permite una mascota pequeña. Parqueadero incluido..."
              />
            </Field>

            <div className="modal-actions">
              <Button type="button" variant="secondary" onClick={() => setContratoModal(null)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={savingContrato}>
                {savingContrato ? 'Generando contrato...' : 'Formalizar contrato'}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
