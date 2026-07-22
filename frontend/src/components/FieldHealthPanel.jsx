import { useState } from 'react';
import { diffFields, getFieldCategory } from '../fieldSchema';

function FieldRow({ field, missing = false, optional = false, onAdd }) {
  const missingColor = optional ? '#2563eb' : '#c53030';
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12, padding: '9px 12px',
      background: missing ? '#fff' : '#f8fafc', borderRadius: 8,
      border: `1px solid ${missing ? (optional ? '#bfdbfe' : '#fed7d7') : '#e2e8f0'}`,
    }}>
      <div style={{
        width: 26, height: 26, borderRadius: '50%', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: missing ? (optional ? '#eff6ff' : '#fff5f5') : '#e7f7ee',
        color: missing ? missingColor : '#1a9d57', fontWeight: 800,
      }}>
        {missing ? '!' : '✓'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--color-text-primary)' }}>{field.label}</div>
        {missing && <div style={{ fontSize: 12.5, color: optional ? '#64748b' : '#8a3a3a', marginTop: 2 }}>{optional ? 'Optional enhancement' : field.impact}</div>}
      </div>
      {missing && onAdd && (
        <button type="button" onClick={onAdd} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: 12.5 }}>
          Add content
        </button>
      )}
    </div>
  );
}

export default function FieldHealthPanel({ acf_data, page_type, onAddField, imageReady, imageLabel = 'Hero image' }) {
  const [showOptional, setShowOptional] = useState(false);
  const { present, requiredMissing, optionalMissing, templateDefaults } = diffFields(acf_data, page_type);
  const requiredPresent = present.filter(field => field.required);
  const optionalPresent = present.filter(field => !field.required);
  const addableOptional = optionalMissing.filter(field => getFieldCategory(field) === 'optional' && field.key !== 'admission_steps');
  const requiredTotal = requiredPresent.length + requiredMissing.length;
  // Score = text completion (0–90 pts) + image readiness (0–10 pts).
  // This prevents the image from claiming 50% of the score when there is
  // only one required text field (e.g. the university page).
  const textScore = requiredTotal > 0
    ? Math.round((requiredPresent.length / requiredTotal) * 90)
    : 90;
  const score = textScore + (imageReady ? 10 : 0);
  const ready = requiredMissing.length === 0 && imageReady;
  // Distinct state: required content done but image still missing
  const contentDoneImageMissing = requiredMissing.length === 0 && !imageReady;

  if (!requiredTotal && !optionalMissing.length && !templateDefaults.length) return null;

  return (
    <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 'var(--radius)', marginBottom: 24, overflow: 'hidden' }}>
      <div style={{
        padding: '18px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
        background: ready ? '#f0fdf4' : contentDoneImageMissing ? '#fffbeb' : '#fff8f8', borderBottom: '1px solid var(--border)',
      }}>
        <div>
          <div style={{ fontWeight: 800, fontSize: 15, color: 'var(--navy)' }}>Publishing readiness</div>
          <div style={{ fontSize: 13, color: 'var(--color-text-secondary)', marginTop: 3 }}>
            {ready
              ? 'All required content is ready. Optional enhancements do not affect publishing.'
              : contentDoneImageMissing
                ? 'Content is ready — add the hero image below to finish.'
                : 'Complete the highlighted publishing tasks before publishing.'}
          </div>
        </div>
        <div style={{
          minWidth: 118, textAlign: 'center', borderRadius: 9, padding: '8px 14px',
          background: ready ? '#dcfce7' : contentDoneImageMissing ? '#fef9c3' : '#fee2e2',
          color:      ready ? '#166534' : contentDoneImageMissing ? '#92400e' : '#991b1b',
          fontWeight: 800,
        }}>
          {score}% · {ready ? 'Ready ✓' : contentDoneImageMissing ? 'Image needed' : 'Needs work'}
        </div>
      </div>

      <div style={{ padding: '13px 24px', background: requiredMissing.length ? '#fff8f8' : '#fff', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontSize: 11.5, fontWeight: 800, color: requiredMissing.length ? '#c53030' : '#166534', textTransform: 'uppercase', letterSpacing: '.07em', marginBottom: requiredMissing.length ? 10 : 0 }}>
          Required content · {requiredMissing.length ? `${requiredMissing.length} missing` : '✓ Complete'}
        </div>
        {requiredMissing.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
            {requiredMissing.map(field => (
              <FieldRow key={field.key} field={field} missing onAdd={() => onAddField(field)} />
            ))}
          </div>
        )}
      </div>

      <div style={{ padding: '13px 24px', background: imageReady ? '#fff' : '#fffbeb', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
        <div style={{ fontSize: 11.5, fontWeight: 800, color: imageReady ? '#166534' : '#92400e', textTransform: 'uppercase', letterSpacing: '.07em' }}>
          Images · {imageReady ? '✓ Complete' : `⚠ Missing ${imageLabel}`}
        </div>
        {!imageReady && <span style={{ fontSize: 12.5, color: '#92400e' }}>Add it in Image Slots below</span>}
      </div>

      <div style={{ padding: '14px 24px', borderBottom: '1px solid var(--border)' }}>
        <button type="button" onClick={() => setShowOptional(value => !value)} style={{ background: 'none', border: 'none', padding: 0, color: 'var(--color-text-secondary)', fontSize: 13, fontWeight: 700 }}>
          {showOptional ? '▾' : '▸'} Optional enhancements · {optionalPresent.length} added, {optionalMissing.length} available
        </button>
        {showOptional && (
          <div style={{ marginTop: 12 }}>
            <p style={{ fontSize: 12.5, marginBottom: optionalPresent.length ? 10 : 0 }}>
              These can enrich the page, but leaving them empty will not block publishing.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
              {optionalPresent.map(field => <FieldRow key={field.key} field={field} />)}
              {addableOptional.map(field => <FieldRow key={field.key} field={field} missing optional onAdd={() => onAddField(field)} />)}
            </div>
          </div>
        )}
      </div>

      {templateDefaults.length > 0 && (
        <div style={{ padding: '13px 24px', background: '#f8fafc', fontSize: 12.5, color: 'var(--color-text-secondary)' }}>
          <strong style={{ color: 'var(--color-text-primary)' }}>Template defaults · Using defaults.</strong>{' '}
          Section headings can be overridden in Advanced Customization.
        </div>
      )}
    </div>
  );
}
