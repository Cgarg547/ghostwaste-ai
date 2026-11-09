'use client';

import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react';

export function AppShell({ sidebar, topbar, children }: { sidebar: ReactNode; topbar: ReactNode; children: ReactNode }) {
  return <div className="app-shell"><aside>{sidebar}</aside><div className="app-main"><div className="app-topbar">{topbar}</div><main>{children}</main></div></div>;
}

export function Sidebar({ brand, children, footer }: { brand: ReactNode; children: ReactNode; footer?: ReactNode }) {
  return <nav aria-label="Main navigation" className="design-sidebar"><div>{brand}</div><div className="design-sidebar-links">{children}</div>{footer && <div className="design-sidebar-footer">{footer}</div>}</nav>;
}

export function Topbar({ children }: { children: ReactNode }) { return <header className="design-topbar">{children}</header>; }

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <header className="design-page-header"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p className="sub">{description}</p>}</div>{actions && <div className="headerActions">{actions}</div>}</header>;
}

export function StatCard({ label, value, detail, tone = 'green' }: { label: string; value: ReactNode; detail?: ReactNode; tone?: 'green' | 'lime' | 'amber' }) {
  return <article className={`card stat-card tone-${tone}`}><span>{label}</span><strong>{value}</strong>{detail && <small>{detail}</small>}</article>;
}

export function DataPanel({ title, description, actions, children }: { title?: string; description?: string; actions?: ReactNode; children: ReactNode }) {
  return <section className="panel data-panel">{(title || description || actions) && <SectionHeader title={title} description={description} actions={actions}/>}<div>{children}</div></section>;
}

export function SectionHeader({ title, description, actions }: { title?: string; description?: string; actions?: ReactNode }) {
  return <div className="section-header">{(title || description) && <div>{title && <h2>{title}</h2>}{description && <p className="detail">{description}</p>}</div>}{actions && <div>{actions}</div>}</div>;
}

export function StatusBadge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'success' | 'warning' | 'danger' }) {
  return <span className={`design-status tone-${tone}`} role="status">{children}</span>;
}

export function EmptyState({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return <div className="empty-state"><span className="empty-state-mark" aria-hidden="true">◇</span><strong>{title}</strong>{description && <p>{description}</p>}{action}</div>;
}

export function LoadingSkeleton({ lines = 3, label = 'Loading data' }: { lines?: number; label?: string }) {
  return <div className="loading-skeleton" role="status" aria-label={label}>{Array.from({ length: Math.max(1, lines) }, (_, index) => <i key={index}/>)}</div>;
}

export function ConfirmationDialog({ open, title, description, confirmLabel = 'Confirm', cancelLabel = 'Cancel', busy = false, onConfirm, onCancel }: { open: boolean; title: string; description: string; confirmLabel?: string; cancelLabel?: string; busy?: boolean; onConfirm: () => void; onCancel: () => void }) {
  if (!open) return null;
  return <div className="dialog-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onCancel(); }}><section className="confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="confirm-title" aria-describedby="confirm-description"><h2 id="confirm-title">{title}</h2><p id="confirm-description">{description}</p><div><button className="secondary" type="button" onClick={onCancel} disabled={busy}>{cancelLabel}</button><button type="button" onClick={onConfirm} disabled={busy}>{busy ? 'Working…' : confirmLabel}</button></div></section></div>;
}

type FieldProps = { label: string; error?: string; hint?: string; id: string };
export function FormField({ label, error, hint, id, ...props }: FieldProps & InputHTMLAttributes<HTMLInputElement>) {
  return <label className="design-form-field" htmlFor={id}><span>{label}</span><input id={id} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined} {...props}/>{hint && !error && <small id={`${id}-hint`}>{hint}</small>}{error && <small id={`${id}-error`} role="alert">{error}</small>}</label>;
}
export function SelectField({ label, error, hint, id, ...props }: FieldProps & SelectHTMLAttributes<HTMLSelectElement>) {
  return <label className="design-form-field" htmlFor={id}><span>{label}</span><select id={id} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined} {...props}/>{hint && !error && <small id={`${id}-hint`}>{hint}</small>}{error && <small id={`${id}-error`} role="alert">{error}</small>}</label>;
}
export function TextAreaField({ label, error, hint, id, ...props }: FieldProps & TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <label className="design-form-field" htmlFor={id}><span>{label}</span><textarea id={id} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined} {...props}/>{hint && !error && <small id={`${id}-hint`}>{hint}</small>}{error && <small id={`${id}-error`} role="alert">{error}</small>}</label>;
}

export function ResponsiveDataTable({ headers, rows, empty = 'No saved records yet.' }: { headers: string[]; rows: ReactNode[][]; empty?: string }) {
  return <div className="table"><table><thead><tr>{headers.map(header => <th key={header} scope="col">{header}</th>)}</tr></thead><tbody>{rows.length ? rows.map((row, index) => <tr key={index}>{row.map((cell, cellIndex) => <td key={cellIndex}>{cell}</td>)}</tr>) : <tr><td colSpan={headers.length}>{empty}</td></tr>}</tbody></table></div>;
}
