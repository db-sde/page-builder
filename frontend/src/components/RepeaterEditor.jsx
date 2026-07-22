import { useState } from 'react';

const REPEATER_CONFIG = {
  highlights: {
    itemLabel: 'Highlight',
    fields: [
      { key: 'highlight_title', label: 'Highlight', placeholder: 'Example: Flexible online learning' },
      { key: 'highlight_description', label: 'Description', placeholder: 'Explain this benefit in one or two sentences.', multiline: true },
    ],
  },
  facts: {
    itemLabel: 'Fact',
    fields: [
      { key: 'fact_title', label: 'Label', placeholder: 'Example: Admission Mode' },
      { key: 'fact_description', label: 'Value', placeholder: 'Example: Online application and document verification', multiline: true },
    ],
  },
  programs_table: {
    itemLabel: 'Program',
    fields: [
      { key: 'program_name', label: 'Program name', placeholder: 'Example: Online MBA' },
      { key: 'program_fee', label: 'Fee', placeholder: 'Example: ₹2,00,000 total' },
      { key: 'program_eligibility', label: 'Eligibility', placeholder: 'Example: Graduation with at least 50% marks', multiline: true },
    ],
  },
  accreditations: {
    itemLabel: 'Accreditation',
    fields: [
      { key: 'body_name', label: 'Accrediting body', placeholder: 'Example: NAAC' },
      { key: 'body_descriptor', label: 'Recognition', placeholder: 'Example: A+ Grade' },
      { key: 'body_detail', label: 'Details', placeholder: 'Explain what this recognition means for students.', multiline: true },
    ],
  },
  reviews: {
    itemLabel: 'Review',
    fields: [
      { key: 'review_text', label: 'Review', placeholder: 'Share the student’s experience in their own words.', multiline: true },
      { key: 'reviewer_name', label: 'Student name', placeholder: 'Example: Priya Sharma' },
      { key: 'reviewer_label', label: 'Student details', placeholder: 'Example: Online MBA, 2025' },
    ],
  },
  faculty_members: {
    itemLabel: 'Faculty member',
    fields: [
      { key: 'member_name', label: 'Name', placeholder: 'Example: Dr. Anjali Mehta' },
      { key: 'member_program', label: 'Program or department', placeholder: 'Example: School of Business' },
      { key: 'member_designation', label: 'Role or title', placeholder: 'Example: Professor of Finance' },
      { key: 'member_qualification', label: 'Qualification', placeholder: 'Example: PhD, IIM Ahmedabad' },
    ],
  },
  faqs: {
    itemLabel: 'FAQ',
    fields: [
      { key: 'question', label: 'Question', placeholder: 'Example: What is the eligibility for the Online MBA?' },
      { key: 'answer', label: 'Answer', placeholder: 'Example: Candidates must have a bachelor’s degree with at least 50% marks.', multiline: true },
    ],
  },
  fee_plans: {
    itemLabel: 'Fee plan',
    fields: [
      { key: 'plan_name', label: 'Plan name', placeholder: 'Example: Semester payment plan' },
      { key: 'plan_amount', label: 'Installment amount', placeholder: 'Example: ₹50,000 per semester' },
      { key: 'plan_total', label: 'Total', placeholder: 'Example: ₹2,00,000' },
    ],
  },
  job_profiles: {
    itemLabel: 'Job profile',
    fields: [
      { key: 'job_title', label: 'Role', placeholder: 'Example: Marketing Manager' },
      { key: 'avg_salary', label: 'Typical salary', placeholder: 'Example: ₹8–12 LPA' },
    ],
  },
  other_specs: {
    itemLabel: 'Specialization',
    fields: [
      { key: 'other_spec_name', label: 'Specialization name', placeholder: 'Example: MBA in Finance' },
      { key: 'other_spec_fee', label: 'Fee', placeholder: 'Example: ₹2,00,000 total' },
    ],
  },
};

export default function RepeaterEditor({ fieldKey, label, items, onChange }) {
  const config = REPEATER_CONFIG[fieldKey];
  const [openIndex, setOpenIndex] = useState(items.length ? 0 : null);
  if (!config) return null;

  const updateItem = (index, key, value) => {
    onChange(items.map((item, itemIndex) => (
      itemIndex === index ? { ...item, [key]: value } : item
    )));
  };

  const addItem = () => {
    onChange([...items, Object.fromEntries(config.fields.map(field => [field.key, '']))]);
    setOpenIndex(items.length);
  };

  const removeItem = (index) => {
    onChange(items.filter((_, itemIndex) => itemIndex !== index));
    setOpenIndex(current => current === index ? null : current > index ? current - 1 : current);
  };

  return (
    <div style={{ border: '1px solid var(--color-border)', borderRadius: 9, padding: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: items.length ? 16 : 0 }}>
        <div>
          <div style={{ fontWeight: 800, color: 'var(--color-text-primary)', fontSize: 14.5 }}>{label}</div>
          <div style={{ fontSize: 12.5, color: 'var(--color-text-secondary)', marginTop: 2 }}>
            {items.length ? `${items.length} ${items.length === 1 ? 'item' : 'items'}` : `No ${label.toLowerCase()} added yet`}
          </div>
        </div>
        <button type="button" className="btn btn-secondary" onClick={addItem} style={{ padding: '7px 13px', fontSize: 12.5 }}>
          + Add {config.itemLabel}
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {items.map((item, index) => (
          <div key={index} style={{ background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 8, overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <button type="button" onClick={() => setOpenIndex(openIndex === index ? null : index)} style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, border: 'none', background: 'none', padding: '10px 12px', textAlign: 'left' }}>
                <span style={{ color: 'var(--color-text-secondary)', fontSize: 11 }}>{openIndex === index ? '▼' : '▶'}</span>
                <span style={{ fontSize: 13, fontWeight: 800, color: 'var(--color-text-primary)' }}>
                  {item?.[config.fields[0].key] || `${config.itemLabel} ${index + 1}`}
                </span>
              </button>
              <button type="button" onClick={() => removeItem(index)} style={{ border: 'none', background: 'none', color: 'var(--color-error)', fontSize: 12.5, fontWeight: 700, padding: '10px 12px' }}>
                Remove
              </button>
            </div>
            {openIndex === index && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10, padding: '2px 12px 12px', borderTop: '1px solid var(--color-border)' }}>
                {config.fields.map(field => (
                  <div key={field.key} style={{ gridColumn: field.multiline ? '1 / -1' : undefined, paddingTop: 10 }}>
                    <label style={{ display: 'block', fontSize: 12, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 5 }}>{field.label}</label>
                    {field.multiline ? (
                      <textarea className="input" rows={3} value={item?.[field.key] ?? ''} placeholder={field.placeholder} onChange={event => updateItem(index, field.key, event.target.value)} style={{ width: '100%', resize: 'vertical' }} />
                    ) : (
                      <input className="input" value={item?.[field.key] ?? ''} placeholder={field.placeholder} onChange={event => updateItem(index, field.key, event.target.value)} style={{ width: '100%' }} />
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
