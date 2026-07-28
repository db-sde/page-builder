import { useMemo, useState } from 'react';
import {
  FIELD_SECTION_PREFERENCE,
  getFieldPresentation,
  REPEATER_PRESENTATION,
  SECTION_FIELD_ADDITIONS,
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
              {field.manual && <span className="author-badge author-badge--manual">Your input</span>}
            </div>
            {repeater ? (
              <RepeaterEditor
                name={field.name}
                value={values[field.name]}
                onChange={value => onChange(field.name, value)}
                disabled={disabled}
                emptyMessage={hasNoImportedContent ? `No ${repeater.itemLabel.toLowerCase()}s were found in the uploaded document.` : undefined}
              />
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
              </div>
              <div className="author-image-actions">
                <label className="author-link author-upload-link">
                  {hasImage ? 'Replace' : 'Add image'}
                  <input type="file" accept="image/*" onChange={event => {
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
            <p className="author-image-hint">{hasImage ? 'Image added' : 'Image needed'} · Recommended {slot.dims}</p>
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
  const missingRequired = (section.required_fields || []).filter(field => (
    Array.isArray(field) ? field.every(name => isEmpty(values[name])) : isEmpty(values[field])
  ));
  const fields = section.fields || [];
  const repeaters = fields.filter(field => REPEATER_PRESENTATION[field.name] && Array.isArray(values[field.name]));
  const itemCount = repeaters.reduce((count, field) => count + values[field.name].length, 0);
  const missingManual = fields.some(field => (field.manual || field.source === 'MANUAL') && isEmpty(values[field.name]));
  const missingImported = fields.some(field => field.source === 'AUTO' && isEmpty(values[field.name]));
  const missingAny = fields.some(field => isEmpty(values[field.name]));
  const filled = fields.filter(field => !isEmpty(values[field.name])).length;

  if (section.systemManaged || !fields.length) return { key: 'system', label: '⚙ System Managed', itemCount, filled: 0, total: 0 };
  if (missingManual && !missingImported) return { key: 'manual', label: '✏ Manual Input Required', itemCount, filled, total: fields.length };
  if (missingRequired.length || missingImported || !filled) return { key: 'missing', label: '⚠ Missing Content', itemCount, filled, total: fields.length };
  if (missingAny) return { key: 'review', label: '📝 Review Imported Content', itemCount, filled, total: fields.length };
  return { key: 'complete', label: '✓ Complete', itemCount, filled, total: fields.length };
}

function sectionSummary(descriptor, state) {
  if (descriptor.kind === 'images') return `${state.filled} of ${state.total} images added`;
  if (state.itemCount) return `${state.itemCount} item${state.itemCount === 1 ? '' : 's'}`;
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
      {isOpen && (descriptor.kind === 'images'
        ? <ImageSection descriptor={descriptor} {...imageProps} />
        : descriptor.systemManaged
          ? <div className="author-managed-note">{descriptor.data_source === 'workspace' ? 'This section is assembled automatically from published workspace pages.' : 'This section is generated by the system and does not need page-level editing.'}</div>
          : <SectionFields descriptor={descriptor} values={values} onChange={onChange} onManualOverride={onManualOverride} />
      )}
    </section>
  );
}

function ProgressPanel({ descriptors, values }) {
  const states = descriptors.map(descriptor => sectionState(descriptor, values));
  const authorable = states.filter(state => state.key !== 'system');
  const complete = authorable.filter(state => state.key === 'complete').length;
  const missing = states.filter(state => ['missing', 'manual'].includes(state.key));
  const review = states.filter(state => state.key === 'review');
  const percent = authorable.length ? Math.round((complete / authorable.length) * 100) : 100;
  const missingImages = descriptors.find(descriptor => descriptor.kind === 'images')?.slots.filter(slot => slot.required && isEmpty(values[slot.key])).length || 0;

  return (
    <section className="card author-progress">
      <div className="author-progress-heading">
        <div>
          <span className="author-eyebrow">Page Progress</span>
          <h2>{complete} / {authorable.length} sections complete</h2>
          <p>Finish the sections below, then generate a preview.</p>
        </div>
        <strong>{percent}% <span>complete</span></strong>
      </div>
      <div className="author-progress-track" aria-label={`${percent}% complete`}><span style={{ width: `${percent}%` }} /></div>
      <div className="author-progress-meta">
        <span>{missing.length} section{missing.length === 1 ? '' : 's'} need content</span>
        <span>{review.length} section{review.length === 1 ? '' : 's'} need review</span>
        <span>{missingImages} image{missingImages === 1 ? '' : 's'} missing</span>
      </div>
      {missing.length > 0 && <div className="author-progress-missing">Next: {descriptors.filter(descriptor => ['missing', 'manual'].includes(sectionState(descriptor, values).key)).slice(0, 3).map(descriptor => descriptor.label).join(', ')}</div>}
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
      const additions = SECTION_FIELD_ADDITIONS[blueprint.page_type]?.[section.section] || [];
      const names = [...new Set([...(section.fields_used || []), ...additions])];
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
