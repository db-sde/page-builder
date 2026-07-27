import { useState } from 'react';
import { diffFields, FIELD_SCHEMA } from '../fieldSchema';

// ── palette helpers ─────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  'required-missing': {
    dot: '#c53030', dotBg: '#fff5f5', dotBorder: '#feb2b2',
    icon: '✗', labelColor: '#c53030', impactColor: '#c53030',
    rowBg: '#fff', rowBorder: '#fed7d7',
  },
  'optional-missing': {
    dot: '#d97706', dotBg: '#fffbeb', dotBorder: '#fde68a',
    icon: '–', labelColor: '#92400e', impactColor: '#b45309',
    rowBg: '#fff', rowBorder: '#fde68a',
  },
  'present': {
    dot: '#1a9d57', dotBg: '#e7f7ee', dotBorder: '#a7f0c4',
    icon: '✓', labelColor: '#1c4532', impactColor: '#5d6b7c',
    rowBg: '#f8fafc', rowBorder: '#e2e8f0',
  },
};

// ── FieldRow ─────────────────────────────────────────────────────────────────
function FieldRow({ field, status, onAdd }) {
  const c = STATUS_CONFIG[status];
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12, padding: '8px 12px',
      background: c.rowBg, borderRadius: 8, border: `1px solid ${c.rowBorder}`,
    }}>
      {/* Status dot */}
      <div style={{
        width: 26, height: 26, borderRadius: '50%', background: c.dotBg,
        border: `1.5px solid ${c.dot}`, display: 'flex', alignItems: 'center',
        justifyContent: 'center', fontSize: 13, fontWeight: 800, color: c.dot, flexShrink: 0,
      }}>{c.icon}</div>

      {/* Field info */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 13.5, fontWeight: 700, color: c.labelColor }}>{field.label}</span>
          <code style={{
            fontSize: 11, fontFamily: 'ui-monospace, monospace', background: '#f0f4f8',
            border: '1px solid #dde3eb', borderRadius: 4, padding: '2px 6px', color: '#5d6b7c',
          }}>{field.key}</code>
          <span style={{
            fontSize: 11.5, fontWeight: 600, color: '#8a95a5', background: '#f4f7fb',
            border: '1px solid #dde3eb', borderRadius: 4, padding: '2px 7px',
          }}>{field.section}</span>
        </div>
        {status !== 'present' && (
          <div style={{ fontSize: 12.5, color: c.impactColor, marginTop: 3, fontWeight: 500 }}>
            {field.impact}
          </div>
        )}
      </div>

      {/* Add button */}
      {status !== 'present' && onAdd && (
        <button
          onClick={onAdd}
          style={{
            background: 'var(--navy)', color: '#fff', border: 'none', borderRadius: 7,
            padding: '6px 14px', fontSize: 12.5, fontWeight: 700, cursor: 'pointer',
            flexShrink: 0, whiteSpace: 'nowrap',
          }}
        >+ Add</button>
      )}
    </div>
  );
}

// ── SectionBlock ──────────────────────────────────────────────────────────────
function SectionBlock({ title, titleColor, bgColor, borderColor, children }) {
  return (
    <div style={{ padding: '14px 24px', background: bgColor, borderBottom: `1px solid ${borderColor}` }}>
      <div style={{
        fontSize: 11.5, fontWeight: 800, color: titleColor,
        textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: 10,
      }}>{title}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
        {children}
      </div>
    </div>
  );
}

// ── FieldHealthPanel ──────────────────────────────────────────────────────────
/**
 * Derive the panel rows from the backend Editing State.
 *
 * The backend already knows which fields the template actually uses, which are
 * required, and which are unused schema fields that must never warn — so the
 * frontend does not recompute any of it. `diffFields` remains the fallback for
 * page types with no blueprint (e.g. blog).
 */
function fromEditingState(editing_state, page_type) {
  const schema = FIELD_SCHEMA[page_type] || [];
  const labels = Object.fromEntries(schema.map(f => [f.key, f]));
  const describe = (name, field) => labels[name] || {
    key: name,
    label: field.label || name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    section: (field.sections && field.sections[0]) || 'Page',
    required: field.required,
    impact: field.image
      ? 'Image is required before the site can be built'
      : 'Section using this field stays hidden',
  };

  const present = [];
  const requiredMissing = [];
  const optionalMissing = [];

  for (const [name, field] of Object.entries(editing_state.fields || {})) {
    // Infrastructure (slug/page_type/...) and fields no template uses are
    // preserved in the data but never shown as work for the operator.
    if (field.infrastructure) continue;
    if (!field.used_by_template && !field.required) continue;

    const row = describe(name, field);
    if (!field.missing) present.push(row);
    else if (field.needs_attention) requiredMissing.push(row);
    else optionalMissing.push(row);
  }
  return { present, requiredMissing, optionalMissing };
}

export default function FieldHealthPanel({ acf_data, page_type, onAddField, editing_state }) {
  const [showPresent, setShowPresent] = useState(false);

  const hasBackendState = editing_state && editing_state.fields;
  let present, requiredMissing, optionalMissing;
  if (hasBackendState) {
    ({ present, requiredMissing, optionalMissing } = fromEditingState(editing_state, page_type));
  } else {
    const diff = diffFields(acf_data, page_type);
    present = diff.present;
    requiredMissing = diff.requiredMissing;
    optionalMissing = diff.missing.filter(f => !f.required);
  }
  const missing = [...requiredMissing, ...optionalMissing];
  const total = present.length + missing.length;

  if (total === 0) return null; // unknown page type — don't render

  const score = total > 0 ? Math.round((present.length / total) * 100) : 0;

  const scoreColor  = score === 100 ? '#1a9d57' : score >= 70 ? '#d97706' : '#c53030';
  const scoreBg     = score === 100 ? '#e7f7ee' : score >= 70 ? '#fffbeb' : '#fff5f5';
  const scoreBorder = score === 100 ? '#a7f0c4' : score >= 70 ? '#fde68a' : '#fed7d7';
  const scoreLabel  = score === 100 ? 'Complete ✓' : score >= 70 ? 'Good' : 'Incomplete';

  const barColor = requiredMissing.length > 0 ? '#c53030' : optionalMissing.length > 0 ? '#d97706' : '#1a9d57';

  return (
    <div style={{
      background: '#fff', border: '1px solid var(--border)',
      borderRadius: 'var(--radius)', marginBottom: 24, overflow: 'hidden',
    }}>
      {/* ── Header ── */}
      <div style={{
        padding: '16px 24px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
        background: '#fafbfc',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ fontWeight: 800, fontSize: 15, color: 'var(--navy)' }}>
            📋 Page Health Check
          </div>
          <div style={{ fontSize: 12.5, color: 'var(--muted)', fontWeight: 600 }}>
            {present.length} of {total} fields filled
            {missing.length > 0 && ` · ${missing.length} missing`}
          </div>
        </div>

        {/* Score badge */}
        <div style={{
          background: scoreBg, border: `1.5px solid ${scoreBorder}`, borderRadius: 9,
          padding: '7px 16px', display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <div style={{ fontWeight: 800, fontSize: 20, color: scoreColor, lineHeight: 1 }}>{score}%</div>
          <div style={{ fontSize: 12, fontWeight: 700, color: scoreColor }}>{scoreLabel}</div>
        </div>
      </div>

      {/* ── Progress bar ── */}
      <div style={{ height: 5, background: '#eef2f8', position: 'relative' }}>
        <div style={{
          position: 'absolute', left: 0, top: 0, bottom: 0,
          width: `${score}%`, background: barColor,
          transition: 'width 0.5s ease',
          borderRadius: '0 3px 3px 0',
        }} />
      </div>

      {/* ── Required Missing ── */}
      {requiredMissing.length > 0 && (
        <SectionBlock
          title="⚠ Required fields missing — these will break the page"
          titleColor="#c53030"
          bgColor="#fff5f5"
          borderColor="#fed7d7"
        >
          {requiredMissing.map(f => (
            <FieldRow key={f.key} field={f} status="required-missing" onAdd={() => onAddField(f)} />
          ))}
        </SectionBlock>
      )}

      {/* ── Optional Missing ── */}
      {optionalMissing.length > 0 && (
        <SectionBlock
          title="Sections that will be hidden (optional fields missing)"
          titleColor="#92400e"
          bgColor="#fffcf5"
          borderColor="#fde68a"
        >
          {optionalMissing.map(f => (
            <FieldRow key={f.key} field={f} status="optional-missing" onAdd={() => onAddField(f)} />
          ))}
        </SectionBlock>
      )}

      {/* ── Present fields (collapsed) ── */}
      <div style={{ padding: '12px 24px' }}>
        <button
          onClick={() => setShowPresent(v => !v)}
          style={{
            background: 'none', border: 'none', fontSize: 13, fontWeight: 700,
            color: 'var(--muted)', cursor: 'pointer', padding: 0,
            display: 'flex', alignItems: 'center', gap: 6,
          }}
        >
          <span style={{ fontSize: 13, transition: 'transform 0.2s', display: 'inline-block', transform: showPresent ? 'rotate(90deg)' : 'none' }}>▸</span>
          {showPresent ? 'Hide' : 'Show'} filled fields ({present.length})
        </button>

        {showPresent && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 7, marginTop: 12 }}>
            {present.map(f => (
              <FieldRow key={f.key} field={f} status="present" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
