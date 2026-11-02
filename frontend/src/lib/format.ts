export function money(value?: number | null) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return 'Sin definir';
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(value));
}

export function dateLabel(value?: string | null) {
  if (!value) return 'Sin fecha';
  const dateOnly = /^\d{4}-\d{2}-\d{2}$/.test(value);
  const parts = dateOnly ? value.split('-').map(Number) : null;
  const parsed = parts ? new Date(parts[0], parts[1] - 1, parts[2], 12) : new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' }).format(parsed);
}

export function fullName(user?: { correo?: string; perfil?: { nombre?: string | null; apellido?: string | null } | null } | null) {
  const name = [user?.perfil?.nombre, user?.perfil?.apellido].filter(Boolean).join(' ').trim();
  return name || user?.correo || 'Usuario';
}

export function initials(name: string) {
  return name.split(/[\s@._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0].toUpperCase()).join('') || 'R';
}
