import { useEffect, useState, type FormEvent } from 'react';
import { CalendarDays, Check, FileText, X } from 'lucide-react';
import { rentalsApi } from '../../api/services';
import { getApiError } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { dateLabel, fullName, money } from '../../lib/format';
import type { Contrato, SolicitudArriendo } from '../../types';
import { Alert, Button, EmptyState, Field, LoadingState, Modal, PageHeader, Panel, StatusBadge } from '../../components/ui';

export default function ArriendosList() {
  const user = useAuthStore((state) => state.user);
  const owner = user?.rol === 'propietario';
  const [requests, setRequests] = useState<SolicitudArriendo[]>([]);
  const [contracts, setContracts] = useState<Contrato[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [tab, setTab] = useState<'solicitudes' | 'contratos'>('solicitudes');
  const [selected, setSelected] = useState<SolicitudArriendo | null>(null);
  const [decision, setDecision] = useState<'aceptada' | 'rechazada'>('aceptada');
  // Los campos date usan la fecha local del navegador; toISOString() convertiría a UTC
  // y podría adelantar o atrasar el día en zonas horarias como America/Bogota.
  const toDateInput = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  const currentDate = new Date();
  const today = toDateInput(currentDate);
  const nextYearDate = new Date(currentDate);
  nextYearDate.setFullYear(nextYearDate.getFullYear() + 1);
  const nextYear = toDateInput(nextYearDate);
  const [contractForm, setContractForm] = useState({ fecha_inicio: today, fecha_fin: nextYear, precio_acordado: '' });
  const [saving, setSaving] = useState(false);

  async function loadData() {
    setLoading(true); setError('');
    try {
      const [requestData, contractData] = await Promise.all([
        owner ? rentalsApi.received() : rentalsApi.mine(), rentalsApi.contracts(),
      ]);
      setRequests(requestData); setContracts(contractData);
    } catch (err) { setError(getApiError(err, 'No fue posible consultar la información de arriendos.')); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadData(); }, [user?.rol]);

  function openDecision(request: SolicitudArriendo, value: 'aceptada' | 'rechazada') {
    setSelected(request); setDecision(value); setContractForm({ fecha_inicio: today, fecha_fin: nextYear, precio_acordado: String(request.propiedad?.precio_mensual || '') }); setError('');
  }

  async function submitDecision(event: FormEvent) {
    event.preventDefault(); if (!selected) return;
    setSaving(true); setError('');
    try {
      const payload = decision === 'aceptada'
        ? { estado: decision, fecha_inicio: contractForm.fecha_inicio, fecha_fin: contractForm.fecha_fin, precio_acordado: contractForm.precio_acordado ? Number(contractForm.precio_acordado) : undefined }
        : { estado: decision };
      await rentalsApi.respond(selected.id, payload);
      setSelected(null); setSuccess(decision === 'aceptada' ? 'Solicitud aceptada. El backend formalizó el contrato y actualizó la propiedad.' : 'La solicitud fue rechazada.');
      await loadData();
    } catch (err) { setError(getApiError(err, 'No fue posible responder la solicitud.')); }
    finally { setSaving(false); }
  }

  const pendingCount = requests.filter((item) => item.estado === 'pendiente').length;

  return <div className="page-stack">
    <PageHeader eyebrow="RELACIONES CONTRACTUALES" title={owner ? 'Solicitudes y contratos' : 'Mis arriendos'} description={owner ? 'Revisa las solicitudes recibidas y administra los contratos que se formalizan desde la plataforma.' : 'Consulta las solicitudes que has enviado y los contratos asociados a tus arriendos.'} />
    {error && !selected && <Alert>{error}</Alert>}{success && <Alert variant="success" onClose={() => setSuccess('')}>{success}</Alert>}
    <div className="rentals-summary"><div><span className="eyebrow">SOLICITUDES</span><strong>{requests.length}</strong><small>{pendingCount} pendientes de respuesta</small></div><div><span className="eyebrow">CONTRATOS</span><strong>{contracts.length}</strong><small>{contracts.filter((c) => c.estado === 'activo').length} activos</small></div><div className="rentals-summary-icon"><FileText size={34} strokeWidth={1.2} /></div></div>
    <div className="tabs-bar"><button className={tab === 'solicitudes' ? 'tab-active' : ''} onClick={() => setTab('solicitudes')}>Solicitudes <span>{requests.length}</span></button><button className={tab === 'contratos' ? 'tab-active' : ''} onClick={() => setTab('contratos')}>Contratos <span>{contracts.length}</span></button></div>
    {loading ? <LoadingState label="Consultando solicitudes y contratos..." /> : tab === 'solicitudes' ? requests.length === 0 ? <EmptyState title="Todavía no hay solicitudes" description={owner ? 'Cuando alguien solicite uno de tus inmuebles, podrás revisar su información aquí.' : 'Cuando solicites un inmueble, verás aquí el estado de tu proceso.'} /> : <div className="request-list">{requests.map((request) => <Panel className="request-card" key={request.id}><div className="request-card-top"><div><span className="eyebrow">SOLICITUD #{request.id}</span><h3>{request.propiedad?.titulo || `Propiedad #${request.propiedad_id}`}</h3><p className="request-subline">{request.propiedad?.direccion || 'Dirección no disponible'}</p></div><StatusBadge value={request.estado} /></div><div className="request-card-details"><div><span>{owner ? 'SOLICITANTE' : 'FECHA DE SOLICITUD'}</span><strong>{owner ? fullName(request.arrendatario) : dateLabel(request.fecha_solicitud)}</strong>{owner && <small>{request.arrendatario?.correo}</small>}</div><div><span>CANON MENSUAL</span><strong>{money(request.propiedad?.precio_mensual)}</strong></div><div><span>MENSAJE</span><strong className="request-message">{request.mensaje || 'Sin mensaje adicional.'}</strong></div></div>
          {request.contrato && <div className="request-contract-note"><Check size={15} /> Contrato #{request.contrato.id} formalizado · {dateLabel(request.contrato.fecha_inicio)} al {dateLabel(request.contrato.fecha_fin)}</div>}
          {owner && request.estado === 'pendiente' && <div className="request-actions"><Button variant="secondary" onClick={() => openDecision(request, 'rechazada')}><X size={16} /> Rechazar</Button><Button onClick={() => openDecision(request, 'aceptada')}><Check size={16} /> Aceptar y crear contrato</Button></div>}
        </Panel>)}</div> : contracts.length === 0 ? <EmptyState title="Aún no tienes contratos" description="Los contratos aparecerán aquí cuando una solicitud de arriendo sea aceptada y formalizada." /> : <div className="contracts-grid">{contracts.map((contract) => <Panel className="contract-card" key={contract.id}><div className="contract-card-head"><div className="contract-icon"><FileText size={20} /></div><StatusBadge value={contract.estado} /></div><span className="eyebrow">CONTRATO #{contract.id}</span><h3>Contrato de arrendamiento</h3><div className="contract-price">{money(contract.precio_acordado)}<small>/ mes</small></div><div className="contract-dates"><div><CalendarDays size={15} /><span>Inicio</span><strong>{dateLabel(contract.fecha_inicio)}</strong></div><div><CalendarDays size={15} /><span>Finalización</span><strong>{dateLabel(contract.fecha_fin)}</strong></div></div><p className="contract-foot">Solicitud relacionada #{contract.solicitud_id}</p></Panel>)}</div>}

    {selected && <Modal title={decision === 'aceptada' ? 'Aceptar solicitud y formalizar' : 'Rechazar solicitud'} onClose={() => setSelected(null)}>
      <form className="modal-form" onSubmit={submitDecision}>{error && <Alert>{error}</Alert>}<p className="modal-intro">{decision === 'aceptada' ? `Al aceptar la solicitud de ${fullName(selected.arrendatario)}, el backend creará el contrato y cambiará el estado de la propiedad a arrendada.` : `Confirma que deseas rechazar la solicitud para ${selected.propiedad?.titulo || 'esta propiedad'}.`}</p>
        {decision === 'aceptada' && <><div className="form-grid-two"><Field label="Fecha de inicio"><input className="text-input" type="date" required value={contractForm.fecha_inicio} onChange={(e) => setContractForm((v) => ({ ...v, fecha_inicio: e.target.value }))} /></Field><Field label="Fecha de finalización"><input className="text-input" type="date" required min={contractForm.fecha_inicio} value={contractForm.fecha_fin} onChange={(e) => setContractForm((v) => ({ ...v, fecha_fin: e.target.value }))} /></Field></div><Field label="Precio mensual acordado (COP)"><input className="text-input" type="number" min="0" step="1000" value={contractForm.precio_acordado} onChange={(e) => setContractForm((v) => ({ ...v, precio_acordado: e.target.value }))} /></Field></>}
        <div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setSelected(null)}>Cancelar</Button><Button type="submit" variant={decision === 'rechazada' ? 'danger' : 'primary'} disabled={saving}>{saving ? 'Procesando...' : decision === 'aceptada' ? 'Confirmar y crear contrato' : 'Confirmar rechazo'}</Button></div>
      </form>
    </Modal>}
  </div>;
}
