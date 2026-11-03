import { useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, Building2, FileText, Users, Sparkles, LogOut, Menu, X,
  UserRound, Settings2, ChevronDown, ArrowUpRight,
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { authApi } from '../api/services';
import { fullName, initials } from '../lib/format';
import type { Rol } from '../types';

const allNavigation = [
  { label: 'Resumen', path: '/dashboard', icon: LayoutDashboard, roles: ['arrendatario', 'propietario', 'admin'] },
  { label: 'Propiedades', path: '/propiedades', icon: Building2, roles: ['arrendatario', 'propietario', 'admin'] },
  { label: 'Arriendos', path: '/arriendos', icon: FileText, roles: ['arrendatario', 'propietario'] },
  { label: 'Marketing IA', path: '/marketing-ia', icon: Sparkles, roles: ['propietario'] },
  { label: 'Usuarios', path: '/usuarios', icon: Users, roles: ['admin'] },
  { label: 'Catálogos', path: '/catalogos', icon: Settings2, roles: ['admin'] },
];

const roleLabels: Record<Rol, string> = { propietario: 'Propietario', arrendatario: 'Arrendatario', admin: 'Administrador' };

export default function DashboardLayout() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const switchSession = useAuthStore((state) => state.switchSession);
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [switchingRole, setSwitchingRole] = useState(false);
  const availableRoles = user?.roles || [user?.rol];
  const canSwitchRole = availableRoles.includes('arrendatario') && availableRoles.includes('propietario');
  async function changeRole(role: 'arrendatario' | 'propietario') {
    if (!user || role === user.rol || switchingRole) return;
    setSwitchingRole(true);
    try {
      const session = await authApi.switchRole(role);
      switchSession(session.usuario, session.token);
      setProfileOpen(false);
      navigate('/dashboard', { replace: true });
    } catch (error) {
      console.error('No fue posible cambiar el modo de RENTIO.', error);
    } finally { setSwitchingRole(false); }
  }
  const navigation = useMemo(() => allNavigation.filter((item) => user && item.roles.includes(user.rol)), [user]);
  const current = navigation.find((item) => location.pathname === item.path);
  const name = fullName(user);

  const signOut = () => { logout(); navigate('/login', { replace: true }); };
  const navContent = <>
    <div className="sidebar-brand"><span className="brand-mark"><Building2 size={21} /></span><span>rentio<span className="brand-dot">.</span></span><span className="brand-beta">APP</span></div>
    <div className="sidebar-section-label">ESPACIO DE TRABAJO</div>
    <nav className="sidebar-nav">
      {navigation.map((item) => <NavLink key={item.path} to={item.path} onClick={() => setMobileOpen(false)} className={({ isActive }) => `nav-item ${isActive ? 'nav-item-active' : ''}`}>
        <item.icon size={18} strokeWidth={1.8} /><span>{item.label}</span>{item.path === '/marketing-ia' && <span className="nav-new">IA</span>}
      </NavLink>)}
    </nav>
    <div className="sidebar-bottom">
      <div className="sidebar-help"><div className="help-icon"><Sparkles size={17} /></div><div><strong>¿Necesitas ayuda?</strong><span>Estamos para orientarte.</span></div><ArrowUpRight size={15} /></div>
      <button className="sidebar-logout" onClick={signOut}><LogOut size={17} /> Cerrar sesión</button>
      <div className="sidebar-user"><div className="avatar">{initials(name)}</div><div className="sidebar-user-copy"><strong>{name}</strong><span>{user ? roleLabels[user.rol] : 'Cuenta'}</span></div><button className="user-more" onClick={() => navigate('/perfil')} aria-label="Abrir perfil"><ArrowUpRight size={16} /></button></div>
    </div>
  </>;

  return <div className="app-shell">
    <aside className="sidebar">{navContent}</aside>
    {mobileOpen && <div className="mobile-sidebar-backdrop" onClick={() => setMobileOpen(false)}><aside className="mobile-sidebar" onClick={(e) => e.stopPropagation()}><button className="mobile-close" onClick={() => setMobileOpen(false)}><X size={20} /></button>{navContent}</aside></div>}
    <div className="workspace">
      <header className="topbar">
        <div className="topbar-left"><button className="mobile-menu-button" onClick={() => setMobileOpen(true)} aria-label="Abrir menú"><Menu size={21} /></button><div className="breadcrumb"><span>RENTIO</span><span className="breadcrumb-separator">/</span><strong>{current?.label || (location.pathname === '/perfil' ? 'Mi perfil' : 'Panel')}</strong></div></div>
        <div className="topbar-actions"><span className="topbar-date">Medellín, Colombia</span><div className="profile-menu-wrap"><button className="topbar-profile" onClick={() => setProfileOpen((open) => !open)}><div className="avatar avatar-small">{initials(name)}</div><span>{name}</span><ChevronDown size={15} /></button>{profileOpen && <div className="profile-dropdown">{canSwitchRole && <><button disabled={switchingRole} onClick={() => changeRole(user?.rol === 'propietario' ? 'arrendatario' : 'propietario')}><Building2 size={16} /> {switchingRole ? 'Cambiando...' : user?.rol === 'propietario' ? 'Cambiar a arrendatario' : 'Cambiar a propietario'}</button><div className="profile-dropdown-divider" /></>}<button onClick={() => { setProfileOpen(false); navigate('/perfil'); }}><UserRound size={16} /> Mi perfil</button><button onClick={signOut}><LogOut size={16} /> Cerrar sesión</button></div>}</div></div>
      </header>
      <main className="main-content"><div className="content-inner"><Outlet /></div><footer className="app-footer"><span>© {new Date().getFullYear()} RENTIO</span><span>Gestión de arriendos · Medellín</span></footer></main>
    </div>
  </div>;
}
