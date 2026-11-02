import { useEffect, useMemo, useState } from 'react';
import { Building2, Search, ShieldCheck, UserRound, Users } from 'lucide-react';
import { adminApi } from '../../api/services';
import { getApiError } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { dateLabel, fullName, initials } from '../../lib/format';
import type { Usuario } from '../../types';
import { Alert, EmptyState, LoadingState, PageHeader, Panel, StatusBadge } from '../../components/ui';

export default function UsuariosList() {
  const currentUser = useAuthStore((state) => state.user);
  const [users, setUsers] = useState<Usuario[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [changingId, setChangingId] = useState<number | null>(null);

  async function load() {
    setLoading(true); setError('');
    try { setUsers(await adminApi.users()); }
    catch (err) { setError(getApiError(err, 'No fue posible cargar los usuarios.')); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function changeRole(user: Usuario, rol: Usuario['rol']) {
    if (rol === user.rol) return;
    setChangingId(user.id); setError(''); setSuccess('');
    try { const updated = await adminApi.changeRole(user.id, rol); setUsers((items) => items.map((item) => item.id === user.id ? updated : item)); setSuccess(`El rol de ${user.correo} se actualizó a ${rol}.`); }
    catch (err) { setError(getApiError(err, 'No fue posible cambiar el rol.')); }
    finally { setChangingId(null); }
  }

  const filtered = useMemo(() => users.filter((user) => `${user.correo} ${fullName(user)} ${user.rol}`.toLowerCase().includes(search.toLowerCase())), [users, search]);
  const counts = { propietario: users.filter((u) => u.rol === 'propietario').length, arrendatario: users.filter((u) => u.rol === 'arrendatario').length, admin: users.filter((u) => u.rol === 'admin').length };

  return <div className="page-stack">
    <PageHeader eyebrow="ADMINISTRACIÓN" title="Gestión de usuarios" description="Consulta las cuentas registradas y administra sus permisos dentro de la plataforma." />
    {error && <Alert>{error}</Alert>}{success && <Alert variant="success" onClose={() => setSuccess('')}>{success}</Alert>}
    <div className="stats-grid stats-grid-four"><div className="mini-stat"><span className="mini-stat-icon mini-blue"><Users size={18} /></span><div><strong>{users.length}</strong><small>Usuarios registrados</small></div></div><div className="mini-stat"><span className="mini-stat-icon mini-teal"><Building2 size={18} /></span><div><strong>{counts.propietario}</strong><small>Propietarios</small></div></div><div className="mini-stat"><span className="mini-stat-icon mini-violet"><UserRound size={18} /></span><div><strong>{counts.arrendatario}</strong><small>Arrendatarios</small></div></div><div className="mini-stat"><span className="mini-stat-icon mini-blue"><ShieldCheck size={18} /></span><div><strong>{counts.admin}</strong><small>Administradores</small></div></div></div>
    <Panel className="table-panel"><div className="table-toolbar"><div><h2>Directorio de cuentas</h2><p>{filtered.length} resultados</p></div><div className="search-box search-box-compact"><Search size={17} /><input placeholder="Buscar usuario..." value={search} onChange={(e) => setSearch(e.target.value)} /></div></div>
      {loading ? <LoadingState label="Cargando usuarios..." /> : filtered.length === 0 ? <EmptyState title="No hay usuarios" description="No encontramos cuentas con ese criterio de búsqueda." /> : <div className="table-scroll"><table className="data-table"><thead><tr><th>Usuario</th><th>Correo</th><th>Fecha de registro</th><th>Rol actual</th><th>Permisos</th></tr></thead><tbody>{filtered.map((user) => <tr key={user.id}><td><div className="user-cell"><span className="avatar avatar-table">{initials(fullName(user))}</span><div><strong>{fullName(user)}</strong><small>ID #{user.id}</small></div></div></td><td>{user.correo}</td><td>{dateLabel(user.fecha_creacion)}</td><td><StatusBadge value={user.rol} /></td><td>{user.id === currentUser?.id ? <span className="muted-inline">Tu cuenta</span> : <select className="role-select" value={user.rol} disabled={changingId === user.id} onChange={(e) => changeRole(user, e.target.value as Usuario['rol'])}><option value="arrendatario">Arrendatario</option><option value="propietario">Propietario</option><option value="admin">Administrador</option></select>}</td></tr>)}</tbody></table></div>}
    </Panel>
    <div className="info-strip"><ShieldCheck size={18} /><span>Los cambios de rol se validan en el backend. Tu propia cuenta no se modifica desde esta pantalla.</span></div>
  </div>;
}
