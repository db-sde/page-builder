import { useMemo, useState } from 'react';
import {
  FIELD_SECTION_PREFERENCE,
  getFieldPresentation,
  REPEATER_PRESENTATION,
  SECTION_HELP,
  SECTION_NAVIGATION_GROUPS,
} from '../contentEditorSchema';

function isEmpty(value) {
  if (value === null || value === undefined) return true;
  if (typeof value === 'string') return !value.trim();
  if (Array.isArray(value)) return value.length === 0;
  return false;
}

function toReviewEditorItem(item) {
  const source = item && typeof item === 'object' ? item : {};
  let reviewerName = source.reviewer_name || '';
  let reviewerRole = source.reviewer_role || '';
  if (!reviewerName && source.reviewer_label) {
    const parts = String(source.reviewer_label).split(',').map(part => part.trim()).filter(Boolean);
    reviewerName = parts.shift() || '';
    reviewerRole = parts.join(', ');
  }
  return { ...source, reviewer_name: reviewerName, reviewer_role: reviewerRole };
}

function fromReviewEditorItem(item) {
  const reviewerName = String(item.reviewer_name || '').trim();
  const reviewerRole = String(item.reviewer_role || '').trim();
  const reviewerLabel = [reviewerName, reviewerRole].filter(Boolean).join(', ');
  const output = { ...item, reviewer_label: reviewerLabel };
  delete output.reviewer_name;
  delete output.reviewer_role;
  if (!reviewerLabel) delete output.reviewer_label;
  return output;
}

function itemSummary(name, item) {
  if (name === 'reviews') {
    const nameOrRole = item.reviewer_name || item.reviewer_role || item.review_text || 'New review';
    const rating = String(item.rating || '').trim();
    return rating ? `${nameOrRole} · ${rating}` : nameOrRole;
  }
  const config = REPEATER_PRESENTATION[name];
  const firstFilled = config.fields.map(field => item?.[field.key]).find(value => !isEmpty(value));
  return firstFilled || `New ${config.itemLabel.toLowerCase()}`;
}

function RepeaterEditor({ name, value, onChange, disabled, emptyMessage }) {
  const config = REPEATER_PRESENTATION[name];
  const [openItems, setOpenItems] = useState(() => new Set());
  const editorItems = useMemo(() => {
    const items = Array.isArray(value) ? value : [];
    if (config.scalar) return items.map(item => ({ value: typeof item === 'string' ? item : item?.value || '' }));
    return name === 'reviews' ? items.map(toReviewEditorItem) : items;
  }, [config.scalar, name, value]);

  const commit = (items) => {
    if (config.scalar) {
      onChange(items.map(item => item.value));
      return;
    }
    onChange(name === 'reviews' ? items.map(fromReviewEditorItem) : items);
  };

  const addItem = () => {
    const nextIndex = editorItems.length;
    commit([...editorItems, {}]);
    setOpenItems(current => new Set([...current, nextIndex]));
  };

  return (
    <div className="author-repeater">
      {editorItems.length === 0 && <div className="author-empty">{emptyMessage || `No ${config.itemLabel.toLowerCase()} items yet.`}</div>}
      {editorItems.map((item, index) => {
        const isOpen = openItems.has(index);
        return (
          <div className="author-repeater-item" key={`${name}-${index}`}>
            <div className="author-repeater-heading">
              <div className="author-repeater-summary">
                <strong>{config.itemLabel} {index + 1}</strong>
                <span>{itemSummary(name, item)}</span>
              </div>
              {!disabled && (
                <div className="author-repeater-actions">
                  <button type="button" className="author-link" onClick={() => setOpenItems(current => {
                    const next = new Set(current);
                    if (next.has(index)) next.delete(index); else next.add(index);
                    return next;
                  })}>{isOpen ? 'Close' : 'Edit'}</button>
                  <button type="button" className="author-link author-link--danger" onClick={() => {
                    commit(editorItems.filter((_, itemIndex) => itemIndex !== index));
                    setOpenItems(current => new Set([...current].filter(itemIndex => itemIndex !== index).map(itemIndex => itemIndex > index ? itemIndex - 1 : itemIndex)));
                  }}>Delete</button>
                </div>
              )}
            </div>
            {isOpen && (
              <div className="author-fields-grid">
                {config.fields.map(field => (
                  <label className={field.type === 'textarea' ? 'author-field author-field--wide' : 'author-field'} key={field.key}>
                    <span>{field.label}</span>
                    {field.type === 'textarea' ? (
                      <textarea
                        className="input"
                        rows={3}
                        value={item?.[field.key] || ''}
                        placeholder={field.placeholder}
                        disabled={disabled}
                        onChange={event => commit(editorItems.map((existing, itemIndex) => (
                          itemIndex === index ? { ...existing, [field.key]: event.target.value } : existing
                        )))}
                      />
                    ) : (
                      <input
                        className="input"
                        value={item?.[field.key] || ''}
                        placeholder={field.placeholder}
                        disabled={disabled}
                        onChange={event => commit(editorItems.map((existing, itemIndex) => (
                          itemIndex === index ? { ...existing, [field.key]: event.target.value } : existing
                        )))}
                      />
                    )}
                  </label>
                ))}
              </div>
            )}
          </div>
        );
      })}
      {!disabled && <button type="button" className="btn btn-secondary author-add-button" onClick={addItem}>+ {config.addLabel}</button>}
    </div>
  );
}

function escapeHtml(value) {
  return String(value || '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function admissionStepMatch(text) {
  return text.match(/\bstep\s*\d+\s*[.):\-]?\s*|^\d+\s*[.):\-]\s*/i);
}

function isAdmissionStepElement(node) {
  if (node.tagName === 'OL') return Boolean(node.querySelector('li'));
  return node.matches('p, li') && Boolean(admissionStepMatch(node.textContent.trim()));
}

function parseAdmissionSteps(value) {
  if (Array.isArray(value)) {
    return value.map(item => typeof item === 'string'
      ? { title: item, description: '' }
      : { title: item?.title || item?.t || '', description: item?.description || item?.d || '' });
  }
  if (!value || typeof DOMParser === 'undefined') return [];
  const documentNode = new DOMParser().parseFromString(`<div>${value}</div>`, 'text/html');
  const numberedParagraphs = [...documentNode.body.querySelectorAll('p, li')]
    .filter(node => admissionStepMatch(node.textContent.trim()));
  const orderedListItems = [...documentNode.body.querySelectorAll('ol > li')];
  return [...new Set([...numberedParagraphs, ...orderedListItems])]
    .map(node => node.textContent.trim())
    .filter(Boolean)
    .map(text => {
      const marker = admissionStepMatch(text);
      const content = marker ? text.slice(marker.index + marker[0].length) : text;
      const parts = content.match(/^([^:–—]{1,80})\s*[:–—]\s*(.+)$/);
      return parts
        ? { title: parts[1].trim(), description: parts[2].trim() }
        : { title: content, description: '' };
    });
}

function surroundingHtml(value, isStructuredElement) {
  if (!value || Array.isArray(value) || typeof DOMParser === 'undefined') return { before: '', after: '' };
  const documentNode = new DOMParser().parseFromString(`<div>${value}</div>`, 'text/html');
  const children = [...documentNode.body.firstElementChild.children];
  const structuredIndexes = children
    .map((node, index) => isStructuredElement(node) ? index : -1)
    .filter(index => index >= 0);
  if (!structuredIndexes.length) return { before: value, after: '' };
  const first = Math.min(...structuredIndexes);
  const last = Math.max(...structuredIndexes);
  return {
    before: children.slice(0, first).map(node => node.outerHTML).join(''),
    after: children.slice(last + 1).map(node => node.outerHTML).join(''),
  };
}

function serializeAdmissionSteps(steps, originalValue) {
  const { before, after } = surroundingHtml(originalValue, isAdmissionStepElement);
  const structured = steps
    .filter(step => !isEmpty(step.title) || !isEmpty(step.description))
    .map((step, index) => {
      const content = [String(step.title || '').trim(), String(step.description || '').trim()].filter(Boolean).join(': ');
      return `<p>${index + 1}. ${escapeHtml(content)}</p>`;
    })
    .join('');
  return `${before}${structured}${after}`;
}

function AdmissionStepsEditor({ value, onChange, disabled }) {
  const steps = useMemo(() => parseAdmissionSteps(value), [value]);
  const commit = next => onChange(serializeAdmissionSteps(next, value));
  return (
    <div className="author-repeater">
      {steps.length === 0 && <div className="author-empty">No admission steps found in the uploaded document.</div>}
      {steps.map((step, index) => (
        <div className="author-repeater-item" key={`admission-step-${index}`}>
          <div className="author-repeater-heading">
            <strong>Step {index + 1}</strong>
            {!disabled && <button type="button" className="author-link author-link--danger" onClick={() => commit(steps.filter((_, stepIndex) => stepIndex !== index))}>Delete</button>}
          </div>
          <div className="author-fields-grid">
            <label className="author-field">
              <span>Title</span>
              <input className="input" value={step.title} placeholder="Register on the admission portal" disabled={disabled} onChange={event => commit(steps.map((item, stepIndex) => stepIndex === index ? { ...item, title: event.target.value } : item))} />
            </label>
            <label className="author-field author-field--wide">
              <span>Description</span>
              <textarea className="input" rows={2} value={step.description} placeholder="Explain what the applicant needs to do" disabled={disabled} onChange={event => commit(steps.map((item, stepIndex) => stepIndex === index ? { ...item, description: event.target.value } : item))} />
            </label>
          </div>
        </div>
      ))}
      {!disabled && <button type="button" className="btn btn-secondary author-add-button" onClick={() => commit([...steps, { title: '', description: '' }])}>+ Add Step</button>}
    </div>
  );
}

function isSyllabusHeading(node) {
  return node.matches('h3, h4, h5, h6') && (/\byear\b/i.test(node.textContent) || /\b(?:sem(?:ester)?|term)\b/i.test(node.textContent));
}

function isSyllabusStructureElement(node) {
  return node.tagName === 'TABLE' || isSyllabusHeading(node) || node.tagName === 'UL' || node.tagName === 'OL';
}

function cellSubjects(cell) {
  const listItems = [...cell.querySelectorAll('li')].map(item => item.textContent.trim()).filter(Boolean);
  if (listItems.length) return listItems;
  const clone = cell.cloneNode(true);
  clone.querySelectorAll('br').forEach(br => br.replaceWith('\n'));
  return clone.textContent
    .split(/\n+/)
    .map(text => text.replace(/^[•·\-*]\s*/, '').trim())
    .filter(Boolean);
}

function parseSyllabusTable(table) {
  const years = [];
  let currentYear = null;
  let currentSemesters = [];
  const ensureYear = label => {
    if (!currentYear || (label && currentYear.label !== label)) {
      currentYear = { label: label || `Year ${years.length + 1}`, semesters: [] };
      years.push(currentYear);
    }
    return currentYear;
  };

  [...table.querySelectorAll('tr')].forEach(row => {
    const cells = [...row.children].filter(node => ['TH', 'TD'].includes(node.tagName));
    if (!cells.length) return;
    const labels = cells.map(cell => cell.textContent.trim()).filter(Boolean);
    const yearLabel = labels.length === 1 && /^year\b/i.test(labels[0]) ? labels[0] : '';
    if (yearLabel) {
      ensureYear(yearLabel);
      currentSemesters = [];
      return;
    }

    const semesterLabels = labels.length === cells.length && labels.every(label => /^(?:sem(?:ester)?|term)\b/i.test(label));
    if (semesterLabels) {
      const year = ensureYear();
      currentSemesters = labels.map(label => ({ title: label, subjects: [] }));
      year.semesters.push(...currentSemesters);
      return;
    }

    if (currentSemesters.length) {
      cells.forEach((cell, index) => {
        if (currentSemesters[index]) currentSemesters[index].subjects.push(...cellSubjects(cell));
      });
    }
  });
  return years;
}

function parseSyllabus(value) {
  if (Array.isArray(value)) return value;
  if (!value || typeof DOMParser === 'undefined') return [];
  const documentNode = new DOMParser().parseFromString(`<div>${value}</div>`, 'text/html');
  const table = documentNode.body.querySelector('table');
  if (table) return parseSyllabusTable(table);
  const years = [];
  let currentYear = null;
  let currentSemester = null;
  [...documentNode.body.querySelectorAll('h3, h4, h5, h6, li')].forEach(node => {
    const text = node.textContent.trim();
    if (!text) return;
    if (node.matches('h3, h4, h5, h6') && /\byear\b/i.test(text) && !/\b(?:sem(?:ester)?|term)\b/i.test(text)) {
      currentYear = { label: text, semesters: [] };
      years.push(currentYear);
      currentSemester = null;
    } else if (node.matches('h3, h4, h5, h6') && /\b(?:sem(?:ester)?|term)\b/i.test(text)) {
      if (!currentYear) {
        currentYear = { label: 'Year 1', semesters: [] };
        years.push(currentYear);
      }
      currentSemester = { title: text, subjects: [] };
      currentYear.semesters.push(currentSemester);
    } else if (node.tagName === 'LI' && currentSemester) {
      currentSemester.subjects.push(text);
    }
  });
  return years;
}

function serializeSyllabus(years, originalValue) {
  const { before, after } = surroundingHtml(originalValue, isSyllabusStructureElement);
  const structured = years.map((year, yearIndex) => {
    const yearLabel = String(year.label || `Year ${yearIndex + 1}`).trim();
    const semesters = (year.semesters || []).map((semester, semesterIndex) => {
      const semesterTitle = String(semester.title || `Semester ${semesterIndex + 1}`).trim();
      const subjects = (semester.subjects || []).filter(subject => !isEmpty(subject));
      return `<h4>${escapeHtml(semesterTitle)}</h4><ul>${subjects.map(subject => `<li>${escapeHtml(subject)}</li>`).join('')}</ul>`;
    }).join('');
    return `<h3>${escapeHtml(yearLabel)}</h3>${semesters}`;
  }).join('');
  return `${before}${structured}${after}`;
}

function SyllabusEditor({ value, onChange, disabled }) {
  const years = useMemo(() => parseSyllabus(value), [value]);
  const commit = next => onChange(serializeSyllabus(next, value));
  return (
    <div className="author-repeater">
      {years.length === 0 && <div className="author-empty">No structured syllabus found in the uploaded document.</div>}
      {years.map((year, yearIndex) => (
        <div className="author-repeater-item" key={`syllabus-year-${yearIndex}`}>
          <div className="author-repeater-heading">
            <strong>Year {yearIndex + 1}</strong>
            {!disabled && <button type="button" className="author-link author-link--danger" onClick={() => commit(years.filter((_, index) => index !== yearIndex))}>Delete Year</button>}
          </div>
          <label className="author-field">
            <span>Year</span>
            <input className="input" value={year.label || ''} placeholder={`Year ${yearIndex + 1}`} disabled={disabled} onChange={event => commit(years.map((item, index) => index === yearIndex ? { ...item, label: event.target.value } : item))} />
          </label>
          {(year.semesters || []).map((semester, semesterIndex) => (
            <div className="author-structured-group" key={`semester-${yearIndex}-${semesterIndex}`}>
              <div className="author-repeater-heading">
                <strong>Semester {semesterIndex + 1}</strong>
                {!disabled && <button type="button" className="author-link author-link--danger" onClick={() => commit(years.map((item, index) => index === yearIndex ? { ...item, semesters: item.semesters.filter((_, semIndex) => semIndex !== semesterIndex) } : item))}>Delete Semester</button>}
              </div>
              <label className="author-field">
                <span>Semester</span>
                <input className="input" value={semester.title || ''} placeholder={`Semester ${semesterIndex + 1}`} disabled={disabled} onChange={event => commit(years.map((item, index) => index === yearIndex ? { ...item, semesters: item.semesters.map((sem, semIndex) => semIndex === semesterIndex ? { ...sem, title: event.target.value } : sem) } : item))} />
              </label>
              {(semester.subjects || []).map((subject, subjectIndex) => (
                <div className="author-inline-field" key={`subject-${yearIndex}-${semesterIndex}-${subjectIndex}`}>
                  <label className="author-field">
                    <span>Subject {subjectIndex + 1}</span>
                    <input className="input" value={subject} placeholder="Enter the subject name" disabled={disabled} onChange={event => commit(years.map((item, index) => index === yearIndex ? { ...item, semesters: item.semesters.map((sem, semIndex) => semIndex === semesterIndex ? { ...sem, subjects: sem.subjects.map((entry, entryIndex) => entryIndex === subjectIndex ? event.target.value : entry) } : sem) } : item))} />
                  </label>
                  {!disabled && <button type="button" className="author-link author-link--danger" onClick={() => commit(years.map((item, index) => index === yearIndex ? { ...item, semesters: item.semesters.map((sem, semIndex) => semIndex === semesterIndex ? { ...sem, subjects: sem.subjects.filter((_, entryIndex) => entryIndex !== subjectIndex) } : sem) } : item))}>Remove</button>}
                </div>
              ))}
              {!disabled && <button type="button" className="author-link" onClick={() => commit(years.map((item, index) => index === yearIndex ? { ...item, semesters: item.semesters.map((sem, semIndex) => semIndex === semesterIndex ? { ...sem, subjects: [...(sem.subjects || []), ''] } : sem) } : item))}>+ Add Subject</button>}
            </div>
          ))}
          {!disabled && <button type="button" className="author-link" onClick={() => commit(years.map((item, index) => index === yearIndex ? { ...item, semesters: [...(item.semesters || []), { title: `Semester ${(item.semesters || []).length + 1}`, subjects: [] }] } : item))}>+ Add Semester</button>}
        </div>
      ))}
      {!disabled && <button type="button" className="btn btn-secondary author-add-button" onClick={() => commit([...years, { label: `Year ${years.length + 1}`, semesters: [] }])}>+ Add Year</button>}
    </div>
  );
}

function ownershipLabel(field, value, overridden = false) {
  if (field.auto_filled || field.derived || field.source === 'DERIVED') return 'Generated Automatically';
  if (field.source === 'WORKSPACE') return 'Workspace Managed';
  if (field.source === 'SYSTEM') return 'System Managed';
  if (field.manual || field.source === 'MANUAL') return 'Manual Input';
  if (overridden || (field.missing && !isEmpty(value))) return 'Manual Override';
  return isEmpty(value) ? 'Document Content Missing' : 'Imported from Document';
}

function SectionFields({ descriptor, values, onChange, onManualOverride }) {
  const [override, setOverride] = useState(false);
  const hasExtractedFields = descriptor.fields.some(field => field.source === 'AUTO' && !field.missing);
  const hasAutoFields = descriptor.fields.some(field => field.source === 'AUTO');
  const hasNoImportedContent = hasAutoFields && !descriptor.fields.some(field => field.source === 'AUTO' && !isEmpty(values[field.name]));
  const editingDisabled = hasExtractedFields && !override;

  const switchToManualEditing = () => {
    setOverride(true);
    onManualOverride?.();
  };

  return (
    <div className="author-section-body">
      {hasExtractedFields && !override && (
        <div className="author-extracted-note">
          <span>This content was imported from the uploaded document.</span>
          <button type="button" className="author-link" onClick={switchToManualEditing}>Switch to manual editing</button>
        </div>
      )}
      {hasNoImportedContent && (
        <div className="author-empty-import">
          <span>No content was found in the uploaded document.</span>
          <span>You can add this content manually.</span>
        </div>
      )}
      {descriptor.fields.map(field => {
        const presentation = getFieldPresentation(field.name);
        const repeater = REPEATER_PRESENTATION[field.name];
        const disabled = field.derived || (field.source === 'AUTO' && !field.missing && editingDisabled);
        return (
          <div className="author-field-block" key={field.name}>
            <div className="author-field-heading">
              <div>
                <span className="author-field-label">{repeater?.label || presentation.label}</span>
                {field.required && <span className="author-required">Required</span>}
              </div>
              <span className={`author-badge author-badge--${String(field.source || 'auto').toLowerCase()}`}>{ownershipLabel(field, values[field.name], override)}</span>
            </div>
            {repeater ? (
              <RepeaterEditor
                name={field.name}
                value={values[field.name]}
                onChange={value => onChange(field.name, value)}
                disabled={disabled}
                emptyMessage={hasNoImportedContent ? `No ${repeater.itemLabel.toLowerCase()}s were found in the uploaded document.` : undefined}
              />
            ) : field.name === 'admission_steps' ? (
              <AdmissionStepsEditor value={values[field.name]} onChange={value => onChange(field.name, value)} disabled={disabled} />
            ) : field.name === 'syllabus_content' ? (
              <SyllabusEditor value={values[field.name]} onChange={value => onChange(field.name, value)} disabled={disabled} />
            ) : presentation.type === 'textarea' ? (
              <textarea
                className="input author-textarea"
                rows={3}
                value={values[field.name] || ''}
                placeholder={presentation.placeholder}
                disabled={disabled}
                onChange={event => onChange(field.name, event.target.value)}
              />
            ) : (
              <input
                className="input"
                value={values[field.name] || ''}
                placeholder={presentation.placeholder}
                disabled={disabled}
                onChange={event => onChange(field.name, event.target.value)}
              />
            )}
            {field.required && isEmpty(values[field.name]) && <div className="author-missing-note">Required before publishing.</div>}
          </div>
        );
      })}
    </div>
  );
}

function ImageSection({ descriptor, imageUrls, heroImageAlt, onImageChange, onAltChange, getImageUrl }) {
  const [openDetails, setOpenDetails] = useState(() => new Set());

  return (
    <div className="author-section-body">
      {descriptor.slots.map(slot => {
        const hasImage = Boolean(imageUrls[slot.key]);
        const detailsOpen = openDetails.has(slot.key);
        const toggleDetails = () => setOpenDetails(current => {
          const next = new Set(current);
          if (next.has(slot.key)) next.delete(slot.key); else next.add(slot.key);
          return next;
        });

        return (
        <div className="author-image" key={slot.key}>
          <div className="author-image-preview">
            {hasImage ? <img src={getImageUrl(imageUrls[slot.key])} alt="" /> : <span>Image</span>}
          </div>
          <div className="author-image-details">
            <div className="author-field-heading">
              <div>
                <span className="author-field-label">{slot.label}</span>
                {slot.required && <span className="author-required">Required</span>}
                <span className="author-badge author-badge--manual">Manual Input</span>
              </div>
              <div className="author-image-actions">
                <label className="author-link author-upload-link">
                  {hasImage ? 'Replace' : 'Add image'}
                  <input type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" onChange={event => {
                    const file = event.target.files?.[0];
                    if (!file) return;
                    const reader = new FileReader();
                    reader.onloadend = () => onImageChange(slot.key, reader.result);
                    reader.readAsDataURL(file);
                  }} />
                </label>
                {hasImage && <button type="button" className="author-link author-link--danger" onClick={() => onImageChange(slot.key, '')}>Remove</button>}
                <button type="button" className="author-link" onClick={toggleDetails}>{detailsOpen ? 'Close details' : 'Edit details'}</button>
              </div>
            </div>
            <p className="author-image-hint">{hasImage ? 'Image added' : 'Image needed'} · Recommended size {slot.dims} · Accepted formats: JPG, PNG, WebP</p>
            {detailsOpen && (
              <div className="author-image-editing">
                <label className="author-field">
                  <span>Image URL</span>
                  <input className="input" value={imageUrls[slot.key] || ''} placeholder="Paste an image URL" onChange={event => onImageChange(slot.key, event.target.value)} />
                </label>
                {slot.key === 'hero_image_url' && (
                  <label className="author-field">
                    <span>Alt Text</span>
                    <input className="input" value={heroImageAlt} placeholder="Describe the image for accessibility" onChange={event => onAltChange(event.target.value)} />
                  </label>
                )}
              </div>
            )}
          </div>
        </div>
        );
      })}
    </div>
  );
}

function sectionSource(section, values, manuallyEdited = false) {
  if (section.systemManaged) return section.data_source === 'workspace' ? 'Managed by workspace' : 'Managed by system';
  if (manuallyEdited) return 'Manually edited';

  const fields = section.fields || [];
  const imported = fields.some(field => field.source === 'AUTO' && !isEmpty(values[field.name]));
  if (imported) return 'Imported from Document';
  if (fields.some(field => field.source === 'AUTO')) return 'Manual input needed';
  if (fields.some(field => field.manual || field.source === 'MANUAL')) return 'Manual input';
  return 'Managed by system';
}

function sectionState(section, values) {
  const fields = section.fields || [];
  const repeaters = fields.filter(field => REPEATER_PRESENTATION[field.name] && Array.isArray(values[field.name]));
  const itemCount = repeaters.reduce((count, field) => count + values[field.name].length, 0);
  const filled = fields.filter(field => !isEmpty(values[field.name])).length;
  const requiredNames = new Set(fields.filter(field => field.required).map(field => field.name));
  (section.required_fields || []).forEach(entry => {
    if (!Array.isArray(entry)) requiredNames.add(entry);
  });
  const missingRequired = [...requiredNames].filter(name => isEmpty(values[name]));

  if (section.systemManaged || !fields.length) return { key: 'system', label: '⚙ System Managed', itemCount, filled: 0, total: 0, required: 0 };
  if (missingRequired.length) return { key: 'missing', label: '⚠ Required Content Missing', itemCount, filled, total: fields.length, required: requiredNames.size };
  if (requiredNames.size) return { key: 'complete', label: '✓ Ready', itemCount, filled, total: fields.length, required: requiredNames.size };
  if (filled) return { key: 'review', label: '📝 Optional · Review Content', itemCount, filled, total: fields.length, required: 0 };
  return { key: 'optional', label: 'Optional', itemCount, filled, total: fields.length, required: 0 };
}

function sectionSummary(descriptor, state) {
  if (descriptor.kind === 'images') return `${state.filled} of ${state.total} images added`;
  if (state.itemCount) return `${state.itemCount} item${state.itemCount === 1 ? '' : 's'}`;
  if (state.key === 'optional') return 'Optional section';
  if (state.total) return `${state.filled} of ${state.total} complete`;
  return descriptor.data_source === 'workspace' ? 'Managed by workspace' : 'Managed by system';
}

function WorkflowSection({ descriptor, isOpen, onToggle, values, onChange, imageProps, manuallyEdited, onManualOverride }) {
  const state = sectionState(descriptor, values);
  const id = `author-section-${descriptor.id}`;
  const source = sectionSource(descriptor, values, manuallyEdited);
  const icon = descriptor.kind === 'images'
    ? '▧'
    : state.key === 'system'
      ? '◌'
      : state.key === 'missing'
        ? '!'
        : state.key === 'manual'
          ? '✎'
          : state.key === 'review'
            ? '◐'
            : state.key === 'optional'
              ? '○'
            : '✓';
  return (
    <section className={`card author-section author-section--${state.key}`} id={id}>
      <button type="button" className="author-section-header" onClick={onToggle} aria-expanded={isOpen}>
          <span className="author-section-leading">
          <span className="author-section-icon">{icon}</span>
          <span>
            <strong>{descriptor.label}</strong>
            <small>{source} · {sectionSummary(descriptor, state)}</small>
          </span>
        </span>
        <span className="author-section-trailing">
          <span className={`author-section-status author-section-status--${state.key}`}>{state.label}</span>
          <span className="author-chevron">{isOpen ? '⌃' : '⌄'}</span>
        </span>
      </button>
      {isOpen && <div>
        {SECTION_HELP[descriptor.id] && <p className="author-section-help">{SECTION_HELP[descriptor.id]}{!descriptor.systemManaged && ' Review imported content only when the source document needs correction; complete fields marked Manual Input yourself.'}</p>}
        {descriptor.kind === 'images'
          ? <ImageSection descriptor={descriptor} {...imageProps} />
          : descriptor.systemManaged
            ? <div className="author-managed-note">{descriptor.data_source === 'workspace' ? 'This section is assembled automatically from published workspace pages.' : 'This section is generated by the system and does not need page-level editing.'}</div>
            : <SectionFields descriptor={descriptor} values={values} onChange={onChange} onManualOverride={onManualOverride} />}
      </div>}
    </section>
  );
}

function ProgressPanel({ descriptors, values }) {
  const states = descriptors.map(descriptor => sectionState(descriptor, values));
  const requiredFields = new Map();
  descriptors.forEach(descriptor => (descriptor.fields || []).forEach(field => {
    if (field.required) requiredFields.set(field.name, field);
  }));
  const requiredTotal = requiredFields.size;
  const requiredComplete = [...requiredFields].filter(([name]) => !isEmpty(values[name])).length;
  const missing = states.filter(state => state.key === 'missing');
  const review = states.filter(state => state.key === 'review');
  const percent = requiredTotal ? Math.round((requiredComplete / requiredTotal) * 100) : 100;
  const missingImages = descriptors.find(descriptor => descriptor.kind === 'images')?.slots.filter(slot => slot.required && isEmpty(values[slot.key])).length || 0;

  return (
    <section className="card author-progress">
      <div className="author-progress-heading">
        <div>
          <span className="author-eyebrow">Page Progress</span>
          <h2>{requiredComplete} / {requiredTotal} required fields complete</h2>
          <p>Required Blueprint fields determine whether this page is ready.</p>
        </div>
        <strong>{percent}% <span>complete</span></strong>
      </div>
      <div className="author-progress-track" aria-label={`${percent}% complete`}><span style={{ width: `${percent}%` }} /></div>
      <div className="author-progress-meta">
        <span>{missing.length} section{missing.length === 1 ? '' : 's'} need content</span>
        <span>{review.length} section{review.length === 1 ? '' : 's'} need review</span>
        <span>{missingImages} image{missingImages === 1 ? '' : 's'} missing</span>
      </div>
      {missing.length > 0 && <div className="author-progress-missing">Next: {descriptors.filter(descriptor => sectionState(descriptor, values).key === 'missing').slice(0, 3).map(descriptor => descriptor.label).join(', ')}</div>}
    </section>
  );
}

export default function SectionContentEditor({
  blueprint,
  editingState,
  values,
  onChange,
  slots,
  imageUrls,
  heroImageAlt,
  onImageChange,
  onAltChange,
  getImageUrl,
}) {
  const descriptors = useMemo(() => {
    if (!blueprint?.sections?.length) return [];
    const preferences = FIELD_SECTION_PREFERENCE[blueprint.page_type] || {};
    const pageSections = blueprint.sections.map(section => {
      const names = [...new Set(section.fields_used || [])];
      const fields = names
        .map(name => editingState?.fields?.[name] || blueprint.fields?.[name] || { name, source: 'MANUAL', manual: true, missing: isEmpty(values[name]) })
        .filter(field => {
          const preferredSection = preferences[field.name];
          return (!preferredSection || preferredSection === section.section) && !field.derived && !field.image && field.name !== 'hero_image_alt';
        });
      return {
        ...section,
        id: section.section,
        fields,
        systemManaged: fields.length === 0 && section.data_source !== 'page',
      };
    });
    return [...pageSections, {
      id: 'images',
      label: 'Images',
      kind: 'images',
      slots: slots || [],
      fields: (slots || []).map(slot => ({ name: slot.key, required: slot.required, manual: true })),
      required_fields: (slots || []).filter(slot => slot.required).map(slot => slot.key),
      data_source: 'page',
    }];
  }, [blueprint, editingState, slots, values]);

  const initiallyOpen = useMemo(() => descriptors.filter(descriptor => ['missing', 'manual'].includes(sectionState(descriptor, values).key)).map(descriptor => descriptor.id), [descriptors, values]);
  const [openSections, setOpenSections] = useState(null);
  const [activeSection, setActiveSection] = useState(null);
  const [manualOverrides, setManualOverrides] = useState(() => new Set());
  const resolvedOpenSections = openSections ?? new Set(initiallyOpen);
  const activeSectionId = activeSection ?? initiallyOpen[0] ?? descriptors[0]?.id;
  const imageProps = { imageUrls, heroImageAlt, onImageChange, onAltChange, getImageUrl };

  if (!descriptors.length) return null;

  const toggleSection = id => setOpenSections(current => {
    const next = new Set(current ?? initiallyOpen);
    if (next.has(id)) next.delete(id); else {
      next.clear();
      next.add(id);
    }
    return next;
  });

  const navigationGroups = Object.entries(SECTION_NAVIGATION_GROUPS)
    .map(([label, sectionIds]) => ({
      label,
      descriptors: descriptors.filter(descriptor => sectionIds.includes(descriptor.id)),
    }))
    .filter(group => group.descriptors.length > 0);
  const categorizedIds = new Set(navigationGroups.flatMap(group => group.descriptors.map(descriptor => descriptor.id)));
  const uncategorized = descriptors.filter(descriptor => !categorizedIds.has(descriptor.id));
  if (uncategorized.length) navigationGroups.push({ label: 'Other', descriptors: uncategorized });

  const selectSection = id => {
    setActiveSection(id);
    setOpenSections(current => new Set([...(current ?? initiallyOpen), id]));
  };

  return (
    <div className="author-editor">
      <ProgressPanel descriptors={descriptors} values={values} />
      <div className="author-editor-layout">
        <nav className="author-section-nav" aria-label="Page sections">
          {navigationGroups.map(group => (
            <div className="author-nav-group" key={group.label}>
              <span>{group.label}</span>
              {group.descriptors.map(descriptor => (
                <button type="button" key={descriptor.id} className={activeSectionId === descriptor.id ? 'is-active' : ''} onClick={() => {
                  selectSection(descriptor.id);
                  document.getElementById(`author-section-${descriptor.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }}>{descriptor.label}</button>
              ))}
            </div>
          ))}
        </nav>
        <div className="author-sections">
          {descriptors.map(descriptor => (
            <WorkflowSection
              key={descriptor.id}
              descriptor={descriptor}
              isOpen={resolvedOpenSections.has(descriptor.id)}
              onToggle={() => {
                setActiveSection(descriptor.id);
                toggleSection(descriptor.id);
              }}
              values={values}
              onChange={onChange}
              imageProps={imageProps}
              manuallyEdited={manualOverrides.has(descriptor.id)}
              onManualOverride={() => setManualOverrides(current => new Set([...current, descriptor.id]))}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
