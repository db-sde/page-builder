import { useEffect, useMemo, useState } from 'react';
import { EditorContent, useEditor } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Table, TableRow, TableHeader, TableCell } from '@tiptap/extension-table';
import Image from '@tiptap/extension-image';
import { Node, mergeAttributes } from '@tiptap/core';
import { getWorkspaceLinkCatalog } from '../api';

function slugify(value) {
  return String(value || '').toLowerCase().replace(/'/g, '').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}

function csvToList(value) {
  return String(value || '').split(',').map(item => item.trim()).filter(Boolean);
}

function htmlToText(value) {
  return String(value || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

const DynamicComponent = Node.create({
  name: 'dynamicComponent', group: 'block', atom: true,
  addAttributes() { return { component: { default: 'course-cards' }, slugs: { default: '' } }; },
  parseHTML() { return [{ tag: 'div[data-degreebaba-component]', getAttrs: element => ({ component: element.getAttribute('data-degreebaba-component'), slugs: element.getAttribute('data-degreebaba-slugs') || '' }) }]; },
  renderHTML({ HTMLAttributes }) { return ['div', mergeAttributes({ 'data-degreebaba-component': HTMLAttributes.component, 'data-degreebaba-slugs': HTMLAttributes.slugs, class: 'blog-dynamic-reference' })]; },
  addNodeView() { return ({ node }) => { const element = document.createElement('div'); element.className = 'blog-dynamic-reference'; element.textContent = `Dynamic ${node.attrs.component.replace(/-/g, ' ')} block`; return { dom: element }; }; },
});

function splitArticleSections(value) {
  const documentNode = new DOMParser().parseFromString(value || '<p></p>', 'text/html');
  const sections = []; let current = { title: 'Introduction', level: 0, content: '', hasHeading: false };
  [...documentNode.body.children].forEach(node => {
    if (/^H[2-4]$/.test(node.tagName)) { if (current.content.trim() || current.hasHeading) sections.push(current); current = { title: node.textContent || 'Untitled section', level: Number(node.tagName.slice(1)), content: '', hasHeading: true }; }
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

function ArticleSectionEditor({ section, index, onChange, onRemove, onInsert, onDynamic }) {
  const editor = useEditor({
    extensions: [StarterKit.configure({ heading: { levels: [2, 3, 4] }, link: { openOnClick: false, autolink: true } }), Table.configure({ resizable: true }), TableRow, TableHeader, TableCell, Image.configure({ allowBase64: false }), DynamicComponent],
    content: section.content || '<p></p>',
    onUpdate: ({ editor: current }) => onChange({ ...section, content: current.getHTML() }),
    editorProps: { attributes: { class: 'blog-rich-editor blog-rich-editor--section', 'aria-label': `${section.title} content` } },
  });
  if (!editor) return null;
  const insertComponent = (component) => { editor.chain().focus().insertContent({ type: 'dynamicComponent', attrs: { component, slugs: '' } }).run(); onDynamic(editor, component); };
  return <section className="blog-article-section">
    <header><div><span className="blog-section-number">{index + 1}</span><input className="blog-section-title-input" value={section.title} onChange={event => onChange({ ...section, title: event.target.value })} aria-label="Section heading" /></div>{onRemove && <button type="button" className="blog-section-remove" onClick={onRemove}>Remove</button>}</header>
    <div className="blog-toolbar"><ToolbarButton active={editor.isActive('bold')} onClick={() => editor.chain().focus().toggleBold().run()}>B</ToolbarButton><ToolbarButton active={editor.isActive('italic')} onClick={() => editor.chain().focus().toggleItalic().run()}><em>I</em></ToolbarButton><ToolbarButton onClick={() => editor.chain().focus().toggleBulletList().run()}>• List</ToolbarButton><ToolbarButton onClick={() => editor.chain().focus().toggleOrderedList().run()}>1. List</ToolbarButton><ToolbarButton onClick={() => editor.chain().focus().toggleBlockquote().run()}>“”</ToolbarButton><ToolbarButton onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()}>Table</ToolbarButton><ToolbarButton onClick={() => editor.chain().focus().setHorizontalRule().run()}>—</ToolbarButton><ToolbarButton onClick={() => onInsert(editor)}>Internal link</ToolbarButton></div>
    <div className="blog-component-actions"><span>Insert workspace data</span>{[['course-cards', 'Course cards'], ['specialization-buttons', 'Specializations'], ['related-blogs', 'Related blogs'], ['fee-table', 'Fee table'], ['syllabus', 'Syllabus'], ['cta', 'CTA']].map(([kind, label]) => <button type="button" key={kind} onClick={() => insertComponent(kind)}>{label}</button>)}</div>
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
  const [pendingComponent, setPendingComponent] = useState('');
  const [editorError, setEditorError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [, setContentVersion] = useState(0);

  useEffect(() => {
    if (!session.university_slug) return;
    getWorkspaceLinkCatalog(session.university_slug).then(setCatalog).catch(() => setCatalog({ courses: [], specializations: [], blogs: [], universities: [] }));
  }, [session.university_slug]);

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

  const set = (key, value) => setData(current => ({ ...current, [key]: value }));
  const updateTitle = (value) => setData(current => ({ ...current, title: value, slug: current.slug === slugify(current.title) ? slugify(value) : current.slug }));
  const addLink = (href = '') => {
    const target = href || window.prompt('Paste a URL for the selected text');
    if (target) activeEditor?.chain().focus().extendMarkRange('link').setLink({ href: target }).run();
  };
  const applyDynamicSource = (item) => {
    if (!activeEditor || !pendingComponent) return;
    activeEditor.chain().focus().updateAttributes('dynamicComponent', { component: pendingComponent, slugs: item.slug }).run();
    setPendingComponent('');
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

  return <div className="blog-editor-page">
    <header className="blog-editor-header">
      <div><div className="blog-editor-eyebrow">Content workspace</div><h1 className="topbar-title">Blog Editor</h1><p className="topbar-subtitle">Write first. Add links, SEO, and publishing details only when the article is ready.</p></div>
      <div className={`blog-readiness ${requiredReady ? 'blog-readiness--ready' : ''}`}><span>{requiredReady ? 'Ready for review' : 'Draft in progress'}</span><small>{wordCount.toLocaleString()} words · about {Math.max(1, Math.ceil(wordCount / 200))} min read</small></div>
    </header>
    {editorError && <div className="blog-editor-error" role="alert">{editorError}</div>}

    <div className="blog-editor-workspace">
      <main className="blog-editor-main">
        <CollapsibleSection id="basic-information" title="Basic information" description="Set the article identity and the images readers see first." defaultOpen badge={<OwnershipBadge source="AUTO" />}>
          <div className="blog-form-grid">
            <div className="blog-form-span-2"><FieldLabel blueprint={blueprint} field="title" required help="Parsed from the DOCX and shown as the article heading. Keep it clear and specific.">Article title</FieldLabel><input className="blog-input blog-input--title" value={data.title} onChange={event => updateTitle(event.target.value)} /></div>
            <div className="blog-form-span-2"><FieldLabel blueprint={blueprint} field="excerpt" help="Shown below the title and used as the fallback search description. Aim for one concise paragraph.">Excerpt</FieldLabel><textarea className="blog-input" value={data.excerpt} onChange={event => set('excerpt', event.target.value)} rows={3} placeholder="An optional summary. The first article paragraph remains the parser fallback." /></div>
            <div><FieldLabel blueprint={blueprint} field="hero_image_url" required help="Shown in the article hero and required before previewing.">Featured image</FieldLabel><input className="blog-file-input" type="file" accept="image/*" onChange={event => uploadImage('hero_image_url', event.target.files?.[0])} />{images.hero_image_url && <img className="blog-image-preview" src={images.hero_image_url} alt="Featured preview" />}</div>
            <div><FieldLabel blueprint={blueprint} field="hero_image_alt" help="Describes the featured image for screen readers. Keep it factual and concise.">Image alt text</FieldLabel><input className="blog-input" value={data.hero_image_alt} onChange={event => set('hero_image_alt', event.target.value)} placeholder="Describe the image" /><FieldLabel blueprint={blueprint} field="og_image_url" help="Optional image used when this article is shared on social platforms.">Social share image</FieldLabel><input className="blog-file-input" type="file" accept="image/*" onChange={event => uploadImage('og_image_url', event.target.files?.[0])} /></div>
          </div>
        </CollapsibleSection>

        <CollapsibleSection id="article-content" title="Article content" description="This is the primary writing space. Format the article without changing its factual source material." defaultOpen badge={<OwnershipBadge source="AUTO" />}>
          <div className="blog-content-summary"><span>{sections.length} independently editable sections</span><span>{wordCount.toLocaleString()} words</span></div>
          {sections.map((section, index) => <ArticleSectionEditor key={`${index}-${section.title}`} section={section} index={index} onChange={updated => setSections(current => current.map((item, itemIndex) => itemIndex === index ? updated : item))} onRemove={sections.length > 1 ? () => setSections(current => current.filter((_, itemIndex) => itemIndex !== index)) : null} onInsert={current => setActiveEditor(current)} onDynamic={(current, kind) => { setActiveEditor(current); setPendingComponent(kind); }} />)}
          <button type="button" className="blog-add-section" onClick={() => setSections(current => [...current, { title: 'New section', level: 2, content: '<p></p>', hasHeading: true }])}>+ Add article section</button>
          <p className="blog-field-help blog-editor-tip">Headings preserve the parser’s structure and build the table of contents. Dynamic blocks store only workspace references; the published data is resolved at render time.</p>
        </CollapsibleSection>

        <CollapsibleSection id="internal-linking" title="Internal linking" description="Connect readers to relevant pages already published in this workspace." badge={<OwnershipBadge source="MANUAL" />}>
          <div className="blog-inline-linker"><FieldLabel blueprint={blueprint} field="related_course_slugs" help="Select text in the article, then choose an existing workspace page to create a link.">Insert an internal link</FieldLabel><SearchableRelationPicker label="workspace page" options={linkableEntities} value={[]} onChoose={item => addLink(item.href)} hint="Select article text first. This does not change the related-content cards." />{session.entity_suggestions?.length > 0 && <div className="blog-suggestions"><span>Mentioned in this article</span>{session.entity_suggestions.map(item => <button type="button" key={`${item.type}-${item.slug}`} onClick={() => addLink(item.href)}>{item.label}</button>)}</div>}</div>
          {pendingComponent && <SearchableRelationPicker label={`source for ${pendingComponent.replace(/-/g, ' ')}`} options={pendingComponent === 'related-blogs' ? catalog.blogs.filter(item => item.slug !== session.slug) : pendingComponent === 'specialization-buttons' ? catalog.specializations : [...catalog.courses, ...catalog.specializations]} value={[]} onChoose={applyDynamicSource} hint="Choose the published page whose current data should be rendered in this article." />}
          <p className="blog-field-help">Select text in an article section, then choose a published page. To add reusable cards, fee tables, syllabus, or CTA blocks, use the “Insert workspace data” buttons inside the relevant section and select the source from this search.</p>
        </CollapsibleSection>
      </main>

      <aside className="blog-editor-sidebar">
        <section className="blog-checklist" aria-label="Publishing checklist"><div className="blog-checklist-heading"><div><span>Publishing checklist</span><small>Live guidance — it does not block writing.</small></div><OwnershipBadge source="SYSTEM" /></div><div className="blog-checklist-items">{checklist.map(item => <div className={`blog-checklist-item ${item.complete ? 'blog-checklist-item--complete' : ''}`} key={item.label}><span aria-hidden="true">{item.complete ? '✓' : item.required ? '!' : '○'}</span><div>{item.label}<small>{item.complete ? 'Complete' : item.required ? 'Required before preview' : 'Recommended'}</small></div></div>)}</div><div className={`blog-checklist-ready ${requiredReady ? 'blog-checklist-ready--complete' : ''}`}>{requiredReady ? 'Required article fields are ready for review.' : 'Complete the required article fields to generate a preview.'}</div></section>

        <CollapsibleSection id="seo" title="SEO" description="Search and sharing details. Optional, but recommended before publishing." badge={<OwnershipBadge source="MANUAL" />}>
          <FieldLabel blueprint={blueprint} field="slug" help="Creates the article URL. Derived from the title until you edit it.">Slug</FieldLabel><input className="blog-input" value={data.slug} onChange={event => set('slug', slugify(event.target.value))} /><div className="blog-derived-note"><OwnershipBadge source="DERIVED" /> Canonical URL is created from this slug and the workspace primary domain.</div>
          <FieldLabel blueprint={blueprint} field="seo_title" help="Appears in Google search results. Recommended under 60 characters.">SEO title</FieldLabel><input className="blog-input" value={data.seo_title} onChange={event => set('seo_title', event.target.value)} /><FieldLabel blueprint={blueprint} field="meta_description" help="Appears beneath the title in search results. Aim for 140–160 characters.">Meta description</FieldLabel><textarea className="blog-input" rows={3} value={data.meta_description} onChange={event => set('meta_description', event.target.value)} /><FieldLabel blueprint={blueprint} field="focus_keyword" help="The primary keyword this article targets. It is editorial guidance only.">Focus keyword</FieldLabel><input className="blog-input" value={data.focus_keyword} onChange={event => set('focus_keyword', event.target.value)} /><FieldLabel blueprint={blueprint} field="read_time_override" help="Leave blank to use the automatic reading-time calculation.">Read time override</FieldLabel><input className="blog-input" value={data.read_time_override} onChange={event => set('read_time_override', event.target.value)} placeholder="For example: 8 min read" />
        </CollapsibleSection>

        <CollapsibleSection id="publishing" title="Publishing" description="Optional editorial credits and categorisation." badge={<OwnershipBadge source="MANUAL" />}>
          <FieldLabel blueprint={blueprint} field="author" help="Displayed on the published article and included in Article schema when supplied.">Author</FieldLabel><input className="blog-input" value={data.author} onChange={event => set('author', event.target.value)} /><FieldLabel blueprint={blueprint} field="author_role" help="Optional role displayed beneath the author name.">Author role</FieldLabel><input className="blog-input" value={data.author_role} onChange={event => set('author_role', event.target.value)} /><FieldLabel blueprint={blueprint} field="category" help="Optional article grouping used in the Blog listing and schema.">Category</FieldLabel><input className="blog-input" value={data.category} onChange={event => set('category', event.target.value)} /><FieldLabel blueprint={blueprint} field="tags" help="Optional comma-separated topical labels.">Tags</FieldLabel><input className="blog-input" value={data.tags} onChange={event => set('tags', event.target.value)} placeholder="MBA, admissions, online learning" /><FieldLabel blueprint={blueprint} field="published_date" help="Used for article metadata and structured data.">Publish date</FieldLabel><input className="blog-input" type="date" value={data.published_date} onChange={event => set('published_date', event.target.value)} />
        </CollapsibleSection>

        <CollapsibleSection id="cta" title="Optional call to action" description="Use only when the article needs a specific next step." badge={<OwnershipBadge source="MANUAL" />}>
          <FieldLabel blueprint={blueprint} field="cta_title" help="A short heading for the article CTA block.">CTA heading</FieldLabel><input className="blog-input" value={data.cta_title} onChange={event => set('cta_title', event.target.value)} /><FieldLabel blueprint={blueprint} field="cta_description" help="Optional supporting context for the CTA.">CTA description</FieldLabel><textarea className="blog-input" rows={3} value={data.cta_description} onChange={event => set('cta_description', event.target.value)} /><FieldLabel blueprint={blueprint} field="cta_label" help="The button label. It links to the generated workspace contact page.">Button label</FieldLabel><input className="blog-input" value={data.cta_label} onChange={event => set('cta_label', event.target.value)} />
        </CollapsibleSection>
      </aside>
    </div>
    <footer className="blog-editor-actions"><button type="button" className="btn btn-secondary" onClick={onBack}>Back</button><button type="button" className="btn btn-primary" onClick={submit} disabled={submitting || loading}>{submitting || loading ? 'Generating preview…' : 'Generate preview'}</button></footer>
  </div>;
}
