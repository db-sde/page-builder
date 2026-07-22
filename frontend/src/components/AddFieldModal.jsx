import { useState } from 'react';
import { getFieldPlaceholder } from '../fieldSchema';

// Fields that accept long HTML content
const HTML_FIELDS = new Set([
  'about_content', 'eligibility_content', 'admission_steps', 'syllabus_content',
  'placement_content', 'why_choose_content', 'emi_content', 'exam_content',
  'certificate_description', 'content_html',
]);

export default function AddFieldModal({ field, onSave, onClose }) {
  const isHtml = HTML_FIELDS.has(field.key);
  const isTextarea = isHtml;

  const [value, setValue] = useState('');
  const [error, setError] = useState('');

  const handleSave = () => {
    setError('');
    if (!value.trim()) {
      setError('Value cannot be empty.');
      return;
    }
    onSave(field.key, value);
  };

  // Close on backdrop click
  const handleBackdrop = (e) => {
    if (e.target === e.currentTarget) onClose();
  };

  const headerBg = field.required ? '#7f1d1d' : '#1e3a5f';
  const badgeBg  = field.required ? '#fca5a5' : '#93c5fd';
  const badgeColor = field.required ? '#7f1d1d' : '#1e3a5f';

  return (
    <div className="modal-overlay" onClick={handleBackdrop}>
      <div className="modal-card" style={{ maxWidth: 620 }}>

        {/* ── Modal header ── */}
        <div className="modal-header" style={{
          background: headerBg, padding: '18px 24px',
          display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12,
          flexShrink: 0, border: 'none'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, flexWrap: 'wrap' }}>
              <div style={{ color: '#fff', fontWeight: 800, fontSize: 16 }}>Add: {field.label}</div>
              <span style={{
                background: badgeBg, color: badgeColor, fontSize: 11, fontWeight: 800,
                borderRadius: 5, padding: '2px 9px', letterSpacing: '.04em', textTransform: 'uppercase',
              }}>
                {field.required ? 'Required' : 'Optional'}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff',
              width: 32, height: 32, borderRadius: '50%', cursor: 'pointer',
              fontSize: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}
          >✕</button>
        </div>

        {/* ── Field context strip ── */}
        <div style={{
          padding: '12px 24px', background: field.required ? '#fff5f5' : '#fffbeb',
          borderBottom: `1px solid ${field.required ? '#fed7d7' : '#fde68a'}`,
          flexShrink: 0,
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: field.required ? '#c53030' : '#92400e' }}>
            Powers: <strong>{field.section}</strong>
          </div>
          <div style={{ fontSize: 12.5, color: '#5d6b7c', marginTop: 2 }}>
            If left empty: {field.impact}
          </div>
        </div>

        {/* ── Input area ── */}
        <div className="modal-body" style={{ padding: 24, overflowY: 'auto', flex: 1 }}>
          <label style={{
            display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 8,
          }}>
            {isHtml ? 'Content' : field.label}
          </label>

          {isTextarea ? (
            <textarea
              rows={6}
              value={value}
              placeholder={getFieldPlaceholder(field)}
              onChange={e => setValue(e.target.value)}
              className="input"
              style={{
                width: '100%',
                fontFamily: 'inherit',
                resize: 'vertical',
                lineHeight: 1.55,
              }}
            />
          ) : (
            <input
              type="text"
              value={value}
              placeholder={getFieldPlaceholder(field)}
              onChange={e => setValue(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSave()}
              className="input"
              style={{ width: '100%' }}
              autoFocus
            />
          )}

          {isHtml && (
            <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 6, lineHeight: 1.5 }}>
              Paragraphs, emphasis, and lists from the imported document are preserved.
            </div>
          )}

          {error && (
            <div style={{
              background: 'var(--color-error-light)', border: '1px solid var(--color-error)', borderRadius: 'var(--radius-md)',
              padding: '9px 13px', color: 'var(--color-error)', fontSize: 13, marginTop: 12, fontWeight: 500,
            }}>
              ⚠ {error}
            </div>
          )}
        </div>

        {/* ── Actions ── */}
        <div className="modal-footer" style={{
          padding: '18px 24px 22px', display: 'flex', justifyContent: 'flex-end', gap: 10,
          flexShrink: 0, borderTop: '1px solid var(--color-border)', paddingTop: 18,
        }}>
          <button
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '10px 20px' }}
          >Cancel</button>
          <button
            onClick={handleSave}
            className="btn btn-primary"
            style={{ padding: '10px 24px' }}
          >Save Field →</button>
        </div>
      </div>
    </div>
  );
}
