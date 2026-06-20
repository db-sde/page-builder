import { useState } from 'react';

// Fields that must be entered as a JSON array
const JSON_FIELDS = new Set([]);

// Fields that accept long HTML content
const HTML_FIELDS = new Set([
  'about_content', 'eligibility_content', 'admission_steps', 'syllabus_content',
  'placement_content', 'why_choose_content', 'emi_content', 'exam_content',
  'certificate_description',
]);

const PLACEHOLDERS = {
  // HTML
  about_content:         '<p>Write the about section content here. Describe the program\'s highlights, history, and value proposition.</p>',
  eligibility_content:   '<p>A bachelor\'s degree with minimum 50% aggregate marks from a UGC-recognised university. Working professionals and fresh graduates are both eligible.</p>',
  admission_steps:       '<p>1. Register online at the Degreebaba portal<br>2. Fill the application form<br>3. Upload required documents<br>4. Pay first installment</p>',
  syllabus_content:      '<p><strong>Year 1:</strong> Core management subjects including Marketing, Finance, HRM, Operations.<br><strong>Year 2:</strong> Specialization electives and capstone project.</p>',
  placement_content:     '<p>Degreebaba Career Services offers virtual placement drives, a dedicated job board, employer webinars and one-on-one career coaching.</p>',
  why_choose_content:    '<p>Describe why students should choose this university — legacy, rankings, industry connections, etc.</p>',
  emi_content:           '<p>No-cost EMI from ₹8,334/month over 24 months. Education loans available via NBFC partners.</p>',
  exam_content:          '<p>Online proctored examinations conducted at designated centres. Results published within 4 weeks of exam date.</p>',
  certificate_description: '<p>On successful completion you receive a degree certificate identical to the on-campus program, valid for all jobs, higher studies, and government roles.</p>',
};

const DEFAULT_VALUES = {
  program_name: 'Degreebaba Online MBA',
  university_name: '',
  spec_name: '',
  hero_description: '',
  duration: '2 Years',
  mode: 'Online',
  total_fee: '2,00,000',
  naac_grade: 'A+',
  ugc_status: 'UGC Entitled',
  ugc_approved: 'UGC Approved',
  seo_title: '',
  meta_description: '',
  emi_amount: '₹8,334/mo',
  num_specializations: '5',
  established_year: '1981',
  starting_fee: '50,000',
  num_programs: '8',
  hero_title: '',
  counselling_hours: 'Mon–Sat · 9 AM – 8 PM',
  avg_response: 'Within 1 working hour',
  admissions_status: 'Open for 2026 batch',
};

export default function AddFieldModal({ field, onSave, onClose }) {
  const isJson = JSON_FIELDS.has(field.key);
  const isHtml = HTML_FIELDS.has(field.key);
  const isTextarea = isJson || isHtml;

  const defaultVal = PLACEHOLDERS[field.key] ?? DEFAULT_VALUES[field.key] ?? '';
  const [value, setValue] = useState(defaultVal);
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
            <code style={{ color: '#9fb4cc', fontSize: 12, fontFamily: 'var(--font-code)', marginTop: 4, display: 'block' }}>
              {field.key}
            </code>
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
            {isJson ? 'Enter as JSON array' : isHtml ? 'Enter as HTML' : 'Enter value'}
          </label>

          {isTextarea ? (
            <textarea
              rows={isJson ? 10 : 6}
              value={value}
              onChange={e => setValue(e.target.value)}
              className="input"
              style={{
                width: '100%',
                fontFamily: isJson ? 'var(--font-code)' : 'inherit',
                resize: 'vertical',
                lineHeight: 1.55,
              }}
            />
          ) : (
            <input
              type="text"
              value={value}
              onChange={e => setValue(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSave()}
              className="input"
              style={{ width: '100%' }}
              autoFocus
            />
          )}

          {isJson && (
            <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 6, lineHeight: 1.5 }}>
              Must be a valid JSON array — use the pre-filled placeholder as a guide. Each object's keys must match what the transformer expects.
            </div>
          )}
          {isHtml && (
            <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 6, lineHeight: 1.5 }}>
              HTML is allowed: &lt;p&gt;, &lt;strong&gt;, &lt;ol&gt;, &lt;li&gt;, &lt;br&gt;. Content is rendered directly into the page.
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
