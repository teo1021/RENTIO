import { useEffect, useMemo, useState } from 'react';
import { Activity, ArrowRight, Building2, CalendarDays, CheckCircle2, ClipboardList, FileText, Home, Sparkles, Users, Wallet } from 'lucide-react';
import { Link } from 'react-router-dom';
import { adminApi, propertiesApi, rentalsApi } from '../api/services';
import { getApiError } from '../api/client';
import { useAuthStore } from '../store/authStore';
import { fullName, dateLabel, money } from '../lib/format';
import { Alert, EmptyState, LoadingState, PageHeader, Panel, StatCard, StatusBadge } from '../components/ui';
import type { Contrato, Propiedad, SolicitudArriendo, Usuario } from '../types';

export default function Dashboard() {
  const user = useAuthStore((state) => state.user);
  const [properties, setProperties] = useState<Propiedad[]>([]);
  const [requests, setRequests] = useState<SolicitudArriendo[]>([]);
  const [contracts, setContracts] = useState<Contrato[]>([]);
  const [users, setUsers] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const role = user?.rol;

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true); setError('');
      try {
        const requestsToLoad: Promise<unknown>[] = [];
        if (role === 'propietario') {
          requestsToLoad.push(propertiesApi.mine(), rentalsApi.received(), rentalsApi.contracts());
          const [props, reqs, contractsData] = await Promise.all(requestsToLoad) as [Propiedad[], SolicitudArriendo[], Contrato[]];
          if (active) { setProperties(props); setRequests(reqs); setContracts(contractsData); }
        } else if (role === 'arrendatario') {
          const [props, reqs, contractsData] = await Promise.all([propertiesApi.listPublic({}), rentalsApi.mine(), rentalsApi.contracts()]);
          if (active) { setProperties(props.filter((p) => p.estado === 'disponible')); setRequests(reqs); setContracts(contractsData); }
        } else if (role === 'admin') {
          const [props, usersData] = await Promise.all([propertiesApi.listPublic({}), adminApi.users()]);
          if (active) { setProperties(props); setUsers(usersData); }
        }
      } catch (err) { if (active) setError(getApiError(err, 'No fue posible cargar el resumen.')); }
      finally { if (active) setLoading(false); }
    }
    if (role) load();
    return () => { active = false; };
  }, [role]);

  const available = useMemo(() => properties.filter((p) => p.estado === 'disponible').length, [properties]);
  const activeContracts = contracts.filter((c) => c.estado === 'activo').length;
  const pending = requests.filter((r) => r.estado === 'pendiente').length;
  const titleByRole = role === 'propietario' ? 'Administra con claridad.' : role === 'arrendatario' ? 'Encuentra tu próximo hogar.' : 'Todo bajo control.';

  return <div className="page-stack">
    <PageHeader eyebrow="PANEL GENERAL" title={titleByRole} description={`Hola, ${fullName(user)}. Este es el estado actual de tu espacio en RENTIO.`} />
    {error && <Alert>{error}</Alert>}
    {loading ? <LoadingState label="Consultando información real del sistema..." /> : <>
      <div className="welcome-banner"><div><span className="welcome-kicker">TU ESPACIO RENTIO</span><h2>{role === 'propietario' ? 'Tu portafolio, mejor organizado.' : role === 'arrendatario' ? 'Un buen lugar empieza con una buena búsqueda.' : 'Una visión completa de la plataforma.'}</h2><p>{role === 'propietario' ? 'Controla tus inmuebles, atiende solicitudes y utiliza herramientas inteligentes para publicar mejor.' : role === 'arrendatario' ? 'Explora inmuebles disponibles y sigue el estado de tus solicitudes desde un solo lugar.' : 'Consulta el inventario publicado y administra los usuarios registrados.'}</p></div><div className="welcome-art"><div className="welcome-art-circle"><Building2 size={54} strokeWidth={1.1} /></div><span className="art-spark art-spark-one">✦</span><span className="art-spark art-spark-two">✧</span></div></div>
      <div className="stats-grid">
        {role === 'propietario' && <><StatCard label="Mis propiedades" value={properties.length} detail={`${available} disponibles`} icon={Building2} tone="blue" /><StatCard label="Solicitudes pendientes" value={pending} detail="Requieren tu respuesta" icon={ClipboardList} tone="amber" /><StatCard label="Contratos activos" value={activeContracts} detail={`${contracts.length} en total`} icon={FileText} tone="teal" /><StatCard label="Valor mensual activo" value={money(contracts.filter((c) => c.estado === 'activo').reduce((sum, c) => sum + Number(c.precio_acordado || 0), 0))} detail="Según contratos activos" icon={Wallet} tone="violet" /></>}
        {role === 'arrendatario' && <><StatCard label="Inmuebles disponibles" value={available} detail="Publicados en la plataforma" icon={Home} tone="blue" /><StatCard label="Mis solicitudes" value={requests.length} detail={`${pending} pendientes`} icon={ClipboardList} tone="amber" /><StatCard label="Contratos activos" value={activeContracts} detail="Arriendos formalizados" icon={FileText} tone="teal" /></>}
        {role === 'admin' && <><StatCard label="Propiedades publicadas" value={properties.length} detail={`${available} disponibles`} icon={Building2} tone="blue" /><StatCard label="Usuarios registrados" value={users.length} detail="Todas las cuentas" icon={Users} tone="teal" /><StatCard label="Propiedades arrendadas" value={properties.filter((p) => p.estado === 'arrendada').length} detail="Inventario ocupado" icon={Home} tone="violet" /><StatCard label="Propiedades inactivas" value={properties.filter((p) => p.estado === 'inactiva').length} detail="Fuera de publicación" icon={Activity} tone="amber" /></>}
      </div>
      <div className="dashboard-columns">
        <Panel className="dashboard-main-panel"><div className="panel-heading"><div><span className="eyebrow">ACTIVIDAD RECIENTE</span><h2>{role === 'propietario' ? 'Solicitudes por atender' : role === 'arrendatario' ? 'Tus solicitudes' : 'Propiedades recientes'}</h2></div><Link className="text-link" to={role === 'admin' ? '/propiedades' : role === 'propietario' || role === 'arrendatario' ? '/arriendos' : '/propiedades'}>Ver todo <ArrowRight size={15} /></Link></div>
          {role === 'admin' ? (properties.length ? <div className="activity-list">{properties.slice(0, 5).map((p) => <div className="activity-row" key={p.id}><div className="activity-icon"><Building2 size={18} /></div><div className="activity-copy"><strong>{p.titulo}</strong><span>{p.barrio?.nombre || p.direccion}</span></div><StatusBadge value={p.estado} /><span className="activity-value">{money(p.precio_mensual)}</span></div>)}</div> : <EmptyState title="Sin propiedades" description="Todavía no hay inmuebles registrados en la plataforma." />) : requests.length ? <div className="activity-list">{requests.slice(0, 6).map((r) => <div className="activity-row" key={r.id}><div className="activity-icon"><FileText size={18} /></div><div className="activity-copy"><strong>{r.propiedad?.titulo || `Solicitud #${r.id}`}</strong><span>{role === 'propietario' ? r.arrendatario?.correo : `Enviada el ${dateLabel(r.fecha_solicitud)}`}</span></div><StatusBadge value={r.estado} /><span className="activity-value">{r.propiedad?.precio_mensual ? money(r.propiedad.precio_mensual) : ''}</span></div>)}</div> : <EmptyState title="Todo está al día" description={role === 'propietario' ? 'Cuando recibas solicitudes de arriendo, aparecerán aquí.' : 'Cuando envíes una solicitud por un inmueble, podrás seguirla desde aquí.'} action={<Link to={role === 'propietario' ? '/propiedades' : '/propiedades'} className="button button-secondary">{role === 'propietario' ? 'Ver mis propiedades' : 'Explorar propiedades'}</Link>} />}
        </Panel>
        <Panel className="quick-panel"><div className="panel-heading"><div><span className="eyebrow">ACCESOS RÁPIDOS</span><h2>¿Qué necesitas hacer?</h2></div></div>
          <div className="quick-links">
            {role === 'propietario' && <><Link to="/propiedades" className="quick-link"><span className="quick-icon quick-blue"><Building2 size={18} /></span><span><strong>Gestionar propiedades</strong><small>Actualiza tu inventario</small></span><ArrowRight size={16} /></Link><Link to="/arriendos" className="quick-link"><span className="quick-icon quick-amber"><ClipboardList size={18} /></span><span><strong>Revisar solicitudes</strong><small>Responde a interesados</small></span><ArrowRight size={16} /></Link><Link to="/marketing-ia" className="quick-link"><span className="quick-icon quick-violet"><Sparkles size={18} /></span><span><strong>Asistente de marketing IA</strong><small>Mejora tus publicaciones</small></span><ArrowRight size={16} /></Link></>}
            {role === 'arrendatario' && <><Link to="/propiedades" className="quick-link"><span className="quick-icon quick-blue"><Home size={18} /></span><span><strong>Explorar inmuebles</strong><small>Encuentra opciones disponibles</small></span><ArrowRight size={16} /></Link><Link to="/arriendos" className="quick-link"><span className="quick-icon quick-amber"><FileText size={18} /></span><span><strong>Seguir mis solicitudes</strong><small>Consulta su estado</small></span><ArrowRight size={16} /></Link></>}
            {role === 'admin' && <><Link to="/usuarios" className="quick-link"><span className="quick-icon quick-blue"><Users size={18} /></span><span><strong>Administrar usuarios</strong><small>Consulta y gestiona roles</small></span><ArrowRight size={16} /></Link><Link to="/catalogos" className="quick-link"><span className="quick-icon quick-violet"><Settings2Icon /></span><span><strong>Administrar catálogos</strong><small>Barrios y características</small></span><ArrowRight size={16} /></Link></>}
            <Link to="/perfil" className="quick-link"><span className="quick-icon quick-teal"><CalendarDays size={18} /></span><span><strong>Actualizar mi perfil</strong><small>Mantén tus datos al día</small></span><ArrowRight size={16} /></Link>
          </div>
        </Panel>
      </div>
      <div className="dashboard-footnote"><CheckCircle2 size={16} /><span>Los indicadores de este panel se consultan directamente desde el backend de RENTIO. No se utilizan cifras de demostración.</span></div>
    </>}
  </div>;
}

function Settings2Icon() { return <ClipboardList size={18} />; }
