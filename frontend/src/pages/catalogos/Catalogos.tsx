import { useEffect, useState, type FormEvent } from 'react';
import { MapPin, Plus, Tags } from 'lucide-react';
import { catalogsApi } from '../../api/services';
import { getApiError } from '../../api/client';
import type { Barrio, Caracteristica } from '../../types';
import { Alert, Button, EmptyState, Field, LoadingState, PageHeader, Panel } from '../../components/ui';

export default function Catalogos() {
  const [barrios, setBarrios] = useState<Barrio[]>([]);
  const [features, setFeatures] = useState<Caracteristica[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [barrioForm, setBarrioForm] = useState({ nombre: '', comuna: '', zona: '' });
  const [featureForm, setFeatureForm] = useState({ nombre: '', icono: '' });

  async function load() {
    setLoading(true); setError('');
    try { const [b, f] = await Promise.all([catalogsApi.neighborhoods(), catalogsApi.features()]); setBarrios(b); setFeatures(f); }
    catch (err) { setError(getApiError(err, 'No fue posible cargar los catálogos.')); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);

  async function createBarrio(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try { await catalogsApi.createNeighborhood(barrioForm); setBarrioForm({ nombre: '', comuna: '', zona: '' }); setSuccess('Barrio agregado al catálogo.'); await load(); }
    catch (err) { setError(getApiError(err, 'No fue posible crear el barrio.')); }
    finally { setSaving(false); }
  }

  async function createFeature(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try { await catalogsApi.createFeature({ nombre: featureForm.nombre, icono: featureForm.icono || undefined }); setFeatureForm({ nombre: '', icono: '' }); setSuccess('Característica agregada al catálogo.'); await load(); }
    catch (err) { setError(getApiError(err, 'No fue posible crear la característica.')); }
    finally { setSaving(false); }
  }

  return <div className="page-stack"><PageHeader eyebrow="CONFIGURACIÓN DEL SISTEMA" title="Catálogos" description="Administra los barrios de Medellín y las características disponibles para describir los inmuebles." />
    {error && <Alert>{error}</Alert>}{success && <Alert variant="success" onClose={() => setSuccess('')}>{success}</Alert>}
    {loading ? <LoadingState label="Cargando catálogos..." /> : <div className="catalog-grid">
      <Panel className="catalog-panel"><div className="panel-heading"><div><span className="eyebrow">UBICACIONES</span><h2>Barrios</h2><p>Los barrios aparecen en los formularios de propiedades y filtros.</p></div><div className="catalog-count">{barrios.length}</div></div><form onSubmit={createBarrio} className="catalog-form"><Field label="Nombre del barrio"><input className="text-input" required minLength={2} maxLength={100} value={barrioForm.nombre} onChange={(e) => setBarrioForm((v) => ({ ...v, nombre: e.target.value }))} placeholder="Ej. Laureles" /></Field><div className="form-grid-two"><Field label="Comuna"><input className="text-input" required minLength={2} maxLength={100} value={barrioForm.comuna} onChange={(e) => setBarrioForm((v) => ({ ...v, comuna: e.target.value }))} placeholder="Ej. Laureles - Estadio" /></Field><Field label="Zona"><input className="text-input" required minLength={2} maxLength={100} value={barrioForm.zona} onChange={(e) => setBarrioForm((v) => ({ ...v, zona: e.target.value }))} placeholder="Ej. Centro-occidental" /></Field></div><Button type="submit" disabled={saving}><Plus size={16} /> Agregar barrio</Button></form><div className="catalog-list-title">Barrios registrados</div>{barrios.length ? <div className="catalog-list">{barrios.map((barrio) => <div className="catalog-row" key={barrio.id}><span className="catalog-row-icon"><MapPin size={16} /></span><div><strong>{barrio.nombre}</strong><small>{barrio.comuna} · {barrio.zona}</small></div></div>)}</div> : <EmptyState title="Sin barrios" description="No hay barrios registrados." />}</Panel>
      <Panel className="catalog-panel"><div className="panel-heading"><div><span className="eyebrow">DETALLES DEL INMUEBLE</span><h2>Características</h2><p>Amenidades que pueden asociarse a cada propiedad.</p></div><div className="catalog-count">{features.length}</div></div><form onSubmit={createFeature} className="catalog-form"><Field label="Nombre de la característica"><input className="text-input" required minLength={2} maxLength={100} value={featureForm.nombre} onChange={(e) => setFeatureForm((v) => ({ ...v, nombre: e.target.value }))} placeholder="Ej. Parqueadero cubierto" /></Field><Field label="Identificador de icono (opcional)"><input className="text-input" maxLength={100} value={featureForm.icono} onChange={(e) => setFeatureForm((v) => ({ ...v, icono: e.target.value }))} placeholder="Ej. parking" /></Field><Button type="submit" disabled={saving}><Plus size={16} /> Agregar característica</Button></form><div className="catalog-list-title">Características registradas</div>{features.length ? <div className="feature-cloud">{features.map((feature) => <span className="feature-chip" key={feature.id}><Tags size={14} />{feature.nombre}</span>)}</div> : <EmptyState title="Sin características" description="Todavía no hay amenidades registradas." />}</Panel>
    </div>}
    <div className="info-strip"><MapPin size={18} /><span>La creación de barrios y características utiliza los endpoints administrativos existentes; no modifica directamente la base de datos.</span></div>
  </div>;
}
