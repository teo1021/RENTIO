import { Outlet, Link } from 'react-router-dom';
import { Building2, ShieldCheck, Sparkles } from 'lucide-react';

export default function AuthLayout() {
  return <div className="auth-shell">
    <section className="auth-showcase">
      <Link to="/login" className="brand-lockup"><span className="brand-mark"><Building2 size={22} /></span><span>rentio<span className="brand-dot">.</span></span></Link>
      <div className="auth-showcase-copy">
        <div className="showcase-tag"><Sparkles size={14} /> Gestión inmobiliaria inteligente</div>
        <h1>Tu patrimonio,<br /><em>en buenas manos.</em></h1>
        <p>Administra propiedades, organiza solicitudes y toma mejores decisiones para tus arriendos desde un solo lugar.</p>
        <div className="showcase-points"><span><ShieldCheck size={17} /> Información centralizada</span><span><Sparkles size={17} /> Herramientas con IA</span></div>
      </div>
      <div className="showcase-footer">RENTIO · Medellín, Colombia</div>
      <div className="showcase-orb orb-one" /><div className="showcase-orb orb-two" />
    </section>
    <section className="auth-content"><div className="auth-content-inner"><Outlet /><p className="auth-legal">Al continuar, aceptas utilizar RENTIO de forma responsable y segura.</p></div></section>
  </div>;
}
