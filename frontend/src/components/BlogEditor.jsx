import { useEffect, useMemo, useRef, useState } from 'react';
import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Table, TableRow, TableHeader, TableCell } from '@tiptap/extension-table';
import Image from '@tiptap/extension-image';
import { Mark, mergeAttributes } from '@tiptap/core';
import { getWorkspaceLinkCatalog } from '../api';

let sectionSequence = 0;

function createArticleSection(overrides = {}) {
  return {
    id: `article-section-${++sectionSequence}`,
    title: 'New section',
    level: 2,
    content: '<p></p>',
    hasHeading: true,
    ...overrides,
  };
}

function slugify(value) {
  return String(value || '').toLowerCase().replace(/'/g, '').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function csvToList(value) {
  return String(value || '').split(',').map(item => item.trim()).filter(Boolean);
}

function htmlToText(value) {
  return String(value || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

const PageReference = Mark.create({
  name: 'pageReference',
  addAttributes() { return { reference: { default: '' }, slug: { default: '' } }; },
  parseHTML() { return [{ tag: 'a[data-degreebaba-reference]', getAttrs: element => ({ reference: element.getAttribute('data-degreebaba-reference') || '', slug: element.getAttribute('data-degreebaba-slug') || '' }) }]; },
  renderHTML({ HTMLAttributes }) { return ['a', mergeAttributes({ 'data-degreebaba-reference': HTMLAttributes.reference, 'data-degreebaba-slug': HTMLAttributes.slug }), 0]; },
});

const StyledTableCell = TableCell.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      textAlign: { default: 'left', parseHTML: element => element.style.textAlign || 'left', renderHTML: attributes => ({ style: `text-align:${attributes.textAlign};vertical-align:${attributes.verticalAlign || 'top'}` }) },
      verticalAlign: { default: 'top', parseHTML: element => element.style.verticalAlign || 'top', renderHTML: () => ({}) },
    };
  },
});

const StyledTableHeader = TableHeader.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      textAlign: { default: 'left', parseHTML: element => element.style.textAlign || 'left', renderHTML: attributes => ({ style: `text-align:${attributes.textAlign};vertical-align:${attributes.verticalAlign || 'top'}` }) },
      verticalAlign: { default: 'top', parseHTML: element => element.style.verticalAlign || 'top', renderHTML: () => ({}) },
    };
  },
});

function splitArticleSections(value) {
  const documentNode = new DOMParser().parseFromString(value || '<p></p>', 'text/html');
  const sections = []; let current = createArticleSection({ title: 'Introduction', level: 0, content: '', hasHeading: false });
  [...documentNode.body.children].forEach(node => {
    if (/^H[2-4]$/.test(node.tagName)) { if (current.content.trim() || current.hasHeading) sections.push(current); current = createArticleSection({ title: node.textContent || 'Untitled section', level: Number(node.tagName.slice(1)), content: '', hasHeading: true }); }
    else current.content += node.outerHTML;
  });
  if (current.content.trim() || current.hasHeading || !sections.length) sections.push(current);
  return sections;
}

function serializeSections(sections) { return sections.map(section => `${section.hasHeading ? `<h${section.level}>${section.title}</h${section.level}>` : ''}${section.content}`).join(''); }

function ownershipFor(blueprint, field, fallback = 'MANUAL') {
  return blueprint?.fields?.[field]?.source || blueprint?.external_fields?.[field]?.source || fallback;
}

function OwnershipBadge({ source }) {
  return <span className={`blog-ownership-badge blog-ownership-badge--${String(source).toLowerCase()}`}>{source}</span>;
}

function FieldLabel({ blueprint, field, children, help, required = false, source }) {
  const ownership = source || ownershipFor(blueprint, field);
  return <div className="blog-field-label-wrap">
    <label className="blog-field-label">{children}{required && <span className="blog-required-mark"> *</span>}</label>
    <OwnershipBadge source={ownership} />
    {help && <p className="blog-field-help">{help}</p>}
  </div>;
}

function CollapsibleSection({ title, description, children, defaultOpen = false, badge, id }) {
  const [open, setOpen] = useState(defaultOpen);
  return <section className={`blog-section ${open ? 'blog-section--open' : ''}`}>
    <button type="button" className="blog-section-trigger" onClick={() => setOpen(current => !current)} aria-expanded={open} aria-controls={id}>
      <span className="blog-section-trigger-copy"><span className="blog-section-title-row"><span>{title}</span>{badge}</span>{description && <span className="blog-section-description">{description}</span>}</span>
      <span className="blog-section-chevron" aria-hidden="true">{open ? '−' : '+'}</span>
    </button>
    {open && <div id={id} className="blog-section-body">{children}</div>}
  </section>;
}

function ToolbarButton({ active, disabled, onClick, children, title }) {
  return <button type="button" title={title || children} disabled={disabled} onClick={onClick} className={`blog-toolbar-button ${active ? 'blog-toolbar-button--active' : ''}`}>{children}</button>;
}

function SearchableRelationPicker({ label, options, value, onChange, onChoose, multiple = false, hint }) {
  const [query, setQuery] = useState('');
  const selected = multiple ? (Array.isArray(value) ? value : []) : (value ? [value] : []);
  const selectedOptions = options.filter(option => selected.includes(option.slug));
  const matches = options.filter(option => option.label.toLowerCase().includes(query.trim().toLowerCase()) && !selected.includes(option.slug)).slice(0, 8);

  const choose = (option) => {
    if (onChoose) {
      onChoose(option);
    } else {
      onChange(multiple ? [...selected, option.slug] : option.slug);
    }
    setQuery('');
  };
  const remove = (slug) => {
    onChange(multiple ? selected.filter(value => value !== slug) : '');
  };

  return <div className="blog-relation-picker">
    <div className="blog-relation-label">{label}</div>
    {hint && <p className="blog-field-help">{hint}</p>}
    {selectedOptions.length > 0 && <div className="blog-selected-chips">{selectedOptions.map(option => <button type="button" className="blog-selected-chip" key={option.slug} onClick={() => remove(option.slug)} title={`Remove ${option.label}`}>{option.label}<span aria-hidden="true">×</span></button>)}</div>}
    <input className="blog-input" value={query} onChange={event => setQuery(event.target.value)} placeholder={`Search ${label.toLowerCase()}…`} aria-label={`Search ${label.toLowerCase()}`} />
    {query.trim() && <div className="blog-relation-results" role="listbox" aria-label={label}>
      {matches.length > 0 ? matches.map(option => <button type="button" role="option" className="blog-relation-result" key={`${option.type || 'page'}-${option.slug}`} onClick={() => choose(option)}>{option.type ? `${option.type}: ${option.label}` : option.label}</button>) : <span className="blog-relation-empty">No matching published pages.</span>}
    </div>}
  </div>;
}

function ComponentPickerModal({ kind, options, isOpen, onClose, onConfirm }) {
  const [selectedSlug, setSelectedSlug] = useState('');
  const [query, setQuery] = useState('');
  useEffect(() => { if (isOpen) { setSelectedSlug(''); setQuery(''); } }, [isOpen, kind]);

  if (!isOpen) return null;

  const title = `Link selected text to ${kind ? kind.replace(/-/g, ' ') : 'page'}`;

  const filteredOptions = options.filter(item =>
    (item.label || '').toLowerCase().includes(query.trim().toLowerCase())
  );

  const chooseSlug = slug => setSelectedSlug(slug);

  const handleInsert = () => {
    onConfirm(options.find(item => item.slug === selectedSlug));
    onClose();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card blog-picker-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title" style={{ textTransform: 'capitalize' }}>{title}</h3>
          <button type="button" className="modal-close" onClick={onClose}>×</button>
        </div>
        <div className="modal-body">
          <p className="blog-field-help" style={{ marginBottom: 12 }}>
            The article text stays unchanged. DegreeBaba stores a reference to the selected published page and creates the final internal link during preview and publishing.
          </p>
          <input
            className="blog-input"
            style={{ marginBottom: 12 }}
            placeholder={`Search ${title.toLowerCase()}…`}
            value={query}
            onChange={e => setQuery(e.target.value)}
            autoFocus
          />
          <div className="blog-picker-options" style={{ maxHeight: 220, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
            {filteredOptions.length === 0 ? (
              <div className="blog-relation-empty">No matching pages found in this workspace.</div>
            ) : (
              filteredOptions.map(opt => {
                const isSelected = selectedSlug === opt.slug;
                return (
                  <button
                    type="button"
                    key={`${opt.type || 'page'}-${opt.slug}`}
                    className={`blog-picker-option ${isSelected ? 'is-selected' : ''}`}
                    onClick={() => chooseSlug(opt.slug)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10, padding: '9px 12px',
                      background: isSelected ? '#FFF0EB' : '#FFF', border: `1px solid ${isSelected ? '#F9B6A0' : '#E2E8F0'}`,
                      borderRadius: 8, cursor: 'pointer', textAlign: 'left', width: '100%'
                    }}
                  >
                    <span style={{
                      width: 18, height: 18, borderRadius: 4, border: `1px solid ${isSelected ? '#E04015' : '#CBD5E1'}`,
                      background: isSelected ? '#E04015' : '#FFF', color: '#FFF', display: 'grid', placeItems: 'center',
                      fontSize: 12, fontWeight: 800, flexShrink: 0
                    }}>
                      {isSelected ? '✓' : ''}
                    </span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 700, color: '#1C1B22' }}>{opt.label}</div>
                      <div style={{ fontSize: 11, color: '#64748B' }}>{opt.href || opt.slug}</div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
        <div className="modal-footer">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button type="button" className="btn btn-primary" onClick={handleInsert} disabled={!selectedSlug}>
            Save link
          </button>
        </div>
      </div>
    </div>
  );
}

function TableSizePicker({ onChoose }) {
  const [open, setOpen] = useState(false);
  const [hovered, setHovered] = useState([3, 3]);
  return <div className="blog-table-picker">
    <ToolbarButton onClick={() => setOpen(current => !current)}>Table</ToolbarButton>
    {open && <div className="blog-table-picker-popover">
      <div className="blog-table-grid">{Array.from({ length: 36 }, (_, index) => { const row = Math.floor(index / 6) + 1; const col = index % 6 + 1; return <button type="button" key={`${row}-${col}`} className={row <= hovered[0] && col <= hovered[1] ? 'is-active' : ''} onMouseEnter={() => setHovered([row, col])} onClick={() => { onChoose(hovered[0], hovered[1]); setOpen(false); }}>{row} × {col}</button>; })}</div>
      <small>{hovered[0]} rows × {hovered[1]} columns</small>
    </div>}
  </div>;
}

function ArticleSectionEditor({ section, index, onChange, onRemove, onMoveUp, onMoveDown, onInsertAfter, isRecentlyMoved, onInsert, onOpenPicker }) {
  const [isFocused, setIsFocused] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [, setSelectionVersion] = useState(0);
  const sectionRef = useRef(section);
  const onChangeRef = useRef(onChange);
  const cardRef = useRef(null);

  useEffect(() => {
    sectionRef.current = section;
    onChangeRef.current = onChange;
  }, [section, onChange]);

  useEffect(() => {
    if (isRecentlyMoved && cardRef.current) {
      cardRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [isRecentlyMoved]);

  const editor = useEditor({
    extensions: [StarterKit.configure({ heading: { levels: [2, 3, 4] }, link: { openOnClick: false, autolink: true } }), Table.configure({ resizable: true }), TableRow, StyledTableHeader, StyledTableCell, Image.configure({ allowBase64: false }), PageReference],
    content: section.content || '<p></p>',
    onUpdate: ({ editor: current }) => onChangeRef.current({ ...sectionRef.current, content: current.getHTML() }),
    onFocus: () => setIsFocused(true),
    onBlur: () => setIsFocused(false),
    onSelectionUpdate: () => setSelectionVersion(version => version + 1),
    editorProps: { attributes: { class: 'blog-rich-editor blog-rich-editor--section', 'aria-label': `${section.title} content` } },
  });
  if (!editor) return null;
  const cellAttributes = editor.getAttributes('tableCell');
  const headerAttributes = editor.getAttributes('tableHeader');
  const cellAlignment = cellAttributes.textAlign || headerAttributes.textAlign || 'left';
  const verticalAlignment = cellAttributes.verticalAlign || headerAttributes.verticalAlign || 'top';

  return <section ref={cardRef} className={`blog-article-section ${isFocused ? 'is-focused' : ''} ${isRecentlyMoved ? 'is-just-moved' : ''}`}>
    <header className="blog-article-section-header">
      <div className="blog-article-section-title-wrap">
        <span className="blog-section-number">#{index + 1}</span>
        <input className="blog-section-title-input" value={section.title} onChange={event => onChange({ ...section, title: event.target.value })} aria-label="Section heading" placeholder="Section Heading" />
      </div>
      <div className="blog-article-section-actions">
        <div className="blog-section-move-group">
          <button
            type="button"
            className="blog-move-btn"
            onClick={onMoveUp}
            disabled={!onMoveUp}
            title="Move section up"
            aria-label="Move section up"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="18 15 12 9 6 15" />
            </svg>
          </button>
          <button
            type="button"
            className="blog-move-btn"
            onClick={onMoveDown}
            disabled={!onMoveDown}
            title="Move section down"
            aria-label="Move section down"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="6 9 12 15 18 9" />
            </svg>
          </button>
        </div>
        <button type="button" className="blog-section-action-btn blog-section-action-btn--insert" onClick={onInsertAfter} title="Insert section below">
          + Below
        </button>
        {onRemove && (
          <button type="button" className="blog-section-remove-btn" onClick={onRemove} title="Remove section">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              <line x1="10" y1="11" x2="10" y2="17" />
              <line x1="14" y1="11" x2="14" y2="17" />
            </svg>
            <span>Remove</span>
          </button>
        )}
      </div>
    </header>

    <div className={`blog-toolbar-container ${isFocused ? 'is-visible' : 'is-compact'}`}>
      <div className="blog-toolbar">
        <ToolbarButton active={editor.isActive('bold')} onClick={() => editor.chain().focus().toggleBold().run()}>B</ToolbarButton>
        <ToolbarButton active={editor.isActive('italic')} onClick={() => editor.chain().focus().toggleItalic().run()}><em>I</em></ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleBulletList().run()}>• List</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleOrderedList().run()}>1. List</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleBlockquote().run()}>“”</ToolbarButton>
        <TableSizePicker onChoose={(rows, cols) => editor.chain().focus().insertTable({ rows, cols, withHeaderRow: true }).run()} />
        <ToolbarButton onClick={() => editor.chain().focus().setHorizontalRule().run()}>—</ToolbarButton>
        <ToolbarButton onClick={() => onInsert(editor)}>Link</ToolbarButton>
      </div>

      {editor.isActive('table') && <div className="blog-table-tools" aria-label="Table editing tools">
        <span>Table tools</span>
        <ToolbarButton onClick={() => editor.chain().focus().addRowBefore().run()}>+ Row above</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().addRowAfter().run()}>+ Row below</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().deleteRow().run()}>Delete row</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().addColumnBefore().run()}>+ Column left</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().addColumnAfter().run()}>+ Column right</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().deleteColumn().run()}>Delete column</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().mergeCells().run()}>Merge cells</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().splitCell().run()}>Split cell</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleHeaderRow().run()}>Header row</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleHeaderColumn().run()}>Header column</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().toggleHeaderCell().run()}>Header cell</ToolbarButton>
        <span className="blog-table-tool-divider" />
        <ToolbarButton active={cellAlignment === 'left'} onClick={() => editor.chain().focus().setCellAttribute('textAlign', 'left').run()}>Left</ToolbarButton>
        <ToolbarButton active={cellAlignment === 'center'} onClick={() => editor.chain().focus().setCellAttribute('textAlign', 'center').run()}>Center</ToolbarButton>
        <ToolbarButton active={cellAlignment === 'right'} onClick={() => editor.chain().focus().setCellAttribute('textAlign', 'right').run()}>Right</ToolbarButton>
        <ToolbarButton active={cellAlignment === 'justify'} onClick={() => editor.chain().focus().setCellAttribute('textAlign', 'justify').run()}>Justify</ToolbarButton>
        <ToolbarButton active={verticalAlignment === 'top'} onClick={() => editor.chain().focus().setCellAttribute('verticalAlign', 'top').run()}>Top</ToolbarButton>
        <ToolbarButton active={verticalAlignment === 'middle'} onClick={() => editor.chain().focus().setCellAttribute('verticalAlign', 'middle').run()}>Middle</ToolbarButton>
        <ToolbarButton active={verticalAlignment === 'bottom'} onClick={() => editor.chain().focus().setCellAttribute('verticalAlign', 'bottom').run()}>Bottom</ToolbarButton>
        <ToolbarButton onClick={() => editor.chain().focus().deleteTable().run()}>Delete table</ToolbarButton>
      </div>}

      <div className="blog-component-actions">
        <span className="blog-component-label">⚡ Link text to:</span>
        {[
          ['course', 'Course'],
          ['specialization', 'Specialization'],
          ['blog', 'Related blog']
        ].map(([kind, label]) => (
          <button type="button" key={kind} className="blog-component-chip" onMouseDown={event => event.preventDefault()} onClick={() => onOpenPicker(editor, kind)}>
            + {label}
          </button>
        ))}
      </div>
    </div>

    <EditorContent editor={editor} />
  </section>;
}

export default function BlogEditor({ session, blueprint, loading, onBack, onPreview }) {
  const initial = session.acf_data || {};
  const [data, setData] = useState(() => ({
    title: initial.title || '',
    subtitle: initial.subtitle || '',
    excerpt: initial.excerpt || '',
    seo_title: initial.seo_title || '',
    meta_description: initial.meta_description || '',
    author: initial.author || '',
    author_role: initial.author_role || '',
    published_date: initial.published_date || '',
    category: initial.category || initial.tag || '',
    tags: Array.isArray(initial.tags) ? initial.tags.join(', ') : initial.tags || '',
    focus_keyword: initial.focus_keyword || '',
    read_time_override: initial.read_time_override || '',
    cta_title: initial.cta_title || '',
    cta_description: initial.cta_description || '',
    cta_label: initial.cta_label || '',
    primary_course_slug: initial.primary_course_slug || '',
    primary_specialization_slug: initial.primary_specialization_slug || '',
    related_course_slugs: initial.related_course_slugs || [],
    related_specialization_slugs: initial.related_specialization_slugs || [],
    related_blog_slugs: initial.related_blog_slugs || [],
    mentioned_university_slugs: initial.mentioned_university_slugs || [],
    slug: session.slug || slugify(initial.title),
    hero_image_alt: initial.hero_image_alt || '',
  }));

  const [images, setImages] = useState(() => ({
    ...(session.images || {}),
    hero_image_url: session.images?.hero_image_url || initial.hero_image_url || '',
    og_image_url: session.images?.og_image_url || initial.og_image_url || '',
  }));

  const [catalog, setCatalog] = useState({ courses: [], specializations: [], blogs: [], universities: [] });
  const [sections, setSections] = useState(() => splitArticleSections(initial.content_html));
  const [activeEditor, setActiveEditor] = useState(null);
  const [pickerModal, setPickerModal] = useState(null); // { editor, kind }
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editorError, setEditorError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!session.university_slug) return;
    getWorkspaceLinkCatalog(session.university_slug).then(setCatalog).catch(() => setCatalog({ courses: [], specializations: [], blogs: [], universities: [] }));
  }, [session.university_slug]);

  const pickerOptions = useMemo(() => {
    if (!pickerModal) return [];
    const k = pickerModal.kind;
    if (k === 'blog') return catalog.blogs.filter(item => item.slug !== session.slug);
    if (k === 'specialization') return catalog.specializations;
    return catalog.courses;
  }, [pickerModal, catalog, session.slug]);

  const handleConfirmPicker = (selectedPage) => {
    if (!pickerModal || !pickerModal.editor || !selectedPage) return;
    const { editor, selection } = pickerModal;
    const chain = editor.chain().focus();
    if (selection) chain.setTextSelection(selection);
    const attrs = { reference: pickerModal.kind, slug: selectedPage.slug };
    if (selection && selection.from !== selection.to) {
      chain.setMark('pageReference', attrs).run();
    } else {
      chain.insertContent({ type: 'text', text: selectedPage.label, marks: [{ type: 'pageReference', attrs }] }).run();
    }
    setPickerModal(null);
  };

  const linkableEntities = useMemo(() => [
    ...catalog.courses.map(item => ({ ...item, type: 'Course' })),
    ...catalog.specializations.map(item => ({ ...item, type: 'Specialization' })),
    ...catalog.blogs.filter(item => item.slug !== session.slug).map(item => ({ ...item, type: 'Blog' })),
    ...catalog.universities.map(item => ({ ...item, type: 'University' })),
  ], [catalog, session.slug]);

  const contentHtml = serializeSections(sections);
  const bodyText = htmlToText(contentHtml);
  const wordCount = bodyText ? bodyText.split(/\s+/).length : 0;
  const relationCount = [data.primary_course_slug, data.primary_specialization_slug, ...(data.related_course_slugs || []), ...(data.related_specialization_slugs || []), ...(data.related_blog_slugs || []), ...(data.mentioned_university_slugs || [])].filter(Boolean).length;
  const requiredReady = Boolean(data.title.trim() && bodyText && images.hero_image_url);

  const checklist = [
    { label: 'Article title added', complete: Boolean(data.title.trim()), required: true },
    { label: 'Article content added', complete: Boolean(bodyText), required: true },
    { label: 'Featured image added', complete: Boolean(images.hero_image_url), required: true },
    { label: 'SEO title added', complete: Boolean(data.seo_title.trim()), recommended: true },
    { label: 'Meta description added', complete: Boolean(data.meta_description.trim()), recommended: true },
    { label: 'Related content selected', complete: relationCount > 0, recommended: true },
  ];

  const completedCount = checklist.filter(item => item.complete).length;
  const progressPercent = Math.round((completedCount / checklist.length) * 100);

  const [recentlyMovedId, setRecentlyMovedId] = useState(null);
  const [actionToast, setActionToast] = useState(null);
  const toastTimerRef = useRef(null);

  const triggerToast = (message) => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setActionToast(message);
    toastTimerRef.current = setTimeout(() => setActionToast(null), 2400);
  };

  const set = (key, value) => setData(current => ({ ...current, [key]: value }));
  const updateTitle = (value) => setData(current => ({ ...current, title: value, slug: current.slug === slugify(current.title) ? slugify(value) : current.slug }));
  const moveSection = (from, to) => {
    if (to < 0 || to >= sections.length) return;
    const targetSection = sections[from];
    setSections(current => {
      const next = [...current];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
    setRecentlyMovedId(targetSection.id);
    triggerToast(`⚡ Section #${from + 1} moved ${to < from ? 'up' : 'down'} to #${to + 1}`);
  };

  const insertSectionAfter = (index) => {
    const newSection = createArticleSection();
    setSections(current => [
      ...current.slice(0, index + 1),
      newSection,
      ...current.slice(index + 1),
    ]);
    setRecentlyMovedId(newSection.id);
    triggerToast(`+ New section inserted below #${index + 1}`);
  };
  const addLink = (href = '') => {
    const target = href || window.prompt('Paste a URL for the selected text');
    if (target) activeEditor?.chain().focus().extendMarkRange('link').setLink({ href: target }).run();
  };
  const uploadImage = (field, file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setImages(current => ({ ...current, [field]: reader.result }));
    reader.readAsDataURL(file);
  };
  const submit = async () => {
    setEditorError('');
    const content_html = contentHtml;
    if (!requiredReady) {
      setEditorError('Add the article title, body, and featured image before generating a preview.');
      return;
    }
    setSubmitting(true);
    try {
      await onPreview({ ...initial, ...data, content_html, tags: csvToList(data.tags) }, images, data.slug);
    } catch (error) {
      const detail = error.response?.data?.detail;
      const labels = detail?.missing_fields?.map(field => field.label).filter(Boolean) || [];
      setEditorError(labels.length ? `${detail.message} Missing: ${labels.join(', ')}.` : detail?.message || error.message || 'Preview could not be generated.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!blueprint) return <div className="card" style={{ padding: 24 }}>Loading the Blog editing workspace…</div>;

  return (
    <div className={`blog-editor-app ${drawerOpen ? 'has-open-drawer' : 'has-closed-drawer'}`}>
      {/* ===== STICKY TOP STATUS BAR ===== */}
      <header className="blog-editor-sticky-bar">
        <div className="blog-sticky-left">
          <button type="button" className="btn btn-secondary btn-sm blog-back-btn" onClick={onBack}>
            ← Back
          </button>
          <div className="blog-sticky-title-wrap">
            <span className="blog-sticky-title" title={data.title}>{data.title || 'Untitled Article'}</span>
          </div>
        </div>

        <div className="blog-sticky-center">
          <span className={`blog-readiness-badge ${requiredReady ? 'is-ready' : 'is-draft'}`}>
            {requiredReady ? '✓ Ready for Review' : '● Draft in Progress'}
          </span>
          <div className="blog-metric-divider" />
          <div className="blog-metric">
            <span className="blog-metric-val">{wordCount.toLocaleString()}</span>
            <span className="blog-metric-lbl">words</span>
          </div>
          <div className="blog-metric-divider" />
          <div className="blog-metric">
            <span className="blog-metric-val">~{Math.max(1, Math.ceil(wordCount / 200))} min</span>
            <span className="blog-metric-lbl">read</span>
          </div>
          <div className="blog-metric-divider" />
          <div className="blog-progress-compact" onClick={() => setDrawerOpen(true)} title="Click to view publishing checklist">
            <div className="blog-progress-bar-track">
              <div className="blog-progress-bar-fill" style={{ width: `${progressPercent}%` }} />
            </div>
            <span className="blog-progress-pct">{progressPercent}%</span>
          </div>
        </div>

        <div className="blog-sticky-right">
          <button
            type="button"
            className={`btn ${drawerOpen ? 'btn-primary' : 'btn-secondary'} btn-sm`}
            onClick={() => setDrawerOpen(prev => !prev)}
          >
            ⚙️ Settings & SEO
          </button>
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={submit}
            disabled={submitting || loading}
          >
            {submitting || loading ? 'Generating preview…' : 'Generate preview →'}
          </button>
        </div>
      </header>

      {editorError && <div className="blog-editor-error" role="alert">{editorError}</div>}

      <div className="blog-editor-body">
        {/* ===== WIDE MAIN WRITING CANVAS (75-80% Width) ===== */}
        <main className="blog-editor-canvas">
          <div className="blog-article-header-hero">
            <input
              className="blog-title-headline"
              value={data.title}
              onChange={event => updateTitle(event.target.value)}
              placeholder="Article Title..."
            />
            <textarea
              className="blog-excerpt-textarea"
              value={data.excerpt}
              onChange={event => set('excerpt', event.target.value)}
              rows={4}
              placeholder="Write a concise excerpt or subtitle..."
            />
          </div>

          <div className="blog-sections-list">
            {sections.map((section, index) => (
              <ArticleSectionEditor
                key={section.id}
                section={section}
                index={index}
                isRecentlyMoved={recentlyMovedId === section.id}
                onChange={updated => setSections(current => current.map((item, itemIndex) => itemIndex === index ? updated : item))}
                onRemove={sections.length > 1 ? () => setSections(current => current.filter((_, itemIndex) => itemIndex !== index)) : null}
                onMoveUp={index > 0 ? () => moveSection(index, index - 1) : null}
                onMoveDown={index < sections.length - 1 ? () => moveSection(index, index + 1) : null}
                onInsertAfter={() => insertSectionAfter(index)}
                onInsert={current => setActiveEditor(current)}
                onOpenPicker={(ed, kind) => setPickerModal({ editor: ed, kind, selection: { from: ed.state.selection.from, to: ed.state.selection.to } })}
              />
            ))}
          </div>

          <button
            type="button"
            className="blog-add-section-btn"
            onClick={() => setSections(current => [...current, createArticleSection()])}
          >
            + Add New Section
          </button>
        </main>

        {/* ===== COLLAPSIBLE RIGHT SIDEBAR DRAWER ===== */}
        <aside className={`blog-editor-drawer ${drawerOpen ? 'is-open' : 'is-collapsed'}`}>
          <div className="blog-drawer-header">
            <h3 className="blog-drawer-title">Publishing & Settings</h3>
            <button type="button" className="blog-drawer-close-btn" onClick={() => setDrawerOpen(false)}>✕</button>
          </div>

          <div className="blog-drawer-content">
            {/* Widget: Publishing Progress */}
            <div className="blog-progress-widget">
              <div className="blog-progress-widget-header">
                <strong>Publishing Progress</strong>
                <span>{progressPercent}%</span>
              </div>
              <div className="blog-progress-bar-track">
                <div className="blog-progress-bar-fill" style={{ width: `${progressPercent}%` }} />
              </div>
              <div className="blog-progress-checklist">
                {checklist.map(item => (
                  <div key={item.label} className={`blog-progress-check-item ${item.complete ? 'is-complete' : 'is-pending'}`}>
                    <span>{item.complete ? '✓' : '○'}</span>
                    <span>{item.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Basic Information */}
            <CollapsibleSection id="basic-info-drawer" title="Featured Image" defaultOpen badge={<OwnershipBadge source="AUTO" />}>
              <div className="blog-form-grid">
                <div>
                  <FieldLabel blueprint={blueprint} field="hero_image_url" required help="Article header cover image.">
                    Featured image
                  </FieldLabel>
                  <input className="blog-file-input" type="file" accept="image/*" onChange={e => uploadImage('hero_image_url', e.target.files?.[0])} />
                  {images.hero_image_url && <img className="blog-image-preview" src={images.hero_image_url} alt="Featured preview" />}
                </div>
                <div>
                  <FieldLabel blueprint={blueprint} field="hero_image_alt">Alt Text</FieldLabel>
                  <input className="blog-input" value={data.hero_image_alt} onChange={e => set('hero_image_alt', e.target.value)} placeholder="Describe the image" />
                </div>
              </div>
            </CollapsibleSection>

            {/* SEO */}
            <CollapsibleSection id="seo-drawer" title="SEO Settings" badge={<OwnershipBadge source="MANUAL" />}>
              <FieldLabel blueprint={blueprint} field="slug">Slug</FieldLabel>
              <input
                className="blog-input mb-12"
                value={data.slug}
                onChange={e => set('slug', slugify(e.target.value))}
                placeholder="e.g. ignou-mba-admission-2026"
              />

              <FieldLabel blueprint={blueprint} field="seo_title">SEO Title</FieldLabel>
              <input
                className="blog-input mb-12"
                value={data.seo_title}
                onChange={e => set('seo_title', e.target.value)}
                placeholder="e.g. IGNOU MBA Admission 2026: Fees, Eligibility & Process"
              />

              <FieldLabel blueprint={blueprint} field="meta_description">Meta Description</FieldLabel>
              <textarea
                className="blog-input mb-12"
                rows={3}
                value={data.meta_description}
                onChange={e => set('meta_description', e.target.value)}
                placeholder="e.g. Complete guide to IGNOU MBA admissions 2026. Check eligibility, course fees, application deadlines, and semester syllabus."
              />

              <FieldLabel blueprint={blueprint} field="focus_keyword">Focus Keyword</FieldLabel>
              <input
                className="blog-input"
                value={data.focus_keyword}
                onChange={e => set('focus_keyword', e.target.value)}
                placeholder="e.g. IGNOU MBA Admission 2026"
              />
            </CollapsibleSection>

            {/* Publishing Metadata */}
            <CollapsibleSection id="publishing-drawer" title="Publishing Metadata" badge={<OwnershipBadge source="MANUAL" />}>
              <FieldLabel blueprint={blueprint} field="author">Author</FieldLabel>
              <input className="blog-input mb-12" value={data.author} onChange={e => set('author', e.target.value)} />

              <FieldLabel blueprint={blueprint} field="author_role">Author Role</FieldLabel>
              <input className="blog-input mb-12" value={data.author_role} onChange={e => set('author_role', e.target.value)} />

              <FieldLabel blueprint={blueprint} field="category">Category</FieldLabel>
              <input className="blog-input mb-12" value={data.category} onChange={e => set('category', e.target.value)} />

              <FieldLabel blueprint={blueprint} field="tags">Tags</FieldLabel>
              <input className="blog-input mb-12" value={data.tags} onChange={e => set('tags', e.target.value)} placeholder="MBA, admissions, online" />

              <FieldLabel blueprint={blueprint} field="published_date">Publish Date</FieldLabel>
              <input className="blog-input" type="date" value={data.published_date} onChange={e => set('published_date', e.target.value)} />
            </CollapsibleSection>
          </div>
        </aside>
      </div>

      <ComponentPickerModal
        kind={pickerModal?.kind}
        options={pickerOptions}
        isOpen={Boolean(pickerModal)}
        onClose={() => setPickerModal(null)}
        onConfirm={handleConfirmPicker}
      />

      {actionToast && (
        <div className="blog-action-toast" role="status" aria-live="polite">
          {actionToast}
        </div>
      )}
    </div>
  );
}
