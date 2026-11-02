import { useState, type FormEvent } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail } from 'lucide-react';
import { authApi } from '../../api/services';
import { getApiError } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Alert, Button } from '../../components/ui';

export default function Login() {
  const [correo, setCorreo] = useState('');
  const [contrasena, setContrasena] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [params] = useSearchParams();
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true); setError('');
    try {
      const result = await authApi.login(correo.trim().toLowerCase(), contrasena);
      login(result.usuario, result.token);
      navigate('/dashboard', { replace: true });
    } catch (err) { setError(getApiError(err, 'No fue posible iniciar sesión. Verifica tus datos.')); }
    finally { setLoading(false); }
  }

  return <div className="auth-form-wrap">
    <div className="auth-mobile-brand"><span className="brand-mark"><LockKeyhole size={19} /></span> rentio<span className="brand-dot">.</span></div>
    <div className="auth-heading"><span className="eyebrow">BIENVENIDO DE NUEVO</span><h2>Qué bueno tenerte aquí.</h2><p>Ingresa a tu cuenta para continuar gestionando tus arriendos.</p></div>
    {params.get('expired') && <Alert variant="info">Tu sesión terminó. Inicia sesión nuevamente para continuar.</Alert>}
    {error && <Alert>{error}</Alert>}
    <form className="auth-form" onSubmit={handleSubmit}>
      <label className="form-field"><span className="field-label">Correo electrónico</span><div className="input-icon-wrap"><Mail size={17} /><input className="text-input with-icon" type="email" autoComplete="email" required value={correo} onChange={(e) => setCorreo(e.target.value)} placeholder="nombre@correo.com" /></div></label>
      <label className="form-field"><span className="field-label">Contraseña</span><div className="input-icon-wrap"><LockKeyhole size={17} /><input className="text-input with-icon" type={showPassword ? 'text' : 'password'} autoComplete="current-password" required value={contrasena} onChange={(e) => setContrasena(e.target.value)} placeholder="Tu contraseña" /><button className="password-toggle" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button></div></label>
      <Button type="submit" disabled={loading} className="auth-submit">{loading ? 'Ingresando...' : 'Iniciar sesión'} <ArrowRight size={17} /></Button>
    </form>
    <p className="auth-switch">¿Todavía no tienes una cuenta? <Link to="/register">Crear cuenta</Link></p>
    <p className="auth-security"><LockKeyhole size={13} /> Tu sesión está protegida mediante autenticación segura.</p>
  </div>;
}
