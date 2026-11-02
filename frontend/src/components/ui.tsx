import type { ReactNode, ElementType, ButtonHTMLAttributes } from 'react';
import { AlertCircle, CheckCircle2, Loader2, Search, X } from 'lucide-react';

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {action && <div className="page-action">{action}</div>}
    </div>
  );
}

export function Button({ children, variant = 'primary', size = 'md', className = '', ...props }: Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'size'> & { variant?: 'primary' | 'secondary' | 'danger' | 'ghost'; size?: 'sm' | 'md' }) {
  return <button className={`button button-${variant} button-${size} ${className}`} {...props}>{children}</button>;
}

export function Panel({ children, className = '', id }: { children: ReactNode; className?: string; id?: string }) {
  return <section id={id} className={`panel ${className}`}>{children}</section>;
}

export function StatCard({ label, value, detail, icon: Icon, tone = 'blue' }: { label: string; value: string | number; detail?: string; icon: ElementType; tone?: 'blue' | 'teal' | 'amber' | 'violet' }) {
  return (
    <div className="stat-card">
      <div className={`stat-icon tone-${tone}`}><Icon size={21} /></div>
      <div className="min-w-0"><p className="stat-label">{label}</p><p className="stat-value">{value}</p>{detail && <p className="stat-detail">{detail}</p>}</div>
    </div>
  );
}

export function StatusBadge({ value }: { value: string }) {
  const labels: Record<string, string> = { propietario: 'Propietario', arrendatario: 'Arrendatario', admin: 'Administrador', disponible: 'Disponible', arrendada: 'Arrendada', inactiva: 'Inactiva', pendiente: 'Pendiente', aceptada: 'Aceptada', rechazada: 'Rechazada', activo: 'Activo', finalizado: 'Finalizado', cancelado: 'Cancelado', recopilando: 'Recopilando', lista: 'Lista', generada: 'Generada', cerrada: 'Cerrada' };
  const styles: Record<string, string> = {
    disponible: 'status-green', pendiente: 'status-amber', aceptada: 'status-green', activa: 'status-green', activo: 'status-green',
    arrendada: 'status-blue', rechazada: 'status-red', inactiva: 'status-gray', finalizado: 'status-gray', cancelado: 'status-red',
    recopilando: 'status-blue', lista: 'status-green', generada: 'status-violet', cerrada: 'status-gray',
  };
  return <span className={`status-badge ${styles[value?.toLowerCase()] || 'status-gray'}`}>{labels[value?.toLowerCase()] || value || 'Sin estado'}</span>;
}

export function LoadingState({ label = 'Cargando información...' }: { label?: string }) {
  return <div className="loading-state"><Loader2 className="animate-spin" size={22} /><span>{label}</span></div>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return <div className="empty-state"><div className="empty-symbol"><Search size={23} /></div><h3>{title}</h3><p>{description}</p>{action && <div className="mt-4">{action}</div>}</div>;
}

export function Alert({ children, variant = 'error', onClose }: { children: ReactNode; variant?: 'error' | 'success' | 'info'; onClose?: () => void }) {
  const Icon = variant === 'success' ? CheckCircle2 : AlertCircle;
  return <div className={`alert alert-${variant}`} role="status"><Icon size={18} /><div className="min-w-0">{children}</div>{onClose && <button className="ml-auto" onClick={onClose} aria-label="Cerrar"><X size={16} /></button>}</div>;
}

export function Modal({ title, children, onClose, wide = false }: { title: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  return <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <div className={`modal-card ${wide ? 'modal-wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}>
      <div className="modal-header"><h2>{title}</h2><button className="icon-button" onClick={onClose} aria-label="Cerrar"><X size={19} /></button></div>
      {children}
    </div>
  </div>;
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return <label className="form-field"><span className="field-label">{label}</span>{children}{hint && <span className="field-hint">{hint}</span>}</label>;
}
