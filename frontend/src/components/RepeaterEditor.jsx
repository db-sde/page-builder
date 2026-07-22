const REPEATER_CONFIG = {
  highlights: {
    itemLabel: 'Highlight',
    fields: [
      { key: 'highlight_title', label: 'Highlight' },
      { key: 'highlight_description', label: 'Description', multiline: true },
    ],
  },
  facts: {
    itemLabel: 'Fact',
    fields: [
      { key: 'fact_title', label: 'Label' },
      { key: 'fact_description', label: 'Value', multiline: true },
    ],
  },
  programs_table: {
    itemLabel: 'Program',
    fields: [
      { key: 'program_name', label: 'Program name' },
      { key: 'program_fee', label: 'Fee' },
      { key: 'program_eligibility', label: 'Eligibility', multiline: true },
    ],
  },
  accreditations: {
    itemLabel: 'Accreditation',
    fields: [
      { key: 'body_name', label: 'Accrediting body' },
      { key: 'body_descriptor', label: 'Recognition' },
      { key: 'body_detail', label: 'Details', multiline: true },
    ],
  },
  reviews: {
    itemLabel: 'Review',
    fields: [
      { key: 'review_text', label: 'Review', multiline: true },
      { key: 'reviewer_name', label: 'Student name' },
      { key: 'reviewer_label', label: 'Student details' },
    ],
  },
  faculty_members: {
    itemLabel: 'Faculty member',
    fields: [
      { key: 'member_name', label: 'Name' },
      { key: 'member_program', label: 'Program or department' },
      { key: 'member_designation', label: 'Role or title' },
      { key: 'member_qualification', label: 'Qualification' },
    ],
  },
  faqs: {
    itemLabel: 'FAQ',
    fields: [
      { key: 'question', label: 'Question' },
      { key: 'answer', label: 'Answer', multiline: true },
    ],
  },
  fee_plans: {
    itemLabel: 'Fee plan',
    fields: [
      { key: 'plan_name', label: 'Plan name' },
      { key: 'plan_amount', label: 'Installment amount' },
      { key: 'plan_total', label: 'Total' },
    ],
  },
  job_profiles: {
    itemLabel: 'Job profile',
    fields: [
      { key: 'job_title', label: 'Role' },
      { key: 'avg_salary', label: 'Typical salary' },
    ],
  },
  other_specs: {
    itemLabel: 'Specialization',
    fields: [
      { key: 'other_spec_name', label: 'Specialization name' },
      { key: 'other_spec_fee', label: 'Fee' },
    ],
  },
};

export default function RepeaterEditor({ fieldKey, label, items, onChange }) {
  const config = REPEATER_CONFIG[fieldKey];
  if (!config) return null;

  const updateItem = (index, key, value) => {
    onChange(items.map((item, itemIndex) => (
      itemIndex === index ? { ...item, [key]: value } : item
    )));
  };

  const addItem = () => {
    onChange([...items, Object.fromEntries(config.fields.map(field => [field.key, '']))]);
  };

  const removeItem = (index) => {
    onChange(items.filter((_, itemIndex) => itemIndex !== index));
  };

  return (
    <div style={{ border: '1px solid var(--color-border)', borderRadius: 10, padding: 18 }}>
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
          <div key={index} style={{ background: '#f8fafc', border: '1px solid var(--color-border)', borderRadius: 8, padding: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 800, color: 'var(--color-text-secondary)' }}>
                {config.itemLabel} {index + 1}
              </div>
              <button type="button" onClick={() => removeItem(index)} style={{ border: 'none', background: 'none', color: 'var(--color-error)', fontSize: 12.5, fontWeight: 700 }}>
                Remove
              </button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 12 }}>
              {config.fields.map(field => (
                <div key={field.key} style={{ gridColumn: field.multiline ? '1 / -1' : undefined }}>
                  <label style={{ display: 'block', fontSize: 12.5, fontWeight: 700, color: 'var(--color-text-primary)', marginBottom: 6 }}>
                    {field.label}
                  </label>
                  {field.multiline ? (
                    <textarea className="input" rows={3} value={item?.[field.key] ?? ''} onChange={event => updateItem(index, field.key, event.target.value)} style={{ width: '100%', resize: 'vertical' }} />
                  ) : (
                    <input className="input" value={item?.[field.key] ?? ''} onChange={event => updateItem(index, field.key, event.target.value)} style={{ width: '100%' }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
