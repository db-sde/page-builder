// Source of truth — what each page type needs.
// Each entry: key (ACF field name), label (human), required, section (page area), impact (if missing)
export const FIELD_SCHEMA = {
  course: [
    // Required
    { key: 'program_name',        label: 'Program Name',               required: true,  section: 'Hero',                impact: 'Page title will be empty' },
    { key: 'hero_description',    label: 'Hero Description',            required: true,  section: 'Hero',                impact: 'Hero subtitle will be empty' },
    { key: 'duration',            label: 'Duration',                    required: true,  section: 'Hero + Stats',        impact: 'Missing from hero pills and stats strip' },
    { key: 'mode',                label: 'Mode of Learning',            required: false, section: 'Hero + Stats',        impact: 'Defaults to "100% Online" if missing' },
    { key: 'total_fee',           label: 'Total Fee',                   required: true,  section: 'Stats + Sticky Bar',  impact: 'Fee will show blank in stats and sticky bar' },
    { key: 'naac_grade',          label: 'NAAC Grade',                  required: true,  section: 'Hero Badge + Stats',  impact: 'Accreditation badge will be empty' },
    { key: 'ugc_status',          label: 'UGC Status',                  required: true,  section: 'Hero Badge + Stats',  impact: 'UGC label will be empty' },
    { key: 'hero_image_url',      label: 'Hero Image',                  required: true,  section: 'Hero',                impact: 'Hero image will be empty/placeholder' },
    { key: 'certificate_image_url', label: 'Certificate Image',         required: true,  section: 'Placement',           impact: 'Certificate image will be empty/placeholder' },
    // Optional
    { key: 'seo_title',           label: 'SEO Title',                   required: false, section: 'Page Head',           impact: 'Browser tab title will be empty' },
    { key: 'meta_description',    label: 'Meta Description',            required: false, section: 'Page Head',           impact: 'Search snippet will be empty' },
    { key: 'about_content',       label: 'About Content',               required: false, section: 'About Section',       impact: 'About section will be hidden' },
    { key: 'eligibility_content', label: 'Eligibility',                 required: false, section: 'Eligibility Section', impact: 'Eligibility section will be hidden' },
    { key: 'admission_steps',     label: 'Admission Steps',             required: false, section: 'Admission Section',   impact: 'Admission section will be hidden' },
    { key: 'syllabus_content',    label: 'Syllabus',                    required: false, section: 'Syllabus Section',    impact: 'Syllabus section will be hidden' },
    { key: 'placement_content',   label: 'Placement Info',              required: false, section: 'Placement Section',   impact: 'Placement section will be hidden' },
    { key: 'emi_amount',          label: 'EMI Amount',                  required: false, section: 'Sticky Bar + Fees',   impact: 'EMI text will be missing from fee note' },
    { key: 'num_specializations', label: 'Number of Specializations',   required: false, section: 'Stats Strip',         impact: 'Specializations count missing from stats' },
    { key: 'course_name',         label: 'Course Name (alias for program_name)', required: false, section: 'Hero', impact: 'Used as fallback for program_name if that field is missing' },
  ],

  specialization: [
    { key: 'spec_name',               label: 'Specialization Name',     required: true,  section: 'Hero',                impact: 'Page title will be empty' },
    { key: 'hero_description',        label: 'Hero Description',        required: true,  section: 'Hero',                impact: 'Hero subtitle will be empty' },
    { key: 'duration',                label: 'Duration',                required: true,  section: 'Hero + Stats',        impact: 'Missing from hero pills and stats strip' },
    { key: 'mode',                    label: 'Mode of Learning',        required: false, section: 'Hero + Stats',        impact: 'Defaults to "100% Online" if missing' },
    { key: 'total_fee',               label: 'Total Fee',               required: true,  section: 'Stats + Sticky Bar',  impact: 'Fee will show blank' },
    { key: 'naac_grade',              label: 'NAAC Grade',              required: true,  section: 'Stats',               impact: 'Accreditation missing from stats' },
    { key: 'ugc_status',              label: 'UGC Status',              required: true,  section: 'Stats',               impact: 'UGC label missing from stats' },
    { key: 'hero_image_url',          label: 'Hero Image',              required: true,  section: 'Hero',                impact: 'Hero image will be empty/placeholder' },
    // Optional
    { key: 'seo_title',               label: 'SEO Title',               required: false, section: 'Page Head',           impact: 'Browser tab title will be empty' },
    { key: 'meta_description',        label: 'Meta Description',        required: false, section: 'Page Head',           impact: 'Search snippet will be empty' },
    { key: 'about_content',           label: 'About Content',           required: false, section: 'About Section',       impact: 'About section will be hidden' },
    { key: 'eligibility_content',     label: 'Eligibility',             required: false, section: 'Eligibility Section', impact: 'Eligibility section will be hidden' },
    { key: 'admission_steps',         label: 'Admission Steps',         required: false, section: 'Admission Section',   impact: 'Admission section will be hidden' },
    { key: 'syllabus_content',        label: 'Syllabus',                required: false, section: 'Syllabus Section',    impact: 'Syllabus section will be hidden' },
    { key: 'exam_content',            label: 'Exam Process',            required: false, section: 'Exam Section',        impact: 'Exam section will be hidden' },
    { key: 'placement_content',       label: 'Placement Info',          required: false, section: 'Placement Section',   impact: 'Placement section will be hidden' },
    { key: 'certificate_description', label: 'Certificate Description', required: false, section: 'Placement Section',   impact: 'Certificate detail will be hidden' },
    { key: 'emi_amount',              label: 'EMI Amount',              required: false, section: 'Sticky Bar',          impact: 'EMI text missing from sticky bar' },
  ],

  university: [
    { key: 'university_name',     label: 'University Name',             required: true,  section: 'Hero',                impact: 'Page title will be empty' },
    { key: 'hero_description',    label: 'Hero Description',            required: true,  section: 'Hero',                impact: 'Hero subtitle will be empty' },
    { key: 'naac_grade',          label: 'NAAC Grade',                  required: true,  section: 'Hero Badge + Stats',  impact: 'Accreditation badge will be empty' },
    { key: 'ugc_approved',        label: 'UGC Approved Status',         required: true,  section: 'Stats',               impact: 'UGC label missing from stats' },
    { key: 'hero_image_url',      label: 'Hero Image',                  required: true,  section: 'Hero',                impact: 'Hero image will be empty/placeholder' },
    // Optional
    { key: 'seo_title',           label: 'SEO Title',                   required: false, section: 'Page Head',           impact: 'Browser tab title will be empty' },
    { key: 'meta_description',    label: 'Meta Description',            required: false, section: 'Page Head',           impact: 'Search snippet will be empty' },
    { key: 'established_year',    label: 'Established Year',            required: false, section: 'Stats Strip',         impact: 'Est. year missing from stats' },
    { key: 'starting_fee',        label: 'Starting Fee',                required: false, section: 'Stats Strip',         impact: 'Starting fee missing from stats' },
    { key: 'num_programs',        label: 'Number of Programs',          required: false, section: 'Stats Strip',         impact: 'Program count missing from stats' },
    { key: 'about_content',       label: 'About Content',               required: false, section: 'About Section',       impact: 'About section will be hidden' },
    { key: 'why_choose_content',  label: 'Why Choose Content',          required: false, section: 'Why Choose Section',  impact: 'Why Choose section will be hidden' },
    { key: 'admission_steps',     label: 'Admission Steps',             required: false, section: 'Admission Section',   impact: 'Admission section will be hidden' },
    { key: 'emi_content',         label: 'EMI Content',                 required: false, section: 'EMI Section',         impact: 'EMI section will be hidden' },
    { key: 'exam_content',        label: 'Exam Process',                required: false, section: 'Exam Section',        impact: 'Exam section will be hidden' },
    { key: 'placement_content',   label: 'Placement Info',              required: false, section: 'Placement Section',   impact: 'Placement section will be hidden' },
  ],

  blog: [
    { key: 'title',            label: 'Blog Title',          required: true,  section: 'Header',         impact: 'Title of the blog post will be empty' },
    { key: 'excerpt',          label: 'Excerpt / Subtitle',  required: true,  section: 'Header',         impact: 'Subtitle or introduction will be empty' },
    { key: 'hero_image_url',   label: 'Article Hero Image',  required: true,  section: 'Header',         impact: 'Article hero image will be empty/placeholder' },
    { key: 'content_html',     label: 'Article Body HTML',   required: true,  section: 'Body',           impact: 'The main article body will be empty' },
    { key: 'tag',              label: 'Category Tag',        required: false, section: 'Metadata',       impact: 'Defaults to "Career" if missing' },
    { key: 'author',           label: 'Author Name',         required: false, section: 'Metadata',       impact: 'Defaults to "Krishna Porwal" if missing' },
    { key: 'author_role',      label: 'Author Role',         required: false, section: 'Metadata',       impact: 'Defaults to "content writer" if missing' },
    { key: 'read_time',        label: 'Reading Time',        required: false, section: 'Metadata',       impact: 'Will be calculated from word count' },
    { key: 'date',             label: 'Published Date',      required: false, section: 'Metadata',       impact: 'Defaults to current date' },
  ],
};

const PLACEHOLDER_STRINGS = [
  'na', 'n/a', 'not available', 'not applicable', 'null', 'none', 'unknown',
  '-', '--', '---', '--------------', '—'
];

export function isPlaceholder(val) {
  if (val === undefined || val === null) return true;
  if (typeof val !== 'string') return false;
  const s = val.trim().toLowerCase();
  if (PLACEHOLDER_STRINGS.includes(s)) return true;
  if (/^[-—]+$/.test(val.trim())) return true;
  return false;
}

/**
 * Diff ACF data against schema for a page type.
 * Returns { present, missing, requiredMissing, schema }
 */
export function diffFields(acf_data, page_type) {
  const schema = FIELD_SCHEMA[page_type] || [];
  const present = [];
  const missing = [];
  const requiredMissing = [];

  for (const field of schema) {
    const val = acf_data[field.key];
    const isEmpty =
      val === undefined ||
      val === null ||
      val === '' ||
      (Array.isArray(val) && val.length === 0) ||
      (typeof val === 'string' && val.trim() === '') ||
      isPlaceholder(val);

    if (isEmpty) {
      missing.push(field);
      if (field.required) requiredMissing.push(field);
    } else {
      present.push(field);
    }
  }

  return { present, missing, requiredMissing, schema };
}
