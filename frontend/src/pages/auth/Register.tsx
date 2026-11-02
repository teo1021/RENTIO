import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Building2, User } from 'lucide-react';
import { authApi } from '../../api/services';
import { getApiError } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { Alert, Button } from '../../components/ui';

export default function Register() {
  const [form, setForm] = useState({ nombre: '', apellido: '', correo: '', contrasena: '', rol: 'arrendatario' as 'arrendatario' | 'propietario' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const login = useAuthStore((state) => state.login);
  const navigate = useNavigate();
  const update = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError('');
    try {
      await authApi.register({ ...form, correo: form.correo.trim().toLowerCase() });
      const session = await authApi.login(form.correo.trim().toLowerCase(), form.contrasena);
      login(session.usuario, session.token);
      navigate('/dashboard', { replace: true });
    } catch (err) { setError(getApiError(err, 'No fue posible crear la cuenta. Revisa los datos e inténtalo de nuevo.')); }
    finally { setLoading(false); }
  }

  return <div className="auth-form-wrap auth-register-wrap">
    <div className="auth-mobile-brand"><span className="brand-mark"><Building2 size={19} /></span> rentio<span className="brand-dot">.</span></div>
    <div className="auth-heading"><span className="eyebrow">EMPIEZA CON RENTIO</span><h2>Crea tu cuenta.</h2><p>Un espacio organizado para encontrar o gestionar tu próximo arriendo.</p></div>
    {error && <Alert>{error}</Alert>}
    <form className="auth-form" onSubmit={handleSubmit}>
      <div className="form-grid-two"><label className="form-field"><span className="field-label">Nombre</span><input className="text-input" required maxLength={100} value={form.nombre} onChange={(e) => update('nombre', e.target.value)} placeholder="Tu nombre" /></label><label className="form-field"><span className="field-label">Apellido</span><input className="text-input" maxLength={100} value={form.apellido} onChange={(e) => update('apellido', e.target.value)} placeholder="Tu apellido" /></label></div>
      <label className="form-field"><span className="field-label">Correo electrónico</span><input className="text-input" type="email" required value={form.correo} onChange={(e) => update('correo', e.target.value)} placeholder="nombre@correo.com" /></label>
      <label className="form-field"><span className="field-label">Contraseña</span><input className="text-input" type="password" required minLength={8} value={form.contrasena} onChange={(e) => update('contrasena', e.target.value)} placeholder="Mínimo 8 caracteres" /><span className="field-hint">Utiliza al menos 8 caracteres.</span></label>
      <div className="form-field"><span className="field-label">¿Cómo usarás RENTIO?</span><div className="role-choice-grid">
        <button type="button" onClick={() => update('rol', 'arrendatario')} className={`role-choice ${form.rol === 'arrendatario' ? 'role-choice-active' : ''}`}><User size={19} /><span><strong>Busco arriendo</strong><small>Quiero encontrar un inmueble.</small></span><i /></button>
        <button type="button" onClick={() => update('rol', 'propietario')} className={`role-choice ${form.rol === 'propietario' ? 'role-choice-active' : ''}`}><Building2 size={19} /><span><strong>Ofrezco propiedades</strong><small>Quiero gestionar mis inmuebles.</small></span><i /></button>
      </div></div>
      <Button type="submit" disabled={loading} className="auth-submit">{loading ? 'Creando cuenta...' : 'Crear cuenta'} <ArrowRight size={17} /></Button>
    </form>
    <p className="auth-switch">¿Ya tienes una cuenta? <Link to="/login">Iniciar sesión</Link></p>
  </div>;
}
