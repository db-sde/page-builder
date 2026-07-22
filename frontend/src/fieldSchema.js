// Source of truth — what each page type needs.
// Each entry: key (ACF field name), label (human), required, section (page area), impact (if missing)
export const FIELD_SCHEMA = {
  course: [
    { key: '_meta', label: 'Publisher Metadata', required: false, section: 'Tracking', impact: 'Publisher provenance will be unavailable' },
    { key: 'program_name', label: 'Program Name', required: true, section: 'Hero', impact: 'Page title will be empty' },
    { key: 'university_name', label: 'University Name', required: true, section: 'Relationship', impact: 'University context cannot be resolved' },
    { key: 'linked_university', label: 'Linked University', required: false, section: 'Relationship', impact: 'Selected workspace will be used' },
    { key: 'hero_description', label: 'Hero Description', required: false, section: 'Hero', impact: 'Hero subtitle will be hidden' },
    { key: 'duration', label: 'Duration', required: false, section: 'Hero + Stats', impact: 'Duration will be hidden' },
    { key: 'mode', label: 'Mode of Learning', required: false, section: 'Hero + Stats', impact: 'Defaults to 100% Online' },
    { key: 'naac_grade', label: 'NAAC Grade', required: false, section: 'Accreditations', impact: 'NAAC badge will be hidden' },
    { key: 'ugc_status', label: 'UGC Status', required: false, section: 'Accreditations', impact: 'UGC badge will be hidden' },
    { key: 'total_fee', label: 'Total Fee', required: false, section: 'Fees', impact: 'Fee stats will be hidden' },
    { key: 'num_specializations', label: 'Number of Specializations', required: false, section: 'Stats', impact: 'Specialization count will be hidden' },
    { key: 'about_heading', label: 'About Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'highlights_heading', label: 'Highlights Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'accreditations_heading', label: 'Accreditations Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'specializations_heading', label: 'Specializations Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'fee_heading', label: 'Fee Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'eligibility_heading', label: 'Eligibility Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'admission_heading', label: 'Admission Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'syllabus_heading', label: 'Syllabus Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'placement_heading', label: 'Placement Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'jobs_heading', label: 'Jobs Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'faqs_heading', label: 'FAQs Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'about_content', label: 'About Content', required: false, section: 'About', impact: 'About section will be hidden' },
    { key: 'specializations_intro', label: 'Specializations Intro', required: false, section: 'Specializations', impact: 'Intro text will be hidden' },
    { key: 'eligibility_content', label: 'Eligibility Content', required: false, section: 'Eligibility', impact: 'Eligibility summary will be used when available' },
    { key: 'admission_steps', label: 'Admission Steps', required: false, section: 'Admission', impact: 'Admission section will be hidden' },
    { key: 'admission_fee_note', label: 'Admission Fee Note', required: false, section: 'Admission', impact: 'Fee note will be hidden' },
    { key: 'syllabus_content', label: 'Syllabus Content', required: false, section: 'Syllabus', impact: 'Syllabus section will be hidden' },
    { key: 'placement_content', label: 'Placement Content', required: false, section: 'Placement', impact: 'Placement section may be hidden' },
    { key: 'certificate_description', label: 'Certificate Description', required: false, section: 'Placement', impact: 'Certificate detail will be hidden' },
    { key: 'validity', label: 'Degree Validity', required: false, section: 'Placement', impact: 'Validity note will be hidden' },
    { key: 'emi_amount', label: 'EMI Amount', required: false, section: 'Fees', impact: 'EMI note will be hidden' },
    { key: 'highlights', label: 'Highlights', required: false, section: 'Repeater', impact: 'Highlights section will be hidden' },
    { key: 'fee_plans', label: 'Fee Plans', required: false, section: 'Repeater', impact: 'A plan may be inferred from total fee' },
    { key: 'job_profiles', label: 'Job Profiles', required: false, section: 'Repeater', impact: 'Jobs section will be hidden' },
    { key: 'reviews', label: 'Reviews', required: false, section: 'Repeater', impact: 'Reviews section will be hidden' },
    { key: 'faqs', label: 'FAQs', required: false, section: 'Repeater', impact: 'FAQ section will be hidden' },
    { key: 'seo_title', label: 'SEO Title', required: false, section: 'SEO', impact: 'Generated title fallback will be used' },
    { key: 'meta_description', label: 'Meta Description', required: false, section: 'SEO', impact: 'Description may be empty' },
    { key: 'starting_fee', label: 'Starting Fee', required: false, section: 'Listings', impact: 'Starting fee will be hidden from listings' },
    { key: 'eligibility_summary', label: 'Eligibility Summary', required: false, section: 'Eligibility + Listings', impact: 'Summary will be hidden' },
    { key: 'hero_image_url', label: 'Hero Image', required: true, section: 'User Asset', impact: 'A custom hero image must be supplied' },
    { key: 'certificate_image_url', label: 'Certificate Image', required: false, section: 'User Asset', impact: 'Certificate placeholder will be shown' },
    { key: 'course_name', label: 'Course Name (legacy alias)', required: false, section: 'Backward Compatibility', impact: 'program_name is preferred' },
  ],

  specialization: [
    { key: '_meta', label: 'Publisher Metadata', required: false, section: 'Tracking', impact: 'Publisher provenance will be unavailable' },
    { key: 'spec_name', label: 'Specialization Name', required: true, section: 'Hero', impact: 'Page title will be empty' },
    { key: 'university_name', label: 'University Name', required: true, section: 'Relationship', impact: 'University context cannot be resolved' },
    { key: 'linked_university', label: 'Linked University', required: false, section: 'Relationship', impact: 'Selected workspace will be used' },
    { key: 'linked_course', label: 'Linked Course', required: false, section: 'Relationship', impact: 'Parent assignment panel must resolve it' },
    { key: 'hero_description', label: 'Hero Description', required: false, section: 'Hero', impact: 'Hero subtitle will be hidden' },
    { key: 'duration', label: 'Duration', required: false, section: 'Hero + Stats', impact: 'Duration will be hidden' },
    { key: 'mode', label: 'Mode of Learning', required: false, section: 'Hero + Stats', impact: 'Defaults to 100% Online' },
    { key: 'naac_grade', label: 'NAAC Grade', required: false, section: 'Accreditations', impact: 'NAAC stat will be hidden' },
    { key: 'ugc_status', label: 'UGC Status', required: false, section: 'Accreditations', impact: 'UGC stat will be hidden' },
    { key: 'total_fee', label: 'Total Fee', required: false, section: 'Fees', impact: 'Fee stats will be hidden' },
    { key: 'about_heading', label: 'About Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'highlights_heading', label: 'Highlights Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'eligibility_heading', label: 'Eligibility Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'fee_heading', label: 'Fee Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'other_specs_heading', label: 'Other Specializations Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'syllabus_heading', label: 'Syllabus Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'exam_heading', label: 'Exam Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'admission_heading', label: 'Admission Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'placement_heading', label: 'Placement Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'jobs_heading', label: 'Jobs Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'certificate_heading', label: 'Certificate Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'faqs_heading', label: 'FAQs Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'about_content', label: 'About Content', required: false, section: 'About', impact: 'About section will be hidden' },
    { key: 'eligibility_content', label: 'Eligibility Content', required: false, section: 'Eligibility', impact: 'Eligibility summary will be used when available' },
    { key: 'syllabus_content', label: 'Syllabus Content', required: false, section: 'Syllabus', impact: 'Syllabus section will be hidden' },
    { key: 'exam_content', label: 'Exam Content', required: false, section: 'Exam', impact: 'Exam section will be hidden' },
    { key: 'admission_steps', label: 'Admission Steps', required: false, section: 'Admission', impact: 'Admission section will be hidden' },
    { key: 'admission_fee_note', label: 'Admission Fee Note', required: false, section: 'Admission', impact: 'Fee note will be hidden' },
    { key: 'placement_content', label: 'Placement Content', required: false, section: 'Placement', impact: 'Placement section may be hidden' },
    { key: 'certificate_description', label: 'Certificate Description', required: false, section: 'Certificate', impact: 'Certificate section may be hidden' },
    { key: 'emi_amount', label: 'EMI Amount', required: false, section: 'Fees', impact: 'EMI note will be hidden' },
    { key: 'highlights', label: 'Highlights', required: false, section: 'Repeater', impact: 'Highlights section will be hidden' },
    { key: 'other_specs', label: 'Other Specializations', required: false, section: 'Repeater', impact: 'Related specializations will come from workspace when available' },
    { key: 'job_profiles', label: 'Job Profiles', required: false, section: 'Repeater', impact: 'Jobs section will be hidden' },
    { key: 'reviews', label: 'Reviews', required: false, section: 'Repeater', impact: 'Reviews section will be hidden' },
    { key: 'faqs', label: 'FAQs', required: false, section: 'Repeater', impact: 'FAQ section will be hidden' },
    { key: 'seo_title', label: 'SEO Title', required: false, section: 'SEO', impact: 'Generated title fallback will be used' },
    { key: 'meta_description', label: 'Meta Description', required: false, section: 'SEO', impact: 'Description may be empty' },
    { key: 'eligibility_summary', label: 'Eligibility Summary', required: false, section: 'Eligibility', impact: 'Summary will be hidden' },
    { key: 'hero_image_url', label: 'Hero Image', required: true, section: 'User Asset', impact: 'A custom hero image must be supplied' },
  ],

  university: [
    { key: '_meta', label: 'Publisher Metadata', required: false, section: 'Tracking', impact: 'Publisher provenance will be unavailable' },
    { key: 'university_name', label: 'University Name', required: true, section: 'Hero', impact: 'Page title will be empty' },
    { key: 'university_full_name', label: 'University Full Name', required: false, section: 'Hero', impact: 'Short university name will be used' },
    { key: 'hero_description', label: 'Hero Description', required: false, section: 'Hero', impact: 'Hero subtitle will be hidden' },
    { key: 'established_year', label: 'Established Year', required: false, section: 'Stats', impact: 'Established year will be hidden' },
    { key: 'naac_grade', label: 'NAAC Grade', required: false, section: 'Accreditations', impact: 'NAAC badge will be hidden' },
    { key: 'ugc_approved', label: 'UGC Approved Status', required: false, section: 'Accreditations', impact: 'UGC badge will be hidden' },
    { key: 'mode_of_learning', label: 'Mode of Learning', required: false, section: 'Hero', impact: 'Mode pill will be hidden' },
    { key: 'starting_fee', label: 'Starting Fee', required: false, section: 'Stats', impact: 'Starting fee will be hidden' },
    { key: 'num_programs', label: 'Number of Programs', required: false, section: 'Stats', impact: 'Program count will be hidden' },
    { key: 'about_heading', label: 'About Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'why_choose_heading', label: 'Why Choose Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'facts_heading', label: 'Facts Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'accreditations_heading', label: 'Accreditations Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'programs_heading', label: 'Programs Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'admission_heading', label: 'Admission Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'emi_heading', label: 'EMI Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'exam_heading', label: 'Exam Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'faculty_heading', label: 'Faculty Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'placement_heading', label: 'Placement Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'reviews_heading', label: 'Reviews Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'faqs_heading', label: 'FAQs Heading', required: false, section: 'Headings', impact: 'Default heading will be used' },
    { key: 'about_content', label: 'About Content', required: false, section: 'About', impact: 'About section will be hidden' },
    { key: 'why_choose_content', label: 'Why Choose Content', required: false, section: 'Why Choose', impact: 'Why Choose section will be hidden' },
    { key: 'admission_steps', label: 'Admission Steps', required: false, section: 'Admission', impact: 'Admission section will be hidden' },
    { key: 'admission_fee_note', label: 'Admission Fee Note', required: false, section: 'Admission', impact: 'Fee note will be hidden' },
    { key: 'emi_content', label: 'EMI Content', required: false, section: 'EMI', impact: 'EMI section will be hidden' },
    { key: 'exam_content', label: 'Exam Content', required: false, section: 'Exam', impact: 'Exam section will be hidden' },
    { key: 'faculty_intro', label: 'Faculty Intro', required: false, section: 'Faculty', impact: 'Faculty intro will be hidden' },
    { key: 'placement_content', label: 'Placement Content', required: false, section: 'Placement', impact: 'Placement section will be hidden' },
    { key: 'facts', label: 'Facts', required: false, section: 'Repeater', impact: 'Facts section will be hidden' },
    { key: 'accreditations', label: 'Accreditations', required: false, section: 'Repeater', impact: 'Accreditations section will be hidden' },
    { key: 'programs_table', label: 'Programs Table', required: false, section: 'Repeater', impact: 'Workspace courses will be used when available' },
    { key: 'faculty_members', label: 'Faculty Members', required: false, section: 'Repeater', impact: 'Faculty section will be hidden' },
    { key: 'reviews', label: 'Reviews', required: false, section: 'Repeater', impact: 'Reviews section will be hidden' },
    { key: 'faqs', label: 'FAQs', required: false, section: 'Repeater', impact: 'FAQ section will be hidden' },
    { key: 'seo_title', label: 'SEO Title', required: false, section: 'SEO', impact: 'Generated title fallback will be used' },
    { key: 'meta_description', label: 'Meta Description', required: false, section: 'SEO', impact: 'Description may be empty' },
    { key: 'programs_intro', label: 'Programs Intro', required: false, section: 'Programs', impact: 'Programs intro will be hidden' },
    { key: 'hero_image_url', label: 'Hero Image', required: true, section: 'User Asset', impact: 'A custom hero image must be supplied' },
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
