import React, { useState } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────
type AppMode = "auth" | "arrendador" | "arrendatario";

type Screen =
  | "login"
  | "registro"
  | "dashboard"
  | "propiedades"
  | "inquilinos"
  | "perfil-inquilino"
  | "contratos"
  | "pagos"
  | "evaluacion"
  | "evaluacion-resultado"
  | "notificaciones"
  | "configuracion";

type ScreenArrendatario =
  | "at-inicio"
  | "at-buscar"
  | "at-contrato"
  | "at-pagos"
  | "at-perfil";

// ─── Data ─────────────────────────────────────────────────────────────────────
const inquilinos = [
  { id: 1, nombre: "Camila Restrepo Álvarez", doc: "1.026.432.198", propiedad: "Cra 43 #67-12 Apto 301", estado: "Activo", pagos: "Al día", score: 88, riesgo: "Bajo", ingresosRatio: 3.2, retrasos: 0, incidentes: 0 },
  { id: 2, nombre: "Jorge Andrés Méndez", doc: "71.245.637", propiedad: "Cll 10 #34-56 Casa", estado: "Activo", pagos: "Retrasado", score: 54, riesgo: "Medio", ingresosRatio: 2.1, retrasos: 3, incidentes: 1 },
  { id: 3, nombre: "Lucía Fernández Torres", doc: "1.152.874.320", propiedad: "Cra 65 #48-90 Local 2", estado: "Activo", pagos: "Al día", score: 76, riesgo: "Bajo", ingresosRatio: 2.8, retrasos: 1, incidentes: 0 },
  { id: 4, nombre: "Ricardo Salazar Ospina", doc: "98.765.432", propiedad: "Cll 34 #70-15 Apto 202", estado: "Por vencer", pagos: "Pendiente", score: 38, riesgo: "Alto", ingresosRatio: 1.6, retrasos: 6, incidentes: 2 },
];

const propiedades = [
  { id: 1, dir: "Cra 43 #67-12 Apto 301", tipo: "Apartamento", valor: 950000, estado: "Arrendada", inquilino: "Camila Restrepo", contrato: "CON-2024-001" },
  { id: 2, dir: "Cll 10 #34-56 Casa", tipo: "Casa", valor: 1200000, estado: "Arrendada", inquilino: "Jorge Méndez", contrato: "CON-2024-002" },
  { id: 3, dir: "Cra 65 #48-90 Local 2", tipo: "Local comercial", valor: 1800000, estado: "Arrendada", inquilino: "Lucía Fernández", contrato: "CON-2024-003" },
  { id: 4, dir: "Cll 34 #70-15 Apto 202", tipo: "Apartamento", valor: 750000, estado: "Disponible", inquilino: "—", contrato: "—" },
  { id: 5, dir: "Cra 52 #80-21 Apto 105", tipo: "Apartamento", valor: 850000, estado: "Disponible", inquilino: "—", contrato: "—" },
];

const contratos = [
  { id: "CON-2024-001", inquilino: "Camila Restrepo", propiedad: "Cra 43 #67-12", inicio: "01/02/2024", fin: "31/01/2025", canon: 950000, estado: "Activo" },
  { id: "CON-2024-002", inquilino: "Jorge Méndez", propiedad: "Cll 10 #34-56", inicio: "15/03/2024", fin: "14/03/2025", canon: 1200000, estado: "Activo" },
  { id: "CON-2024-003", inquilino: "Lucía Fernández", propiedad: "Cra 65 #48-90", inicio: "01/05/2024", fin: "30/04/2025", canon: 1800000, estado: "Activo" },
  { id: "CON-2023-004", inquilino: "Ricardo Salazar", propiedad: "Cll 34 #70-15", inicio: "01/09/2023", fin: "31/08/2024", canon: 750000, estado: "Por vencer" },
];

const pagos = [
  { id: 1, inquilino: "Camila Restrepo", propiedad: "Cra 43 #67-12", fecha: "01/08/2024", valor: 950000, estado: "Pagado", retraso: 0 },
  { id: 2, inquilino: "Jorge Méndez", propiedad: "Cll 10 #34-56", fecha: "15/08/2024", valor: 1200000, estado: "Retrasado", retraso: 12 },
  { id: 3, inquilino: "Lucía Fernández", propiedad: "Cra 65 #48-90", fecha: "01/09/2024", valor: 1800000, estado: "Pendiente", retraso: 0 },
  { id: 4, inquilino: "Ricardo Salazar", propiedad: "Cll 34 #70-15", fecha: "01/08/2024", valor: 750000, estado: "Retrasado", retraso: 28 },
];

const notificaciones = [
  { id: 1, tipo: "riesgo-alto", titulo: "Riesgo alto detectado", desc: "Ricardo Salazar — Score 38/100. Se recomienda revisar el contrato antes del vencimiento.", hora: "Hace 2 horas", leida: false },
  { id: 2, tipo: "pago-retrasado", titulo: "Pago retrasado", desc: "Jorge Méndez lleva 12 días de retraso en el pago de agosto.", hora: "Hace 5 horas", leida: false },
  { id: 3, tipo: "contrato-vence", titulo: "Contrato próximo a vencer", desc: "El contrato CON-2023-004 de Ricardo Salazar vence el 31 de agosto.", hora: "Ayer", leida: false },
  { id: 4, tipo: "pago-retrasado", titulo: "Pago retrasado", desc: "Ricardo Salazar lleva 28 días de retraso.", hora: "Hace 3 días", leida: true },
  { id: 5, tipo: "pago-proximo", titulo: "Pago próximo", desc: "El pago de Lucía Fernández vence el 1 de septiembre.", hora: "Hace 3 días", leida: true },
  { id: 6, tipo: "evaluacion", titulo: "Evaluación disponible", desc: "Se recomienda evaluar nuevamente a Jorge Méndez.", hora: "Hace 5 días", leida: true },
];

// ─── Utilities ────────────────────────────────────────────────────────────────
const fmt = (n: number) => `$${n.toLocaleString("es-CO")}`;

function scoreColor(score: number) {
  if (score >= 70) return { bg: "#f0fdf4", text: "#16a34a", bar: "#16a34a" };
  if (score >= 50) return { bg: "#fffbeb", text: "#d97706", bar: "#f59e0b" };
  return { bg: "#fef2f2", text: "#dc2626", bar: "#ef4444" };
}

function estadoBadge(estado: string) {
  const map: Record<string, string> = {
    Activo: "bg-green-50 text-green-700 border-green-200",
    Disponible: "bg-blue-50 text-blue-700 border-blue-200",
    Arrendada: "bg-purple-50 text-purple-700 border-purple-200",
    "Por vencer": "bg-amber-50 text-amber-700 border-amber-200",
    Pagado: "bg-green-50 text-green-700 border-green-200",
    Pendiente: "bg-blue-50 text-blue-700 border-blue-200",
    Retrasado: "bg-red-50 text-red-700 border-red-200",
    Borrador: "bg-slate-50 text-slate-600 border-slate-200",
    Finalizado: "bg-slate-50 text-slate-500 border-slate-200",
    "Al día": "bg-green-50 text-green-700 border-green-200",
  };
  return map[estado] || "bg-slate-50 text-slate-600 border-slate-200";
}

function riesgoBadge(r: string) {
  const map: Record<string, string> = {
    Bajo: "bg-green-50 text-green-700",
    Medio: "bg-amber-50 text-amber-700",
    Alto: "bg-red-50 text-red-700",
  };
  return map[r] || "";
}

// ─── Icons (inline SVG) ───────────────────────────────────────────────────────
const Icon = ({ name, size = 18, className = "" }: { name: string; size?: number; className?: string }) => {
  const paths: Record<string, React.ReactElement> = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></>,
    building: <><path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-4h6v4"/></>,
    users: <><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></>,
    file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></>,
    creditCard: <><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></>,
    shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></>,
    bell: <><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></>,
    search: <><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></>,
    chevronRight: <><polyline points="9 18 15 12 9 6"/></>,
    chevronDown: <><polyline points="6 9 12 15 18 9"/></>,
    plus: <><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></>,
    eye: <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>,
    edit: <><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
    alertTriangle: <><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
    checkCircle: <><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></>,
    clock: <><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></>,
    trendingUp: <><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></>,
    x: <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
    check: <><polyline points="20 6 9 17 4 12"/></>,
    logout: <><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></>,
    lock: <><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></>,
    user: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></>,
    info: <><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></>,
    star: <><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></>,
    menu: <><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      {paths[name]}
    </svg>
  );
};

// ─── Reusable Components ──────────────────────────────────────────────────────
function Badge({ label, className = "" }: { label: string; className?: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${estadoBadge(label)} ${className}`}>
      {label}
    </span>
  );
}

function ScoreGauge({ score }: { score: number }) {
  const c = scoreColor(score);
  const riesgo = score >= 70 ? "BAJO" : score >= 50 ? "MEDIO" : "ALTO";
  const prob = Math.round(100 - score);
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative w-32 h-32 flex items-center justify-center rounded-full" style={{ background: `conic-gradient(${c.bar} ${score * 3.6}deg, #e2e8f0 0deg)` }}>
        <div className="w-24 h-24 bg-white rounded-full flex flex-col items-center justify-center shadow-inner">
          <span className="text-2xl font-bold" style={{ color: c.text, fontFamily: "Plus Jakarta Sans, sans-serif" }}>{score}</span>
          <span className="text-xs text-slate-400 font-medium">/ 100</span>
        </div>
      </div>
      <div className="flex flex-col items-center">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Riesgo</span>
        <span className="text-lg font-bold" style={{ color: c.text, fontFamily: "Plus Jakarta Sans, sans-serif" }}>{riesgo}</span>
        <span className="text-xs text-slate-500">Prob. incumplimiento: <strong>{prob}%</strong></span>
      </div>
    </div>
  );
}

function Card({ children, className = "", style }: { children: React.ReactNode; className?: string; style?: React.CSSProperties }) {
  return <div className={`bg-white rounded-xl border border-slate-100 shadow-sm ${className}`} style={style}>{children}</div>;
}

function StatCard({ label, value, sub, icon, color = "blue" }: { label: string; value: string | number; sub?: string; icon: string; color?: string }) {
  const colorMap: Record<string, string> = { blue: "bg-blue-50 text-blue-600", green: "bg-green-50 text-green-600", amber: "bg-amber-50 text-amber-600", red: "bg-red-50 text-red-600", purple: "bg-purple-50 text-purple-600" };
  return (
    <Card className="p-5 flex gap-4 items-start">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${colorMap[color]}`}>
        <Icon name={icon} size={18} />
      </div>
      <div>
        <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-slate-800 mt-0.5" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </Card>
  );
}

function Btn({ children, variant = "primary", size = "md", onClick, className = "", disabled = false }: {
  children: React.ReactNode; variant?: "primary" | "secondary" | "ghost" | "danger"; size?: "sm" | "md";
  onClick?: () => void; className?: string; disabled?: boolean;
}) {
  const v = {
    primary: "bg-blue-700 text-white hover:bg-blue-800 shadow-sm",
    secondary: "bg-white text-slate-700 border border-slate-200 hover:bg-slate-50",
    ghost: "text-slate-600 hover:bg-slate-100",
    danger: "bg-red-600 text-white hover:bg-red-700",
  }[variant];
  const s = size === "sm" ? "px-3 py-1.5 text-xs" : "px-4 py-2 text-sm";
  return (
    <button onClick={onClick} disabled={disabled}
      className={`inline-flex items-center gap-1.5 font-medium rounded-lg transition-colors ${v} ${s} ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"} ${className}`}>
      {children}
    </button>
  );
}

function Input({ label, type = "text", placeholder = "", value, onChange, required }: { label: string; type?: string; placeholder?: string; value?: string; onChange?: (v: string) => void; required?: boolean }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-slate-700">{label}{required && <span className="text-red-500 ml-0.5">*</span>}</label>
      <input type={type} placeholder={placeholder} value={value}
        onChange={e => onChange?.(e.target.value)}
        className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-slate-800 placeholder:text-slate-400" />
    </div>
  );
}

function Select({ label, options, value, onChange }: { label: string; options: string[]; value?: string; onChange?: (v: string) => void }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-slate-700">{label}</label>
      <select value={value} onChange={e => onChange?.(e.target.value)}
        className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white text-slate-800 cursor-pointer">
        {options.map(o => <option key={o}>{o}</option>)}
      </select>
    </div>
  );
}

function Modal({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: React.ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md z-10" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h3 className="font-bold text-slate-800" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{title}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 cursor-pointer"><Icon name="x" size={18} /></button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}

function EmptyState({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4 text-slate-400">
        <Icon name={icon} size={24} />
      </div>
      <p className="font-semibold text-slate-700 mb-1" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{title}</p>
      <p className="text-sm text-slate-400 max-w-xs">{desc}</p>
    </div>
  );
}

// ─── Sidebar ─────────────────────────────────────────────────────────────────
const navItems = [
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "propiedades", label: "Propiedades", icon: "building" },
  { id: "inquilinos", label: "Inquilinos", icon: "users" },
  { id: "contratos", label: "Contratos", icon: "file" },
  { id: "pagos", label: "Pagos", icon: "creditCard" },
  { id: "evaluacion", label: "Evaluación de riesgo", icon: "shield" },
  { id: "notificaciones", label: "Notificaciones", icon: "bell" },
  { id: "configuracion", label: "Configuración", icon: "settings" },
] as const;

function Sidebar({ current, onChange, collapsed, onToggle }: { current: Screen; onChange: (s: Screen) => void; collapsed: boolean; onToggle: () => void }) {
  const unread = notificaciones.filter(n => !n.leida).length;
  return (
    <aside className={`flex flex-col h-full bg-white border-r border-slate-100 transition-all duration-300 ${collapsed ? "w-16" : "w-60"} flex-shrink-0`}>
      {/* Logo */}
      <div className={`flex items-center gap-2.5 px-4 py-5 border-b border-slate-100 ${collapsed ? "justify-center" : ""}`}>
        <div className="w-8 h-8 rounded-lg bg-blue-700 flex items-center justify-center flex-shrink-0">
          <Icon name="building" size={16} className="text-white" />
        </div>
        {!collapsed && <span className="text-lg font-bold text-blue-700 tracking-tight" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>RENTIO</span>}
      </div>
      {/* Nav */}
      <nav className="flex-1 py-4 overflow-y-auto">
        {navItems.map(item => {
          const active = current === item.id;
          return (
            <button key={item.id} onClick={() => onChange(item.id as Screen)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer relative
                ${active ? "bg-blue-50 text-blue-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"}
                ${collapsed ? "justify-center" : ""}`}>
              {active && <span className="absolute left-0 top-1 bottom-1 w-0.5 bg-blue-700 rounded-r" />}
              <Icon name={item.icon} size={17} />
              {!collapsed && <span>{item.label}</span>}
              {!collapsed && item.id === "notificaciones" && unread > 0 && (
                <span className="ml-auto text-xs bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center font-bold">{unread}</span>
              )}
              {collapsed && item.id === "notificaciones" && unread > 0 && (
                <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
              )}
            </button>
          );
        })}
      </nav>
      {/* Collapse toggle */}
      <div className="p-3 border-t border-slate-100">
        <button onClick={onToggle} className={`w-full flex items-center gap-2 px-2 py-2 text-xs text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg cursor-pointer ${collapsed ? "justify-center" : ""}`}>
          <Icon name="menu" size={16} />
          {!collapsed && "Colapsar"}
        </button>
      </div>
    </aside>
  );
}

// ─── Header ───────────────────────────────────────────────────────────────────
function Header({ screen, onNav }: { screen: Screen; onNav: (s: Screen) => void }) {
  const titles: Record<Screen, string> = {
    login: "", registro: "", dashboard: "Dashboard", propiedades: "Propiedades", inquilinos: "Inquilinos",
    "perfil-inquilino": "Perfil del Inquilino", contratos: "Contratos", pagos: "Pagos",
    evaluacion: "Evaluación de Riesgo", "evaluacion-resultado": "Resultado de Evaluación",
    notificaciones: "Notificaciones", configuracion: "Configuración",
  };
  const unread = notificaciones.filter(n => !n.leida).length;
  return (
    <header className="h-14 bg-white border-b border-slate-100 flex items-center gap-4 px-6 flex-shrink-0">
      <h1 className="font-bold text-slate-800 text-base flex-shrink-0" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{titles[screen]}</h1>
      <div className="flex-1 flex items-center bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 gap-2 max-w-xs ml-4">
        <Icon name="search" size={14} className="text-slate-400" />
        <input placeholder="Buscar..." className="bg-transparent text-sm text-slate-600 outline-none w-full placeholder:text-slate-400" />
      </div>
      <div className="ml-auto flex items-center gap-3">
        <button onClick={() => onNav("notificaciones")} className="relative w-8 h-8 flex items-center justify-center text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg cursor-pointer">
          <Icon name="bell" size={17} />
          {unread > 0 && <span className="absolute top-0.5 right-0.5 w-2 h-2 bg-red-500 rounded-full" />}
        </button>
        <button onClick={() => onNav("configuracion")} className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-slate-50 cursor-pointer">
          <div className="w-7 h-7 rounded-full bg-blue-700 flex items-center justify-center text-white text-xs font-bold">CR</div>
          <span className="text-sm font-medium text-slate-700 hidden sm:block">Carlos Ruiz</span>
        </button>
      </div>
    </header>
  );
}

// ─── Screen: Login ────────────────────────────────────────────────────────────
function LoginScreen({ onLogin, onRegister }: { onLogin: () => void; onRegister: () => void }) {
  const [email, setEmail] = useState("carlos@rentio.co");
  const [pass, setPass] = useState("••••••••");
  const [loading, setLoading] = useState(false);
  const handleLogin = () => {
    setLoading(true);
    setTimeout(() => { setLoading(false); onLogin(); }, 900);
  };
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-blue-700 flex items-center justify-center mb-3 shadow-lg shadow-blue-200">
            <Icon name="building" size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-blue-700" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>RENTIO</h1>
          <p className="text-sm text-slate-500 mt-1">Gestión inteligente de arrendamientos</p>
        </div>
        <Card className="p-6 shadow-md">
          <h2 className="text-lg font-bold text-slate-800 mb-5" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Iniciar sesión</h2>
          <div className="flex flex-col gap-4">
            <Input label="Correo electrónico" type="email" placeholder="usuario@correo.com" value={email} onChange={setEmail} required />
            <Input label="Contraseña" type="password" placeholder="••••••••" value={pass} onChange={setPass} required />
            <button className="text-xs text-blue-600 hover:text-blue-800 text-right cursor-pointer mt-0.5 self-end">¿Olvidaste tu contraseña?</button>
            <Btn onClick={handleLogin} disabled={loading} className="w-full justify-center mt-1">
              {loading ? "Ingresando..." : "Iniciar sesión"}
            </Btn>
          </div>
        </Card>
        <p className="text-center text-sm text-slate-500 mt-5">
          ¿No tienes cuenta?{" "}
          <button onClick={onRegister} className="text-blue-600 font-semibold hover:text-blue-800 cursor-pointer">
            Crear cuenta
          </button>
        </p>
        <p className="text-center text-xs text-slate-400 mt-3 flex items-center justify-center gap-1">
          <Icon name="lock" size={11} className="text-slate-400" /> Conexión cifrada y segura
        </p>
      </div>
    </div>
  );
}

// ─── Screen: Registro ─────────────────────────────────────────────────────────
function RegistroScreen({ onBack, onSuccess }: { onBack: () => void; onSuccess: (rol: AppMode) => void }) {
  const [step, setStep] = useState<1 | 2>(1);
  const [rol, setRol] = useState<"arrendador" | "arrendatario" | null>(null);
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [doc, setDoc] = useState("");
  const [tel, setTel] = useState("");
  const [pass, setPass] = useState("");
  const [pass2, setPass2] = useState("");
  const [loading, setLoading] = useState(false);

  const rolesData = [
    {
      key: "arrendador" as const,
      titulo: "Soy arrendador",
      desc: "Tengo una o más propiedades y quiero gestionarlas, registrar inquilinos y controlar pagos.",
      icon: "building",
      color: "blue",
    },
    {
      key: "arrendatario" as const,
      titulo: "Busco arrendar",
      desc: "Necesito encontrar una propiedad para vivir y quiero hacer seguimiento de mis pagos y contrato.",
      icon: "users",
      color: "green",
    },
  ];

  const colorMap: Record<string, string> = {
    blue: "border-blue-500 bg-blue-50",
    green: "border-green-500 bg-green-50",
  };
  const iconColorMap: Record<string, string> = {
    blue: "bg-blue-100 text-blue-600",
    green: "bg-green-100 text-green-600",
  };

  const handleFinalizar = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onSuccess(rol as AppMode);
    }, 900);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-7">
          <div className="w-12 h-12 rounded-xl bg-blue-700 flex items-center justify-center mb-3 shadow-lg shadow-blue-200">
            <Icon name="building" size={22} className="text-white" />
          </div>
          <h1 className="text-xl font-bold text-blue-700" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>RENTIO</h1>
        </div>

        <Card className="p-6 shadow-md">
          {/* Step indicator */}
          <div className="flex items-center gap-2 mb-6">
            {[1, 2].map(s => (
              <div key={s} className="flex items-center gap-2 flex-1 last:flex-none">
                <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 transition-colors
                  ${s < step ? "bg-blue-700 text-white" : s === step ? "bg-blue-700 text-white ring-4 ring-blue-100" : "bg-slate-100 text-slate-400"}`}>
                  {s < step ? <Icon name="check" size={12} /> : s}
                </div>
                <span className={`text-xs ${s === step ? "text-blue-700 font-semibold" : "text-slate-400"}`}>
                  {s === 1 ? "Tipo de cuenta" : "Tus datos"}
                </span>
                {s < 2 && <div className={`flex-1 h-px mx-1 ${step > 1 ? "bg-blue-700" : "bg-slate-200"}`} />}
              </div>
            ))}
          </div>

          {step === 1 && (
            <div className="flex flex-col gap-4">
              <div className="mb-1">
                <h2 className="text-lg font-bold text-slate-800" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>¿Cómo usarás RENTIO?</h2>
                <p className="text-sm text-slate-500 mt-0.5">Elige el tipo de cuenta que mejor te describe.</p>
              </div>
              {rolesData.map(r => (
                <button key={r.key} onClick={() => setRol(r.key)}
                  className={`w-full text-left border-2 rounded-xl p-4 flex items-start gap-4 transition-all cursor-pointer
                    ${rol === r.key ? colorMap[r.color] : "border-slate-100 bg-white hover:border-slate-200"}`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${rol === r.key ? iconColorMap[r.color] : "bg-slate-100 text-slate-400"}`}>
                    <Icon name={r.icon} size={18} />
                  </div>
                  <div>
                    <p className={`font-semibold text-sm ${rol === r.key ? "text-slate-800" : "text-slate-700"}`} style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{r.titulo}</p>
                    <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{r.desc}</p>
                  </div>
                  <div className={`ml-auto w-4 h-4 rounded-full border-2 flex-shrink-0 mt-0.5 transition-colors
                    ${rol === r.key ? (r.color === "blue" ? "border-blue-600 bg-blue-600" : "border-green-600 bg-green-600") : "border-slate-300"}`} />
                </button>
              ))}
              <div className="flex justify-between items-center mt-2">
                <button onClick={onBack} className="text-sm text-slate-500 hover:text-slate-700 cursor-pointer">← Volver al login</button>
                <Btn onClick={() => setStep(2)} disabled={!rol}>Continuar <Icon name="chevronRight" size={14} /></Btn>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="flex flex-col gap-4">
              <div className="mb-1">
                <h2 className="text-lg font-bold text-slate-800" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Tus datos personales</h2>
                <p className="text-sm text-slate-500 mt-0.5">Completa la información para crear tu cuenta.</p>
              </div>
              <Input label="Nombre completo" placeholder="Nombre Apellido" value={nombre} onChange={setNombre} required />
              <div className="grid grid-cols-2 gap-3">
                <Input label="Número de documento" placeholder="CC / NIT" value={doc} onChange={setDoc} required />
                <Input label="Teléfono" type="tel" placeholder="300 000 0000" value={tel} onChange={setTel} />
              </div>
              <Input label="Correo electrónico" type="email" placeholder="correo@email.com" value={email} onChange={setEmail} required />
              <Input label="Contraseña" type="password" placeholder="Mínimo 8 caracteres" value={pass} onChange={setPass} required />
              <Input label="Confirmar contraseña" type="password" placeholder="Repite tu contraseña" value={pass2} onChange={setPass2} required />
              <div className="flex justify-between items-center mt-2">
                <button onClick={() => setStep(1)} className="text-sm text-slate-500 hover:text-slate-700 cursor-pointer">← Anterior</button>
                <Btn onClick={handleFinalizar} disabled={loading || !nombre || !email || !doc || !pass}>
                  {loading ? "Creando cuenta..." : "Crear cuenta"}
                </Btn>
              </div>
            </div>
          )}
        </Card>

        <p className="text-center text-xs text-slate-400 mt-4 flex items-center justify-center gap-1">
          <Icon name="lock" size={11} /> Tus datos están protegidos
        </p>
      </div>
    </div>
  );
}

// ─── Screen: Dashboard ────────────────────────────────────────────────────────
function DashboardScreen({ onNav }: { onNav: (s: Screen) => void }) {
  const pagosRetrasados = pagos.filter(p => p.estado === "Retrasado").length;
  const arrendadas = propiedades.filter(p => p.estado === "Arrendada").length;

  const atencion = [
    { dot: "bg-red-500", label: "Ricardo Salazar", sub: "28 días de retraso en el pago", action: () => onNav("perfil-inquilino") },
    { dot: "bg-amber-400", label: "Contrato CON-2023-004", sub: "Vence el 31 de agosto", action: () => onNav("contratos") },
    { dot: "bg-green-500", label: "Sin otros problemas", sub: "El resto de la cartera está al día", action: null },
  ];

  const actividad = [
    { text: "Camila Restrepo realizó el pago de agosto", time: "Ayer" },
    { text: "Riesgo alto detectado en Ricardo Salazar", time: "Hace 2 días" },
    { text: "Contrato generado para Lucía Fernández", time: "Hace 5 días" },
  ];

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-10">

        {/* Bienvenida */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>
            Buenos días, Carlos 👋
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Este es el estado de tu cartera y las tareas que requieren atención.
          </p>
        </div>

        {/* Alerta prioritaria */}
        <div className="flex items-center gap-4 bg-white border border-red-200 rounded-xl px-5 py-4 mb-8 shadow-sm">
          <div className="w-2 h-10 bg-red-500 rounded-full flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-800">1 inquilino requiere atención</p>
            <p className="text-xs text-slate-400 mt-0.5 truncate">Ricardo Salazar — 28 días de retraso</p>
          </div>
          <Btn size="sm" onClick={() => onNav("perfil-inquilino")}>Revisar</Btn>
        </div>

        {/* 3 indicadores */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { label: "Propiedades", value: propiedades.length, note: "registradas" },
            { label: "Arrendadas", value: arrendadas, note: `${propiedades.length - arrendadas} disponibles` },
            { label: "Pagos pendientes", value: pagosRetrasados, note: "requieren acción" },
          ].map(s => (
            <div key={s.label} className="bg-white rounded-xl border border-slate-100 shadow-sm px-5 py-5">
              <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-2">{s.label}</p>
              <p className="text-3xl font-bold text-slate-900" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{s.value}</p>
              <p className="text-xs text-slate-400 mt-1">{s.note}</p>
            </div>
          ))}
        </div>

        {/* Dos columnas: atención + actividad */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">

          {/* Requiere atención */}
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm px-5 py-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Requiere atención</p>
            <div className="flex flex-col gap-4">
              {atencion.map((a, i) => (
                <div key={i} className="flex items-start gap-3">
                  <span className={`w-2 h-2 rounded-full flex-shrink-0 mt-1.5 ${a.dot}`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800 truncate">{a.label}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{a.sub}</p>
                  </div>
                  {a.action && (
                    <button
                      onClick={a.action}
                      className="text-xs text-blue-600 hover:text-blue-800 font-medium flex-shrink-0 cursor-pointer mt-0.5">
                      Ver →
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Actividad reciente */}
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm px-5 py-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Actividad reciente</p>
            <div className="flex flex-col gap-4">
              {actividad.map((a, i) => (
                <div key={i} className="flex items-start gap-3">
                  <span className="w-1 h-1 rounded-full bg-slate-300 flex-shrink-0 mt-2" />
                  <p className="text-sm text-slate-600 flex-1 leading-snug">{a.text}</p>
                  <span className="text-xs text-slate-300 flex-shrink-0 whitespace-nowrap mt-0.5">{a.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Acciones rápidas */}
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Acciones rápidas</p>
          <div className="flex flex-wrap gap-2">
            <Btn onClick={() => onNav("propiedades")}>
              <Icon name="plus" size={14} />Registrar propiedad
            </Btn>
            <Btn variant="secondary" onClick={() => onNav("inquilinos")}>
              <Icon name="users" size={14} />Registrar inquilino
            </Btn>
            <Btn variant="secondary" onClick={() => onNav("contratos")}>
              <Icon name="file" size={14} />Crear contrato
            </Btn>
          </div>
        </div>

      </div>
    </div>
  );
}

// ─── Screen: Propiedades ──────────────────────────────────────────────────────
function PropiedadesScreen() {
  const [modal, setModal] = useState(false);
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-sm text-slate-500">{propiedades.length} propiedades registradas</p>
          </div>
          <Btn onClick={() => setModal(true)}><Icon name="plus" size={14} />Registrar propiedad</Btn>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {propiedades.map(p => (
            <Card key={p.id} className="p-5 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 flex-shrink-0">
                  <Icon name="building" size={18} />
                </div>
                <Badge label={p.estado} />
              </div>
              <h3 className="font-semibold text-slate-800 text-sm mb-1" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{p.dir}</h3>
              <p className="text-xs text-slate-400 mb-3">{p.tipo}</p>
              <div className="flex items-center justify-between text-sm mb-3">
                <span className="text-slate-500">Canon mensual</span>
                <span className="font-bold text-slate-800">{fmt(p.valor)}</span>
              </div>
              {p.inquilino !== "—" && (
                <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 rounded-lg px-3 py-2 mb-3">
                  <Icon name="user" size={12} />
                  {p.inquilino}
                </div>
              )}
              <div className="flex gap-2 mt-2">
                <Btn variant="ghost" size="sm"><Icon name="eye" size={13} />Ver</Btn>
                <Btn variant="ghost" size="sm"><Icon name="edit" size={13} />Editar</Btn>
              </div>
            </Card>
          ))}
        </div>
      </div>
      <Modal open={modal} onClose={() => setModal(false)} title="Registrar propiedad">
        <div className="flex flex-col gap-4">
          <Input label="Dirección" placeholder="Cra 43 #67-12 Apto 301" required />
          <Select label="Tipo de propiedad" options={["Apartamento", "Casa", "Local comercial", "Oficina"]} />
          <Input label="Valor del arriendo" type="number" placeholder="950000" required />
          <Select label="Estado" options={["Disponible", "Arrendada"]} />
          <Input label="Descripción" placeholder="Descripción opcional..." />
          <div className="flex gap-2 justify-end mt-2">
            <Btn variant="secondary" onClick={() => setModal(false)}>Cancelar</Btn>
            <Btn onClick={() => setModal(false)}>Guardar</Btn>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ─── Screen: Inquilinos ───────────────────────────────────────────────────────
function InquilinosScreen({ onNav }: { onNav: (s: Screen) => void }) {
  const [modal, setModal] = useState(false);
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <p className="text-sm text-slate-500">{inquilinos.length} inquilinos registrados</p>
          <Btn onClick={() => setModal(true)}><Icon name="plus" size={14} />Registrar inquilino</Btn>
        </div>
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  {["Nombre", "Documento", "Propiedad", "Contrato", "Pagos", "Score", ""].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {inquilinos.map(inq => {
                  const c = scoreColor(inq.score);
                  return (
                    <tr key={inq.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 text-xs font-bold flex-shrink-0">
                            {inq.nombre.split(" ").map(w => w[0]).join("").slice(0, 2)}
                          </div>
                          <span className="text-sm font-medium text-slate-700">{inq.nombre}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-500">{inq.doc}</td>
                      <td className="px-4 py-3 text-sm text-slate-600 max-w-36 truncate">{inq.propiedad}</td>
                      <td className="px-4 py-3"><Badge label={inq.estado} /></td>
                      <td className="px-4 py-3"><Badge label={inq.pagos} /></td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold" style={{ backgroundColor: c.bg, color: c.text }}>
                            {inq.score}
                          </div>
                          <span className="text-xs font-medium" style={{ color: c.text }}>{inq.riesgo}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-1">
                          <button onClick={() => onNav("perfil-inquilino")} className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg cursor-pointer transition-colors" title="Ver perfil">
                            <Icon name="eye" size={14} />
                          </button>
                          <button className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer transition-colors" title="Editar">
                            <Icon name="edit" size={14} />
                          </button>
                          <button onClick={() => onNav("evaluacion")} className="p-1.5 text-slate-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg cursor-pointer transition-colors" title="Evaluar riesgo">
                            <Icon name="shield" size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
      <Modal open={modal} onClose={() => setModal(false)} title="Registrar inquilino">
        <div className="flex flex-col gap-4">
          <Input label="Nombre completo" placeholder="Nombre Apellido" required />
          <Input label="Número de documento" placeholder="CC / NIT" required />
          <Input label="Correo electrónico" type="email" placeholder="correo@email.com" required />
          <Input label="Teléfono" type="tel" placeholder="300 123 4567" />
          <Select label="Propiedad asignada" options={["Sin asignar", ...propiedades.map(p => p.dir)]} />
          <div className="flex gap-2 justify-end mt-2">
            <Btn variant="secondary" onClick={() => setModal(false)}>Cancelar</Btn>
            <Btn onClick={() => setModal(false)}>Guardar</Btn>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ─── Screen: Perfil Inquilino ─────────────────────────────────────────────────
function PerfilInquilinoScreen({ onNav }: { onNav: (s: Screen) => void }) {
  const inq = inquilinos[3]; // Ricardo Salazar — alto riesgo
  const c = scoreColor(inq.score);
  const historial = [
    { mes: "Ago 2024", valor: 750000, estado: "Retrasado", dias: 28 },
    { mes: "Jul 2024", valor: 750000, estado: "Retrasado", dias: 15 },
    { mes: "Jun 2024", valor: 750000, estado: "Pagado", dias: 0 },
    { mes: "May 2024", valor: 750000, estado: "Retrasado", dias: 8 },
    { mes: "Abr 2024", valor: 750000, estado: "Pagado", dias: 0 },
    { mes: "Mar 2024", valor: 750000, estado: "Pagado", dias: 0 },
  ];
  const factores = [
    { label: "Historial de pagos", valor: "Deficiente", desc: "6 retrasos en los últimos 12 meses", icon: "alertTriangle", color: "text-red-500" },
    { label: "Puntualidad", valor: "Baja", desc: "Promedio de 19 días de retraso", icon: "clock", color: "text-red-500" },
    { label: "Relación ingresos/arriendo", valor: "Ajustada", desc: "Ingreso 1.6x el valor del canon", icon: "trendingUp", color: "text-amber-500" },
    { label: "Incidentes reportados", valor: "2 incidentes", desc: "Daños a la propiedad reportados", icon: "alertTriangle", color: "text-red-500" },
    { label: "Tiempo en la propiedad", valor: "11 meses", desc: "Permanencia moderada", icon: "clock", color: "text-slate-400" },
  ];
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center gap-2 mb-6">
          <button onClick={() => onNav("inquilinos")} className="text-sm text-blue-600 hover:text-blue-800 cursor-pointer">Inquilinos</button>
          <Icon name="chevronRight" size={14} className="text-slate-400" />
          <span className="text-sm text-slate-500">{inq.nombre}</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
          {/* Info */}
          <Card className="p-5 lg:col-span-2">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-14 h-14 rounded-2xl bg-blue-100 flex items-center justify-center text-blue-700 text-xl font-bold flex-shrink-0" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>
                {inq.nombre.split(" ").map(w => w[0]).join("").slice(0, 2)}
              </div>
              <div className="flex-1">
                <h2 className="text-lg font-bold text-slate-800" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{inq.nombre}</h2>
                <p className="text-sm text-slate-500">CC {inq.doc}</p>
                <div className="flex gap-2 mt-2">
                  <Badge label={inq.estado} />
                  <Badge label={inq.pagos} />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              {[
                { label: "Propiedad", value: inq.propiedad },
                { label: "Canon mensual", value: fmt(750000) },
                { label: "Inicio contrato", value: "01/09/2023" },
                { label: "Fin contrato", value: "31/08/2024" },
                { label: "Teléfono", value: "315 678 9012" },
                { label: "Correo", value: "r.salazar@email.com" },
              ].map(f => (
                <div key={f.label} className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-400 mb-0.5">{f.label}</p>
                  <p className="font-medium text-slate-700">{f.value}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* Score */}
          <Card className="p-5 flex flex-col items-center justify-center gap-3" style={{ background: c.bg }}>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Score de Confianza</p>
            <ScoreGauge score={inq.score} />
            <Btn variant="primary" size="sm" onClick={() => onNav("evaluacion")}>
              <Icon name="shield" size={13} />Reevaluar
            </Btn>
          </Card>
        </div>

        {/* Factores */}
        <Card className="p-5 mb-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-4" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Factores de evaluación</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {factores.map(f => (
              <div key={f.label} className="flex items-start gap-2.5 p-3 bg-slate-50 rounded-lg">
                <Icon name={f.icon} size={15} className={`flex-shrink-0 mt-0.5 ${f.color}`} />
                <div>
                  <p className="text-xs font-semibold text-slate-700">{f.label}</p>
                  <p className="text-sm font-bold text-slate-800">{f.valor}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Historial */}
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Historial de pagos</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  {["Mes", "Valor", "Estado", "Días de retraso"].map(h => (
                    <th key={h} className="px-3 py-2 text-left text-xs font-semibold text-slate-500">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {historial.map((h, i) => (
                  <tr key={i} className="border-b border-slate-50">
                    <td className="px-3 py-2.5 text-sm text-slate-700">{h.mes}</td>
                    <td className="px-3 py-2.5 text-sm font-medium text-slate-800">{fmt(h.valor)}</td>
                    <td className="px-3 py-2.5"><Badge label={h.estado} /></td>
                    <td className="px-3 py-2.5 text-sm">
                      {h.dias > 0 ? <span className="text-red-600 font-medium">{h.dias} días</span> : <span className="text-slate-400">—</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ─── Screen: Evaluación ───────────────────────────────────────────────────────
function EvaluacionScreen({ onResult }: { onResult: () => void }) {
  const [step, setStep] = useState(1);
  const [inqSel, setInqSel] = useState(inquilinos[3].nombre);
  const [ingresos, setIngresos] = useState("1200000");
  const [canon, setCanon] = useState("750000");
  const [puntualidad, setPuntualidad] = useState("Baja");
  const totalSteps = 3;

  const steps = ["Inquilino", "Información financiera", "Comportamiento"];

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        {/* Steps */}
        <div className="flex items-center gap-0 mb-8">
          {steps.map((s, i) => (
            <div key={s} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors
                  ${i + 1 < step ? "bg-blue-700 text-white" : i + 1 === step ? "bg-blue-700 text-white ring-4 ring-blue-100" : "bg-slate-100 text-slate-400"}`}>
                  {i + 1 < step ? <Icon name="check" size={14} /> : i + 1}
                </div>
                <span className={`text-xs whitespace-nowrap ${i + 1 === step ? "text-blue-700 font-semibold" : "text-slate-400"}`}>{s}</span>
              </div>
              {i < steps.length - 1 && <div className={`flex-1 h-0.5 mx-2 mb-4 ${i + 1 < step ? "bg-blue-700" : "bg-slate-200"}`} />}
            </div>
          ))}
        </div>

        <Card className="p-6">
          {step === 1 && (
            <div className="flex flex-col gap-5">
              <div>
                <h3 className="font-bold text-slate-800 mb-1" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Seleccionar inquilino</h3>
                <p className="text-sm text-slate-500">Selecciona el inquilino que deseas evaluar o registra uno nuevo.</p>
              </div>
              <Select label="Inquilino" options={inquilinos.map(i => i.nombre)} value={inqSel} onChange={setInqSel} />
              <div className="bg-blue-50 rounded-xl p-4 flex items-start gap-3">
                <Icon name="info" size={16} className="text-blue-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-blue-700">Este análisis te ayudará a tomar una decisión informada. El resultado es una guía, no una decisión automática.</p>
              </div>
            </div>
          )}
          {step === 2 && (
            <div className="flex flex-col gap-5">
              <div>
                <h3 className="font-bold text-slate-800 mb-1" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Información financiera</h3>
                <p className="text-sm text-slate-500">Ingresa los datos económicos del inquilino.</p>
              </div>
              <Input label="Ingresos mensuales estimados" type="number" placeholder="2000000" value={ingresos} onChange={setIngresos} required />
              <Input label="Valor del canon mensual" type="number" placeholder="750000" value={canon} onChange={setCanon} required />
              <Select label="Historial de pagos previos" options={["Sin historial", "Excelente (0 retrasos)", "Bueno (1-2 retrasos)", "Regular (3-5 retrasos)", "Deficiente (6+ retrasos)"]} />
              <Select label="Retrasos en los últimos 12 meses" options={["0", "1-2", "3-5", "6-10", "Más de 10"]} />
            </div>
          )}
          {step === 3 && (
            <div className="flex flex-col gap-5">
              <div>
                <h3 className="font-bold text-slate-800 mb-1" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Comportamiento y referencias</h3>
                <p className="text-sm text-slate-500">Ingresa información sobre el comportamiento del inquilino.</p>
              </div>
              <Select label="Puntualidad general" options={["Alta — siempre puntual", "Media — ocasionalmente tarde", "Baja — frecuentemente tarde"]} value={puntualidad} onChange={setPuntualidad} />
              <Select label="Incidentes reportados" options={["Ninguno", "1 incidente menor", "2 incidentes", "3 o más incidentes"]} />
              <div className="flex flex-col gap-1.5">
                <label className="text-sm font-medium text-slate-700">Observaciones adicionales</label>
                <textarea rows={3} placeholder="Anota cualquier observación relevante sobre el inquilino..."
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none text-slate-800 placeholder:text-slate-400" />
              </div>
            </div>
          )}

          <div className="flex justify-between mt-6">
            {step > 1 ? <Btn variant="secondary" onClick={() => setStep(s => s - 1)}>Anterior</Btn> : <div />}
            {step < totalSteps
              ? <Btn onClick={() => setStep(s => s + 1)}>Siguiente <Icon name="chevronRight" size={14} /></Btn>
              : <Btn onClick={onResult}><Icon name="shield" size={14} />Generar evaluación</Btn>
            }
          </div>
        </Card>
      </div>
    </div>
  );
}

// ─── Screen: Evaluación Resultado ─────────────────────────────────────────────
function EvaluacionResultadoScreen({ onNav }: { onNav: (s: Screen) => void }) {
  const inq = inquilinos[3];
  const c = scoreColor(inq.score);
  const factores = [
    { label: "Historial de pagos", aporte: -28, desc: "Frecuentes retrasos detectados" },
    { label: "Puntualidad", aporte: -22, desc: "Promedio de 19 días de retraso" },
    { label: "Relación ingresos/arriendo", aporte: -15, desc: "Ingresos ajustados al canon" },
    { label: "Incidentes reportados", aporte: -12, desc: "2 incidentes registrados" },
    { label: "Tiempo en la propiedad", aporte: +8, desc: "11 meses de permanencia" },
    { label: "Sin cambios de dirección recientes", aporte: +5, desc: "Estabilidad habitacional" },
  ];
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        {/* Result hero */}
        <Card className="p-8 mb-4 text-center" style={{ background: c.bg }}>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-4">Resultado de evaluación — {inq.nombre}</p>
          <div className="flex justify-center mb-6">
            <ScoreGauge score={inq.score} />
          </div>
          <div className="bg-white rounded-xl p-4 text-left">
            <p className="text-sm font-semibold text-slate-700 mb-2" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Interpretación del resultado</p>
            <p className="text-sm text-slate-600 leading-relaxed">
              Este inquilino presenta un perfil de <strong style={{ color: c.text }}>riesgo alto</strong>. El análisis detecta múltiples retrasos en pagos y una relación ajustada entre sus ingresos y el valor del canon. Se recomienda extremar precauciones antes de renovar o formalizar un contrato.
            </p>
          </div>
          <p className="text-xs text-slate-400 mt-4 flex items-center justify-center gap-1">
            <Icon name="info" size={11} /> Este resultado es una guía de apoyo. La decisión final siempre es tuya como arrendador.
          </p>
        </Card>

        {/* Factores */}
        <Card className="p-5 mb-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-4" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Factores que influyeron en el resultado</h3>
          <div className="flex flex-col gap-3">
            {factores.map(f => (
              <div key={f.label} className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full flex-shrink-0 ${f.aporte > 0 ? "bg-green-500" : "bg-red-400"}`} />
                <div className="flex-1">
                  <p className="text-sm font-medium text-slate-700">{f.label}</p>
                  <p className="text-xs text-slate-400">{f.desc}</p>
                </div>
                <span className={`text-sm font-bold ${f.aporte > 0 ? "text-green-600" : "text-red-500"}`}>
                  {f.aporte > 0 ? "+" : ""}{f.aporte}
                </span>
                <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${f.aporte > 0 ? "bg-green-400" : "bg-red-400"}`}
                    style={{ width: `${Math.abs(f.aporte) * 3}%` }} />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Actions */}
        <Card className="p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-3" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>¿Qué deseas hacer?</h3>
          <div className="flex flex-wrap gap-2">
            <Btn onClick={() => onNav("contratos")}><Icon name="file" size={14} />Crear contrato</Btn>
            <Btn variant="secondary" onClick={() => onNav("notificaciones")}><Icon name="bell" size={14} />Ver alertas</Btn>
            <Btn variant="secondary" onClick={() => onNav("perfil-inquilino")}><Icon name="user" size={14} />Ver perfil</Btn>
            <Btn variant="ghost" onClick={() => onNav("evaluacion")}><Icon name="edit" size={14} />Reevaluar</Btn>
          </div>
        </Card>
      </div>
    </div>
  );
}

// ─── Screen: Contratos ────────────────────────────────────────────────────────
function ContratosScreen() {
  const [modal, setModal] = useState(false);
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <p className="text-sm text-slate-500">{contratos.length} contratos registrados</p>
          <Btn onClick={() => setModal(true)}><Icon name="plus" size={14} />Generar contrato</Btn>
        </div>
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  {["ID", "Inquilino", "Propiedad", "Inicio", "Fin", "Canon", "Estado", ""].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {contratos.map(c => (
                  <tr key={c.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3 text-xs font-mono text-slate-500">{c.id}</td>
                    <td className="px-4 py-3 text-sm font-medium text-slate-700">{c.inquilino}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">{c.propiedad}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">{c.inicio}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">{c.fin}</td>
                    <td className="px-4 py-3 text-sm font-medium text-slate-800">{fmt(c.canon)}</td>
                    <td className="px-4 py-3"><Badge label={c.estado} /></td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        <button className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg cursor-pointer" title="Ver"><Icon name="eye" size={14} /></button>
                        <button className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer" title="Editar"><Icon name="edit" size={14} /></button>
                        <button className="p-1.5 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg cursor-pointer" title="Descargar"><Icon name="download" size={14} /></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
      <Modal open={modal} onClose={() => setModal(false)} title="Generar contrato">
        <div className="flex flex-col gap-4">
          <Select label="Inquilino" options={inquilinos.map(i => i.nombre)} />
          <Select label="Propiedad" options={propiedades.map(p => p.dir)} />
          <Input label="Valor del canon" type="number" placeholder="950000" required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Fecha de inicio" type="date" required />
            <Input label="Fecha de fin" type="date" required />
          </div>
          <Select label="Duración" options={["6 meses", "12 meses", "24 meses", "Personalizado"]} />
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-slate-700">Condiciones especiales</label>
            <textarea rows={2} placeholder="Ej: No se permiten mascotas..."
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>
          <div className="flex gap-2 justify-end mt-2">
            <Btn variant="secondary" onClick={() => setModal(false)}>Cancelar</Btn>
            <Btn onClick={() => setModal(false)}>Generar</Btn>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ─── Screen: Pagos ────────────────────────────────────────────────────────────
function PagosScreen() {
  const [modal, setModal] = useState(false);
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div className="flex gap-2">
            {["Todos", "Pagado", "Pendiente", "Retrasado"].map(f => (
              <button key={f} className={`px-3 py-1.5 text-xs font-medium rounded-lg cursor-pointer transition-colors ${f === "Todos" ? "bg-blue-700 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"}`}>{f}</button>
            ))}
          </div>
          <Btn onClick={() => setModal(true)}><Icon name="plus" size={14} />Registrar pago</Btn>
        </div>
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  {["Inquilino", "Propiedad", "Fecha", "Valor", "Estado", "Retraso", ""].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pagos.map(p => (
                  <tr key={p.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-slate-700">{p.inquilino}</td>
                    <td className="px-4 py-3 text-sm text-slate-500 max-w-36 truncate">{p.propiedad}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">{p.fecha}</td>
                    <td className="px-4 py-3 text-sm font-medium text-slate-800">{fmt(p.valor)}</td>
                    <td className="px-4 py-3"><Badge label={p.estado} /></td>
                    <td className="px-4 py-3 text-sm">
                      {p.retraso > 0 ? <span className="text-red-600 font-medium">{p.retraso} días</span> : <span className="text-slate-400">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      <button className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg cursor-pointer"><Icon name="eye" size={14} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
      <Modal open={modal} onClose={() => setModal(false)} title="Registrar pago">
        <div className="flex flex-col gap-4">
          <Select label="Inquilino" options={inquilinos.map(i => i.nombre)} />
          <Select label="Propiedad" options={propiedades.map(p => p.dir)} />
          <Input label="Valor del pago" type="number" placeholder="950000" required />
          <Input label="Fecha de pago" type="date" required />
          <Select label="Estado del pago" options={["Pagado", "Pendiente", "Retrasado"]} />
          <div className="flex gap-2 justify-end mt-2">
            <Btn variant="secondary" onClick={() => setModal(false)}>Cancelar</Btn>
            <Btn onClick={() => setModal(false)}>Registrar</Btn>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ─── Screen: Notificaciones ───────────────────────────────────────────────────
function NotificacionesScreen({ onNav }: { onNav: (s: Screen) => void }) {
  const iconMap: Record<string, { icon: string; bg: string; text: string }> = {
    "riesgo-alto": { icon: "alertTriangle", bg: "bg-red-50", text: "text-red-500" },
    "pago-retrasado": { icon: "clock", bg: "bg-amber-50", text: "text-amber-500" },
    "contrato-vence": { icon: "file", bg: "bg-purple-50", text: "text-purple-500" },
    "pago-proximo": { icon: "bell", bg: "bg-blue-50", text: "text-blue-500" },
    "evaluacion": { icon: "shield", bg: "bg-blue-50", text: "text-blue-500" },
  };
  const noLeidas = notificaciones.filter(n => !n.leida);
  const leidas = notificaciones.filter(n => n.leida);
  const renderNot = (n: typeof notificaciones[0]) => {
    const meta = iconMap[n.tipo] || { icon: "info", bg: "bg-slate-50", text: "text-slate-400" };
    return (
      <div key={n.id} className={`flex items-start gap-3 p-4 border-b border-slate-50 last:border-0 ${!n.leida ? "bg-blue-50/40" : ""}`}>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${meta.bg}`}>
          <Icon name={meta.icon} size={16} className={meta.text} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <p className="text-sm font-semibold text-slate-800">{n.titulo} {!n.leida && <span className="inline-block w-1.5 h-1.5 bg-blue-600 rounded-full ml-1 mb-0.5 align-middle" />}</p>
            <span className="text-xs text-slate-400 flex-shrink-0">{n.hora}</span>
          </div>
          <p className="text-sm text-slate-500 mt-0.5">{n.desc}</p>
          {n.tipo === "riesgo-alto" && (
            <Btn variant="secondary" size="sm" className="mt-2" onClick={() => onNav("evaluacion-resultado")}>
              Ver evaluación
            </Btn>
          )}
        </div>
      </div>
    );
  };
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        {noLeidas.length > 0 && (
          <Card className="mb-4">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <span className="text-sm font-semibold text-slate-700">No leídas ({noLeidas.length})</span>
              <button className="text-xs text-blue-600 hover:text-blue-800 cursor-pointer">Marcar todas como leídas</button>
            </div>
            {noLeidas.map(renderNot)}
          </Card>
        )}
        <Card>
          <div className="px-4 py-3 border-b border-slate-100">
            <span className="text-sm font-semibold text-slate-700">Anteriores</span>
          </div>
          {leidas.map(renderNot)}
        </Card>
      </div>
    </div>
  );
}

// ─── Screen: Configuración ────────────────────────────────────────────────────
function ConfiguracionScreen() {
  const [passModal, setPassModal] = useState(false);
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto flex flex-col gap-4">
        {/* Cuenta */}
        <Card className="p-5">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>
            <Icon name="user" size={16} className="text-blue-600" /> Información de la cuenta
          </h3>
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-2xl bg-blue-700 flex items-center justify-center text-white text-xl font-bold">CR</div>
            <div>
              <p className="font-semibold text-slate-800">Carlos Ruiz Montoya</p>
              <p className="text-sm text-slate-500">carlos@rentio.co</p>
              <Badge label="Arrendador independiente" className="mt-1" />
            </div>
          </div>
          <div className="grid grid-cols-1 gap-3">
            <Input label="Nombre completo" value="Carlos Ruiz Montoya" />
            <Input label="Correo electrónico" type="email" value="carlos@rentio.co" />
            <Input label="Teléfono" value="301 234 5678" />
          </div>
          <Btn className="mt-4" variant="secondary" size="sm">Guardar cambios</Btn>
        </Card>

        {/* Notificaciones */}
        <Card className="p-5">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>
            <Icon name="bell" size={16} className="text-blue-600" /> Preferencias de notificaciones
          </h3>
          <div className="flex flex-col gap-3">
            {["Alertas de riesgo alto", "Pagos retrasados", "Contratos próximos a vencer", "Pagos próximos", "Evaluaciones disponibles"].map(item => (
              <label key={item} className="flex items-center justify-between cursor-pointer">
                <span className="text-sm text-slate-700">{item}</span>
                <div className="w-10 h-5 bg-blue-700 rounded-full relative flex-shrink-0">
                  <div className="absolute right-0.5 top-0.5 w-4 h-4 bg-white rounded-full shadow" />
                </div>
              </label>
            ))}
          </div>
        </Card>

        {/* Seguridad */}
        <Card className="p-5">
          <h3 className="font-semibold text-slate-800 mb-4 flex items-center gap-2" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>
            <Icon name="lock" size={16} className="text-blue-600" /> Seguridad
          </h3>
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Icon name="checkCircle" size={15} className="text-green-600" />
                <span className="text-sm text-green-700 font-medium">Cuenta protegida</span>
              </div>
              <span className="text-xs text-green-600">Conexión cifrada</span>
            </div>
            <Btn variant="secondary" size="sm" onClick={() => setPassModal(true)}>
              <Icon name="lock" size={13} />Cambiar contraseña
            </Btn>
            <div className="mt-2">
              <p className="text-xs font-semibold text-slate-600 mb-2">Sesiones activas</p>
              {[{ dev: "MacBook Pro — Chrome", loc: "Medellín, Colombia", active: true }, { dev: "iPhone 13 — Safari", loc: "Medellín, Colombia", active: false }].map(s => (
                <div key={s.dev} className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
                  <div>
                    <p className="text-sm text-slate-700">{s.dev}</p>
                    <p className="text-xs text-slate-400">{s.loc}</p>
                  </div>
                  {s.active ? <Badge label="Activo" /> : <Btn variant="ghost" size="sm">Cerrar sesión</Btn>}
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Logout */}
        <Btn variant="danger" className="self-start">
          <Icon name="logout" size={14} />Cerrar sesión
        </Btn>
      </div>
      <Modal open={passModal} onClose={() => setPassModal(false)} title="Cambiar contraseña">
        <div className="flex flex-col gap-4">
          <Input label="Contraseña actual" type="password" placeholder="••••••••" required />
          <Input label="Nueva contraseña" type="password" placeholder="••••••••" required />
          <Input label="Confirmar nueva contraseña" type="password" placeholder="••••••••" required />
          <div className="flex gap-2 justify-end mt-2">
            <Btn variant="secondary" onClick={() => setPassModal(false)}>Cancelar</Btn>
            <Btn onClick={() => setPassModal(false)}>Guardar</Btn>
          </div>
        </div>
      </Modal>
    </div>
  );
}

// ─── Arrendatario: data ───────────────────────────────────────────────────────
const miVivienda = propiedades[0]; // Cra 43 #67-12 Apto 301
const miContrato = contratos[0];   // CON-2024-001 — Camila Restrepo
const misPagos = [
  { mes: "Agosto 2024", valor: 950000, estado: "Pagado", fecha: "01/08/2024", retraso: 0 },
  { mes: "Julio 2024", valor: 950000, estado: "Pagado", fecha: "01/07/2024", retraso: 0 },
  { mes: "Junio 2024", valor: 950000, estado: "Pagado", fecha: "03/06/2024", retraso: 2 },
  { mes: "Mayo 2024", valor: 950000, estado: "Pagado", fecha: "01/05/2024", retraso: 0 },
  { mes: "Abril 2024", valor: 950000, estado: "Pagado", fecha: "01/04/2024", retraso: 0 },
];
const propDisponibles = propiedades.filter(p => p.estado === "Disponible");

// ─── Arrendatario: Sidebar ────────────────────────────────────────────────────
const navArrendatario = [
  { id: "at-inicio", label: "Mi inicio", icon: "dashboard" },
  { id: "at-buscar", label: "Buscar propiedad", icon: "building" },
  { id: "at-contrato", label: "Mi contrato", icon: "file" },
  { id: "at-pagos", label: "Mis pagos", icon: "creditCard" },
  { id: "at-perfil", label: "Mi perfil", icon: "user" },
] as const;

function SidebarArrendatario({ current, onChange, collapsed, onToggle }: {
  current: ScreenArrendatario; onChange: (s: ScreenArrendatario) => void; collapsed: boolean; onToggle: () => void;
}) {
  return (
    <aside className={`flex flex-col h-full bg-white border-r border-slate-100 transition-all duration-300 ${collapsed ? "w-16" : "w-60"} flex-shrink-0`}>
      <div className={`flex items-center gap-2.5 px-4 py-5 border-b border-slate-100 ${collapsed ? "justify-center" : ""}`}>
        <div className="w-8 h-8 rounded-lg bg-blue-700 flex items-center justify-center flex-shrink-0">
          <Icon name="building" size={16} className="text-white" />
        </div>
        {!collapsed && <span className="text-lg font-bold text-blue-700 tracking-tight" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>RENTIO</span>}
      </div>
      <nav className="flex-1 py-4 overflow-y-auto">
        {navArrendatario.map(item => {
          const active = current === item.id;
          return (
            <button key={item.id} onClick={() => onChange(item.id as ScreenArrendatario)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer relative
                ${active ? "bg-blue-50 text-blue-700" : "text-slate-500 hover:bg-slate-50 hover:text-slate-700"}
                ${collapsed ? "justify-center" : ""}`}>
              {active && <span className="absolute left-0 top-1 bottom-1 w-0.5 bg-blue-700 rounded-r" />}
              <Icon name={item.icon} size={17} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          );
        })}
      </nav>
      <div className="p-3 border-t border-slate-100">
        <button onClick={onToggle} className={`w-full flex items-center gap-2 px-2 py-2 text-xs text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg cursor-pointer ${collapsed ? "justify-center" : ""}`}>
          <Icon name="menu" size={16} />
          {!collapsed && "Colapsar"}
        </button>
      </div>
    </aside>
  );
}

function HeaderArrendatario({ screen, onLogout }: { screen: ScreenArrendatario; onLogout: () => void }) {
  const titles: Record<ScreenArrendatario, string> = {
    "at-inicio": "Mi inicio",
    "at-buscar": "Buscar propiedad",
    "at-contrato": "Mi contrato",
    "at-pagos": "Mis pagos",
    "at-perfil": "Mi perfil",
  };
  return (
    <header className="h-14 bg-white border-b border-slate-100 flex items-center gap-4 px-6 flex-shrink-0">
      <h1 className="font-bold text-slate-800 text-base flex-shrink-0" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{titles[screen]}</h1>
      <div className="flex-1 flex items-center bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 gap-2 max-w-xs ml-4">
        <Icon name="search" size={14} className="text-slate-400" />
        <input placeholder="Buscar..." className="bg-transparent text-sm text-slate-600 outline-none w-full placeholder:text-slate-400" />
      </div>
      <div className="ml-auto flex items-center gap-3">
        <button onClick={onLogout} className="flex items-center gap-2 px-2 py-1 rounded-lg hover:bg-slate-50 cursor-pointer" title="Cerrar sesión">
          <div className="w-7 h-7 rounded-full bg-green-600 flex items-center justify-center text-white text-xs font-bold">CR</div>
          <span className="text-sm font-medium text-slate-700 hidden sm:block">Camila R.</span>
        </button>
      </div>
    </header>
  );
}

// ─── Arrendatario: Screens ────────────────────────────────────────────────────
function AtInicioScreen({ onNav }: { onNav: (s: ScreenArrendatario) => void }) {
  const proximoPago = { fecha: "01/09/2024", valor: 950000, diasRestantes: 3 };
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>
            Hola, Camila 👋
          </h2>
          <p className="text-sm text-slate-400 mt-1">Aquí tienes el estado de tu arrendamiento.</p>
        </div>

        {/* Próximo pago — alerta suave */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-4 flex items-center gap-4 mb-8">
          <div className="w-2 h-10 bg-amber-400 rounded-full flex-shrink-0" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-slate-800">Próximo pago en {proximoPago.diasRestantes} días</p>
            <p className="text-xs text-slate-500 mt-0.5">Canon de {fmt(proximoPago.valor)} — vence el {proximoPago.fecha}</p>
          </div>
          <Btn size="sm" onClick={() => onNav("at-pagos")}>Ver pagos</Btn>
        </div>

        {/* Mi vivienda */}
        <Card className="p-5 mb-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Mi vivienda actual</p>
          <div className="flex items-start gap-4 mb-4">
            <div className="w-11 h-11 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600 flex-shrink-0">
              <Icon name="building" size={20} />
            </div>
            <div>
              <p className="font-semibold text-slate-800" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{miVivienda.dir}</p>
              <p className="text-xs text-slate-400 mt-0.5">{miVivienda.tipo}</p>
            </div>
            <Badge label="Arrendada" className="ml-auto" />
          </div>
          <div className="grid grid-cols-3 gap-3 text-sm">
            {[
              { label: "Canon mensual", value: fmt(miVivienda.valor) },
              { label: "Contrato", value: miContrato.id },
              { label: "Vence", value: miContrato.fin },
            ].map(f => (
              <div key={f.label} className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-0.5">{f.label}</p>
                <p className="font-semibold text-slate-800 text-xs">{f.value}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* Resumen pagos */}
        <Card className="p-5 mb-8">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Estado de pagos</p>
          <div className="flex items-center gap-4">
            <div>
              <p className="text-3xl font-bold text-green-600" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>
                {misPagos.filter(p => p.retraso === 0).length}/{misPagos.length}
              </p>
              <p className="text-xs text-slate-400 mt-0.5">pagos al día</p>
            </div>
            <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
              <div className="h-full bg-green-500 rounded-full" style={{ width: `${(misPagos.filter(p => p.retraso === 0).length / misPagos.length) * 100}%` }} />
            </div>
            <button onClick={() => onNav("at-pagos")} className="text-xs text-blue-600 hover:text-blue-800 font-medium cursor-pointer">Ver historial →</button>
          </div>
        </Card>

        {/* Acciones */}
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Acciones rápidas</p>
        <div className="flex flex-wrap gap-2">
          <Btn onClick={() => onNav("at-pagos")}><Icon name="creditCard" size={14} />Registrar pago</Btn>
          <Btn variant="secondary" onClick={() => onNav("at-contrato")}><Icon name="file" size={14} />Ver contrato</Btn>
          <Btn variant="secondary" onClick={() => onNav("at-buscar")}><Icon name="building" size={14} />Buscar propiedad</Btn>
        </div>
      </div>
    </div>
  );
}

function AtBuscarScreen() {
  const [filtro, setFiltro] = useState("Todos");
  const [modal, setModal] = useState<typeof propDisponibles[0] | null>(null);
  const tipos = ["Todos", "Apartamento", "Casa", "Local comercial"];
  const filtradas = filtro === "Todos" ? propDisponibles : propDisponibles.filter(p => p.tipo === filtro);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-4xl mx-auto">
        {/* Filtros */}
        <div className="flex items-center gap-2 mb-6 flex-wrap">
          {tipos.map(t => (
            <button key={t} onClick={() => setFiltro(t)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg cursor-pointer transition-colors
                ${filtro === t ? "bg-blue-700 text-white" : "bg-white border border-slate-200 text-slate-600 hover:bg-slate-50"}`}>
              {t}
            </button>
          ))}
          <span className="ml-auto text-xs text-slate-400">{filtradas.length} propiedades disponibles</span>
        </div>

        {filtradas.length === 0
          ? <EmptyState icon="building" title="No hay propiedades disponibles" desc="Prueba con otro tipo de inmueble o vuelve más tarde." />
          : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filtradas.map(p => (
                <Card key={p.id} className="p-5 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                      <Icon name="building" size={18} />
                    </div>
                    <Badge label="Disponible" />
                  </div>
                  <h3 className="font-semibold text-slate-800 text-sm mb-1" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{p.dir}</h3>
                  <p className="text-xs text-slate-400 mb-4">{p.tipo} · Barrio Laureles, Medellín</p>
                  <div className="flex items-end justify-between">
                    <div>
                      <p className="text-xs text-slate-400">Canon mensual</p>
                      <p className="text-xl font-bold text-slate-800" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{fmt(p.valor)}</p>
                    </div>
                    <Btn size="sm" onClick={() => setModal(p)}>Ver detalles</Btn>
                  </div>
                </Card>
              ))}
            </div>
          )
        }
      </div>

      <Modal open={!!modal} onClose={() => setModal(null)} title="Detalle de la propiedad">
        {modal && (
          <div className="flex flex-col gap-4">
            <div className="flex items-start gap-3 p-4 bg-slate-50 rounded-xl">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600 flex-shrink-0">
                <Icon name="building" size={18} />
              </div>
              <div>
                <p className="font-semibold text-slate-800">{modal.dir}</p>
                <p className="text-sm text-slate-500">{modal.tipo} · Barrio Laureles, Medellín</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Canon mensual", value: fmt(modal.valor) },
                { label: "Tipo", value: modal.tipo },
                { label: "Disponibilidad", value: "Inmediata" },
                { label: "Duración mínima", value: "12 meses" },
              ].map(f => (
                <div key={f.label} className="bg-slate-50 rounded-lg p-3">
                  <p className="text-xs text-slate-400 mb-0.5">{f.label}</p>
                  <p className="text-sm font-semibold text-slate-800">{f.value}</p>
                </div>
              ))}
            </div>
            <div className="bg-blue-50 rounded-xl p-3 flex items-start gap-2">
              <Icon name="info" size={14} className="text-blue-600 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-blue-700">Para solicitar esta propiedad, el arrendador revisará tu perfil y score de confianza.</p>
            </div>
            <div className="flex gap-2 justify-end">
              <Btn variant="secondary" onClick={() => setModal(null)}>Cerrar</Btn>
              <Btn onClick={() => setModal(null)}><Icon name="file" size={14} />Solicitar</Btn>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

function AtContratoScreen() {
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        <Card className="p-5 mb-4">
          <div className="flex items-start justify-between mb-5">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">Contrato activo</p>
              <p className="font-mono text-xs text-slate-500">{miContrato.id}</p>
            </div>
            <Badge label={miContrato.estado} />
          </div>
          <div className="grid grid-cols-2 gap-3 mb-5">
            {[
              { label: "Arrendador", value: "Carlos Ruiz Montoya" },
              { label: "Arrendatario", value: "Camila Restrepo Álvarez" },
              { label: "Propiedad", value: miContrato.propiedad },
              { label: "Canon mensual", value: fmt(miContrato.canon) },
              { label: "Fecha de inicio", value: miContrato.inicio },
              { label: "Fecha de vencimiento", value: miContrato.fin },
              { label: "Duración", value: "12 meses" },
              { label: "Día de pago", value: "1 de cada mes" },
            ].map(f => (
              <div key={f.label} className="bg-slate-50 rounded-lg p-3">
                <p className="text-xs text-slate-400 mb-0.5">{f.label}</p>
                <p className="text-sm font-semibold text-slate-800">{f.value}</p>
              </div>
            ))}
          </div>
          <div className="bg-slate-50 rounded-xl p-4 mb-5">
            <p className="text-xs font-semibold text-slate-600 mb-2">Condiciones especiales</p>
            <p className="text-sm text-slate-500">No se permiten mascotas. El arrendatario es responsable del pago de servicios públicos. Se requiere depósito equivalente a un mes de canon.</p>
          </div>
          <div className="flex gap-2">
            <Btn><Icon name="download" size={14} />Descargar PDF</Btn>
            <Btn variant="secondary"><Icon name="eye" size={14} />Ver completo</Btn>
          </div>
        </Card>
        <Card className="p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Información del arrendador</p>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-blue-700 flex items-center justify-center text-white font-bold text-sm">CR</div>
            <div>
              <p className="font-semibold text-slate-800 text-sm">Carlos Ruiz Montoya</p>
              <p className="text-xs text-slate-400">Arrendador independiente</p>
            </div>
          </div>
          <div className="flex gap-3 text-xs text-slate-500">
            <span>📞 301 234 5678</span>
            <span>✉️ carlos@rentio.co</span>
          </div>
        </Card>
      </div>
    </div>
  );
}

function AtPagosScreen() {
  const [modal, setModal] = useState(false);
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto">
        {/* Próximo pago */}
        <Card className="p-5 mb-5 border-l-4 border-l-amber-400">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Próximo pago</p>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-2xl font-bold text-slate-900" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>{fmt(950000)}</p>
              <p className="text-xs text-slate-500 mt-0.5">Vence el 01/09/2024 · 3 días restantes</p>
            </div>
            <Btn onClick={() => setModal(true)}><Icon name="creditCard" size={14} />Reportar pago</Btn>
          </div>
        </Card>

        {/* Historial */}
        <Card>
          <div className="px-5 py-3 border-b border-slate-100">
            <p className="text-sm font-semibold text-slate-700">Historial de pagos</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  {["Mes", "Fecha", "Valor", "Estado"].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {misPagos.map((p, i) => (
                  <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3 text-sm font-medium text-slate-700">{p.mes}</td>
                    <td className="px-4 py-3 text-sm text-slate-500">{p.fecha}</td>
                    <td className="px-4 py-3 text-sm font-medium text-slate-800">{fmt(p.valor)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Badge label={p.estado} />
                        {p.retraso > 0 && <span className="text-xs text-amber-600">{p.retraso} días tarde</span>}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <Modal open={modal} onClose={() => setModal(false)} title="Reportar pago">
        <div className="flex flex-col gap-4">
          <div className="bg-blue-50 rounded-xl p-3 flex items-start gap-2">
            <Icon name="info" size={14} className="text-blue-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-blue-700">Reporta tu pago para que el arrendador lo pueda verificar y confirmar.</p>
          </div>
          <Input label="Valor pagado" type="number" placeholder="950000" required />
          <Input label="Fecha del pago" type="date" required />
          <Select label="Medio de pago" options={["Transferencia bancaria", "PSE", "Efectivo", "Otro"]} />
          <Input label="Número de comprobante / referencia" placeholder="Opcional" />
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-slate-700">Observaciones</label>
            <textarea rows={2} placeholder="Ej: transferencia desde Bancolombia..."
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>
          <div className="flex gap-2 justify-end mt-1">
            <Btn variant="secondary" onClick={() => setModal(false)}>Cancelar</Btn>
            <Btn onClick={() => setModal(false)}>Reportar pago</Btn>
          </div>
        </div>
      </Modal>
    </div>
  );
}

function AtPerfilScreen() {
  const score = 88;
  const c = scoreColor(score);
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="max-w-2xl mx-auto flex flex-col gap-4">
        {/* Datos personales */}
        <Card className="p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Información personal</p>
          <div className="flex items-center gap-4 mb-5">
            <div className="w-14 h-14 rounded-2xl bg-green-600 flex items-center justify-center text-white text-xl font-bold">CR</div>
            <div>
              <p className="font-bold text-slate-800" style={{ fontFamily: "Plus Jakarta Sans, sans-serif" }}>Camila Restrepo Álvarez</p>
              <p className="text-sm text-slate-500">camila@correo.com</p>
              <Badge label="Arrendataria" className="mt-1" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Nombre completo" value="Camila Restrepo Álvarez" />
            <Input label="Documento" value="1.026.432.198" />
            <Input label="Teléfono" value="315 432 1098" />
            <Input label="Correo electrónico" type="email" value="camila@correo.com" />
          </div>
          <Btn variant="secondary" size="sm" className="mt-4">Guardar cambios</Btn>
        </Card>

        {/* Score */}
        <Card className="p-5" style={{ background: c.bg }}>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">Tu Score de Confianza</p>
          <div className="flex items-center gap-8">
            <ScoreGauge score={score} />
            <div className="flex-1">
              <p className="text-sm font-semibold text-slate-700 mb-3">Factores de tu score</p>
              <div className="flex flex-col gap-2">
                {[
                  { label: "Historial de pagos", valor: "Excelente", color: "text-green-600" },
                  { label: "Puntualidad", valor: "Alta", color: "text-green-600" },
                  { label: "Ingresos / arriendo", valor: "Saludable (3.2x)", color: "text-green-600" },
                  { label: "Incidentes", valor: "Ninguno", color: "text-green-600" },
                ].map(f => (
                  <div key={f.label} className="flex items-center justify-between text-xs">
                    <span className="text-slate-500">{f.label}</span>
                    <span className={`font-semibold ${f.color}`}>{f.valor}</span>
                  </div>
                ))}
              </div>
              <p className="text-xs text-slate-400 mt-3 leading-relaxed">
                Tu score refleja tu historial en RENTIO. Un score alto facilita acceder a nuevas propiedades.
              </p>
            </div>
          </div>
        </Card>

        {/* Seguridad */}
        <Card className="p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Seguridad</p>
          <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg mb-3">
            <div className="flex items-center gap-2">
              <Icon name="checkCircle" size={15} className="text-green-600" />
              <span className="text-sm text-green-700 font-medium">Cuenta protegida</span>
            </div>
            <span className="text-xs text-green-600">Conexión cifrada</span>
          </div>
          <Btn variant="secondary" size="sm"><Icon name="lock" size={13} />Cambiar contraseña</Btn>
        </Card>

        <Btn variant="danger" className="self-start"><Icon name="logout" size={14} />Cerrar sesión</Btn>
      </div>
    </div>
  );
}

// ─── Arrendatario: App Shell ──────────────────────────────────────────────────
function ArrendatarioApp({ onLogout }: { onLogout: () => void }) {
  const [screen, setScreen] = useState<ScreenArrendatario>("at-inicio");
  const [collapsed, setCollapsed] = useState(false);
  return (
    <div className="flex h-full bg-slate-50 overflow-hidden">
      <SidebarArrendatario current={screen} onChange={setScreen} collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <HeaderArrendatario screen={screen} onLogout={onLogout} />
        {screen === "at-inicio" && <AtInicioScreen onNav={setScreen} />}
        {screen === "at-buscar" && <AtBuscarScreen />}
        {screen === "at-contrato" && <AtContratoScreen />}
        {screen === "at-pagos" && <AtPagosScreen />}
        {screen === "at-perfil" && <AtPerfilScreen />}
      </div>
    </div>
  );
}

// ─── App Shell ────────────────────────────────────────────────────────────────
export default function App() {
  const [mode, setMode] = useState<AppMode>("auth");
  const [authScreen, setAuthScreen] = useState<"login" | "registro">("login");
  const [screen, setScreen] = useState<Screen>("dashboard");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [evalStep, setEvalStep] = useState<"form" | "result">("form");

  const nav = (s: Screen) => {
    if (s === "evaluacion") setEvalStep("form");
    setScreen(s);
  };

  const handleLogout = () => { setMode("auth"); setAuthScreen("login"); };

  // Auth flow
  if (mode === "auth") {
    if (authScreen === "registro") {
      return (
        <RegistroScreen
          onBack={() => setAuthScreen("login")}
          onSuccess={(rol) => { setMode(rol); }}
        />
      );
    }
    return (
      <LoginScreen
        onLogin={() => setMode("arrendador")}
        onRegister={() => setAuthScreen("registro")}
      />
    );
  }

  // Arrendatario portal
  if (mode === "arrendatario") {
    return <ArrendatarioApp onLogout={handleLogout} />;
  }

  return (
    <div className="flex h-full bg-slate-50 font-body overflow-hidden">
      <Sidebar current={screen} onChange={nav} collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(c => !c)} />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header screen={screen} onNav={nav} />
        {screen === "dashboard" && <DashboardScreen onNav={nav} />}
        {screen === "propiedades" && <PropiedadesScreen />}
        {screen === "inquilinos" && <InquilinosScreen onNav={nav} />}
        {screen === "perfil-inquilino" && <PerfilInquilinoScreen onNav={nav} />}
        {screen === "contratos" && <ContratosScreen />}
        {screen === "pagos" && <PagosScreen />}
        {screen === "evaluacion" && (
          evalStep === "form"
            ? <EvaluacionScreen onResult={() => { setEvalStep("result"); setScreen("evaluacion-resultado"); }} />
            : <EvaluacionResultadoScreen onNav={nav} />
        )}
        {screen === "evaluacion-resultado" && <EvaluacionResultadoScreen onNav={nav} />}
        {screen === "notificaciones" && <NotificacionesScreen onNav={nav} />}
        {screen === "configuracion" && <ConfiguracionScreen />}
      </div>
    </div>
  );
}
