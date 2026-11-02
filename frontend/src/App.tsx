import { useEffect, useState, type ReactNode } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { LoaderCircle } from 'lucide-react';
import { authApi } from './api/services';
import { useAuthStore } from './store/authStore';
import type { Rol } from './types';
import AuthLayout from './layouts/AuthLayout';
import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import Dashboard from './pages/Dashboard';
import PropiedadesList from './pages/propiedades/PropiedadesList';
import ArriendosList from './pages/arriendos/ArriendosList';
import UsuariosList from './pages/usuarios/UsuariosList';
import IAMarketing from './pages/marketing/IAMarketing';
import Profile from './pages/perfil/Profile';
import Catalogos from './pages/catalogos/Catalogos';

function Bootstrap() {
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const finishBootstrap = useAuthStore((state) => state.finishBootstrap);
  const [ready, setReady] = useState(!token);

  useEffect(() => {
    let active = true;
    if (!token) {
      setReady(true);
      finishBootstrap();
      return () => { active = false; };
    }
    if (!user) {
      authApi.profile()
        .then((profile) => { if (active) setUser(profile); })
        .catch(() => { /* Axios interceptor clears invalid JWTs. */ })
        .finally(() => { if (active) { finishBootstrap(); setReady(true); } });
    } else {
      finishBootstrap();
      setReady(true);
    }
    return () => { active = false; };
  }, [token, user, setUser, finishBootstrap]);

  if (!ready) return <div className="app-loading"><LoaderCircle className="animate-spin" size={28} /><span>Preparando tu espacio RENTIO...</span></div>;
  return <AppRoutes />;
}

function AppRoutes() {
  const authenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const Protected = ({ children, roles }: { children: ReactNode; roles?: Rol[] }) => {
    if (!authenticated) return <Navigate to="/login" replace />;
    if (roles && user && !roles.includes(user.rol)) return <Navigate to="/dashboard" replace />;
    return children;
  };
  const Guest = ({ children }: { children: ReactNode }) => authenticated ? <Navigate to="/dashboard" replace /> : children;

  return <Routes>
    <Route element={<AuthLayout />}>
      <Route path="/login" element={<Guest><Login /></Guest>} />
      <Route path="/register" element={<Guest><Register /></Guest>} />
    </Route>
    <Route path="/" element={<Protected><DashboardLayout /></Protected>}>
      <Route index element={<Navigate to="/dashboard" replace />} />
      <Route path="dashboard" element={<Dashboard />} />
      <Route path="propiedades" element={<Protected><PropiedadesList /></Protected>} />
      <Route path="arriendos" element={<Protected roles={['arrendatario', 'propietario']}><ArriendosList /></Protected>} />
      <Route path="usuarios" element={<Protected roles={['admin']}><UsuariosList /></Protected>} />
      <Route path="catalogos" element={<Protected roles={['admin']}><Catalogos /></Protected>} />
      <Route path="marketing-ia" element={<Protected roles={['propietario']}><IAMarketing /></Protected>} />
      <Route path="perfil" element={<Profile />} />
    </Route>
    <Route path="*" element={<Navigate to={authenticated ? '/dashboard' : '/login'} replace />} />
  </Routes>;
}

export default function App() {
  return <BrowserRouter><Bootstrap /></BrowserRouter>;
}
