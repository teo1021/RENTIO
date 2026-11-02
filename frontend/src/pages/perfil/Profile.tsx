import { useEffect, useState, type FormEvent } from 'react';
import { Save, ShieldCheck, UserRound } from 'lucide-react';
import { authApi } from '../../api/services';
import { getApiError } from '../../api/client';
import { useAuthStore } from '../../store/authStore';
import { fullName } from '../../lib/format';
import type { Usuario } from '../../types';
import { Alert, Button, Field, LoadingState, PageHeader, Panel } from '../../components/ui';

export default function Profile() {
  const current = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [profile, setProfile] = useState({ nombre: '', apellido: '', telefono: '', cedula: '', foto_perfil: '' });
  const [email, setEmail] = useState(current?.correo || '');
  const [role, setRole] = useState(current?.rol || 'arrendatario');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    let active = true;
    authApi.profile().then((user) => {
      if (!active) return;
      setUser(user); setEmail(user.correo); setRole(user.rol);
      setProfile({ nombre: user.perfil?.nombre || '', apellido: user.perfil?.apellido || '', telefono: user.perfil?.telefono || '', cedula: user.perfil?.cedula || '', foto_perfil: user.perfil?.foto_perfil || '' });
    }).catch((err) => { if (active) setError(getApiError(err, 'No fue posible consultar tu perfil.')); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [setUser]);

  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try {
      const updated: Usuario = await authApi.updateProfile(profile);
      setUser(updated);
      setProfile({ nombre: updated.perfil?.nombre || '', apellido: updated.perfil?.apellido || '', telefono: updated.perfil?.telefono || '', cedula: updated.perfil?.cedula || '', foto_perfil: updated.perfil?.foto_perfil || '' });
      setSuccess('Tu perfil se actualizó correctamente.');
    } catch (err) { setError(getApiError(err, 'No fue posible guardar los cambios.')); }
    finally { setSaving(false); }
  }

  return <div className="page-stack"><PageHeader eyebrow="TU CUENTA" title="Mi perfil" description="Mantén actualizada tu información de contacto y los datos de tu cuenta." />
    {error && <Alert>{error}</Alert>}{success && <Alert variant="success" onClose={() => setSuccess('')}>{success}</Alert>}
    {loading ? <LoadingState label="Cargando perfil..." /> : <div className="profile-layout"><Panel className="profile-summary"><div className="profile-avatar-large">{profile.foto_perfil ? <img src={profile.foto_perfil} alt="Foto de perfil" onError={(e) => { e.currentTarget.style.display = 'none'; }} /> : <UserRound size={35} />}</div><h2>{fullName({ correo: email, perfil: profile })}</h2><p>{email}</p><span className="profile-role"><ShieldCheck size={14} /> {role === 'admin' ? 'Administrador' : role === 'propietario' ? 'Propietario' : 'Arrendatario'}</span><div className="profile-summary-note">Tu rol y correo se administran desde la cuenta. Los datos editables corresponden a tu perfil personal.</div></Panel>
      <Panel className="profile-form-panel"><div className="panel-heading"><div><span className="eyebrow">INFORMACIÓN PERSONAL</span><h2>Datos de contacto</h2></div></div><form className="modal-form" onSubmit={submit}><div className="form-grid-two"><Field label="Nombre"><input className="text-input" maxLength={100} value={profile.nombre} onChange={(e) => setProfile((v) => ({ ...v, nombre: e.target.value }))} placeholder="Tu nombre" /></Field><Field label="Apellido"><input className="text-input" maxLength={100} value={profile.apellido} onChange={(e) => setProfile((v) => ({ ...v, apellido: e.target.value }))} placeholder="Tu apellido" /></Field></div><Field label="Correo electrónico"><input className="text-input text-input-disabled" value={email} disabled /></Field><div className="form-grid-two"><Field label="Teléfono"><input className="text-input" maxLength={20} value={profile.telefono} onChange={(e) => setProfile((v) => ({ ...v, telefono: e.target.value }))} placeholder="300 000 0000" /></Field><Field label="Documento de identidad"><input className="text-input" maxLength={20} value={profile.cedula} onChange={(e) => setProfile((v) => ({ ...v, cedula: e.target.value }))} placeholder="Número de documento" /></Field></div><Field label="URL de foto de perfil" hint="Opcional. Puedes utilizar una imagen accesible mediante una URL pública."><input className="text-input" maxLength={500} value={profile.foto_perfil} onChange={(e) => setProfile((v) => ({ ...v, foto_perfil: e.target.value }))} placeholder="https://..." /></Field><div className="modal-actions"><Button type="submit" disabled={saving}>{saving ? 'Guardando...' : 'Guardar cambios'} <Save size={16} /></Button></div></form></Panel></div>}
  </div>;
}
