function stripMarkup(value) {
  return value
    .replace(/<br\s*\/?\s*>/gi, '\n')
    .replace(/<\/p>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .trim();
}

function admissionHtmlToSteps(value) {
  if (!value) return [];

  // 1. Handle native JS Array
  if (Array.isArray(value)) {
    return value.map(v => String(v).trim()).filter(Boolean);
  }

  const strVal = String(value).trim();

  // 2. Handle stringified JSON array
  if (strVal.startsWith('[') || strVal.startsWith('{')) {
    try {
      const parsed = JSON.parse(strVal);
      if (Array.isArray(parsed)) {
        return parsed.map(v => String(v).trim()).filter(Boolean);
      }
    } catch {
      // Fallback if parsing fails
    }
  }

  // 3. Handle HTML <li> items
  const listItems = [...strVal.matchAll(/<li[^>]*>([\s\S]*?)<\/li>/gi)]
    .map(match => stripMarkup(match[1]))
    .filter(Boolean);
  if (listItems.length) return listItems;

  // 4. Handle plain text separated by newlines
  let cleanText = stripMarkup(strVal);
  cleanText = cleanText.replace(/^[\[\s"]+/, '').replace(/[\]\s",]+$/, '');

  return cleanText
    .split('\n')
    .map(line => line
      .replace(/^\s*(?:step\s*)?\d+[-.):]?\s*/i, '')
      .replace(/^\s*[•*-]\s*/, '')
      .replace(/^"/, '')
      .replace(/",?$/, '')
      .trim()
    )
    .filter(line => line && line !== '[' && line !== ']');
}

export default function StepListEditor({ value, onChange }) {
  const steps = admissionHtmlToSteps(value);
  const update = nextSteps => {
    const cleaned = nextSteps.map(s => String(s).trim()).filter(Boolean);
    onChange(JSON.stringify(cleaned, null, 2));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {steps.map((step, index) => (
        <div key={index} style={{ display: 'grid', gridTemplateColumns: '28px 1fr auto', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 26, height: 26, borderRadius: '50%', background: '#eef2f8', color: 'var(--navy)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 800 }}>{index + 1}</div>
          <input
            className="input"
            value={step}
            placeholder={index === 0 ? 'Example: Complete the online application form.' : 'Describe the next admission step.'}
            onChange={event => update(steps.map((item, itemIndex) => itemIndex === index ? event.target.value : item))}
            style={{ width: '100%' }}
          />
          <button type="button" onClick={() => update(steps.filter((_, itemIndex) => itemIndex !== index))} aria-label={`Remove step ${index + 1}`} style={{ border: 'none', background: 'none', color: 'var(--color-error)', fontWeight: 700, padding: 6 }}>×</button>
        </div>
      ))}
      <button type="button" onClick={() => update([...steps, ''])} className="btn btn-secondary" style={{ alignSelf: 'flex-start', padding: '6px 12px', fontSize: 12.5 }}>
        + Add Step
      </button>
    </div>
  );
}
