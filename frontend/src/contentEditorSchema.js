const FIELD_PRESENTATION = {
  university_name: { label: 'University Name', placeholder: 'Enter the university name' },
  university_full_name: { label: 'Full University Name', placeholder: 'Enter the full official name' },
  program_name: { label: 'Course Name', placeholder: 'Enter the course name' },
  spec_name: { label: 'Specialization Name', placeholder: 'Enter the specialization name' },
  hero_description: { label: 'Hero Description', type: 'textarea', placeholder: 'Enter a concise introduction for the hero section' },
  established_year: { label: 'Established Year', placeholder: 'Enter the year the university was established' },
  naac_grade: { label: 'NAAC Grade', placeholder: 'Enter the current NAAC grade' },
  ugc_approved: { label: 'UGC Approval', placeholder: 'Enter the UGC approval status' },
  ugc_status: { label: 'UGC Status', placeholder: 'Enter the UGC status' },
  mode_of_learning: { label: 'Learning Mode', placeholder: 'Enter the learning mode' },
  mode: { label: 'Learning Mode', placeholder: 'Enter the learning mode' },
  duration: { label: 'Duration', placeholder: 'Enter the course duration' },
  total_fee: { label: 'Total Fee', placeholder: 'Enter the total fee' },
  num_specializations: { label: 'Number of Specializations', placeholder: 'Enter the number of specializations' },
  about_content: { label: 'About Content', type: 'textarea', placeholder: 'Write the full About section content' },
  why_choose_content: { label: 'Why Choose This University', type: 'textarea', placeholder: 'Explain why students should choose this university' },
  admission_steps: { label: 'Admission Process', type: 'textarea', placeholder: 'Describe the admission process and its steps' },
  admission_fee_note: { label: 'Admission Fee Note', type: 'textarea', placeholder: 'Add any admission fee note' },
  eligibility_content: { label: 'Eligibility Criteria', type: 'textarea', placeholder: 'Describe who is eligible for this course' },
  syllabus_content: { label: 'Syllabus', type: 'textarea', placeholder: 'Enter the curriculum or syllabus content' },
  placement_content: { label: 'Placement Support', type: 'textarea', placeholder: 'Describe placement and career support' },
  certificate_description: { label: 'Certificate Description', type: 'textarea', placeholder: 'Describe the certificate awarded on completion' },
  emi_content: { label: 'EMI Information', type: 'textarea', placeholder: 'Describe EMI and financing options' },
  emi_amount: { label: 'EMI Amount', placeholder: 'Enter the EMI amount' },
  exam_content: { label: 'Examination Process', type: 'textarea', placeholder: 'Describe how examinations are conducted' },
  validity: { label: 'Degree Validity', type: 'textarea', placeholder: 'Describe the validity or recognition of the degree' },
  hero_image_alt: { label: 'Hero Image Alt Text', placeholder: 'Describe the hero image for accessibility' },
};

export const REPEATER_PRESENTATION = {
  reviews: {
    label: 'Student Reviews', itemLabel: 'Review', addLabel: 'Add Review',
    fields: [
      { key: 'reviewer_name', label: 'Reviewer Name', placeholder: 'Enter the reviewer name' },
      { key: 'reviewer_role', label: 'Role', placeholder: 'Enter the course, role, or profession' },
      { key: 'review_text', label: 'Review Text', type: 'textarea', placeholder: 'Enter the student review' },
    ],
  },
  faqs: {
    label: 'Frequently Asked Questions', itemLabel: 'FAQ', addLabel: 'Add FAQ',
    fields: [
      { key: 'question', label: 'Question', placeholder: 'Enter the question' },
      { key: 'answer', label: 'Answer', type: 'textarea', placeholder: 'Enter the answer' },
    ],
  },
  facts: {
    label: 'University Facts', itemLabel: 'Fact', addLabel: 'Add Fact',
    fields: [
      { key: 'fact_title', label: 'Title', placeholder: 'Enter the fact title' },
      { key: 'fact_description', label: 'Description', type: 'textarea', placeholder: 'Add supporting detail' },
    ],
  },
  highlights: {
    label: 'Highlights', itemLabel: 'Highlight', addLabel: 'Add Highlight',
    fields: [
      { key: 'highlight_title', label: 'Title', placeholder: 'Enter the highlight' },
      { key: 'highlight_description', label: 'Description', type: 'textarea', placeholder: 'Add supporting detail' },
    ],
  },
  fee_plans: {
    label: 'Fee Plans', itemLabel: 'Fee Plan', addLabel: 'Add Fee Plan',
    fields: [
      { key: 'plan_name', label: 'Title', placeholder: 'Enter the fee plan title' },
      { key: 'plan_amount', label: 'Amount', placeholder: 'Enter the amount' },
      { key: 'plan_total', label: 'Description or Total', placeholder: 'Enter a description or total' },
    ],
  },
  job_profiles: {
    label: 'Career Options', itemLabel: 'Career Option', addLabel: 'Add Career Option',
    fields: [
      { key: 'job_title', label: 'Job Title', placeholder: 'Enter the job title' },
      { key: 'avg_salary', label: 'Average Salary', placeholder: 'Enter the average salary, if provided' },
    ],
  },
  accreditations: {
    label: 'Other Approvals', itemLabel: 'Approval', addLabel: 'Add Approval',
    fields: [
      { key: 'body_name', label: 'Accrediting Body', placeholder: 'Enter the organization name' },
      { key: 'body_descriptor', label: 'Approval or Grade', placeholder: 'Enter the approval or grade' },
      { key: 'body_detail', label: 'Details', type: 'textarea', placeholder: 'Add supporting details' },
    ],
  },
  programs_table: {
    label: 'Programs', itemLabel: 'Program', addLabel: 'Add Program',
    fields: [
      { key: 'program_name', label: 'Program Name', placeholder: 'Enter the program name' },
      { key: 'program_fee', label: 'Fee', placeholder: 'Enter the program fee' },
      { key: 'program_eligibility', label: 'Eligibility', type: 'textarea', placeholder: 'Enter the eligibility criteria' },
    ],
  },
  features: {
    label: 'Feature Cards', itemLabel: 'Feature', addLabel: 'Add Feature',
    fields: [
      { key: 'stat', label: 'Statistic', placeholder: 'Enter a statistic, if provided' },
      { key: 't', label: 'Title', placeholder: 'Enter the feature title' },
      { key: 'd', label: 'Description', type: 'textarea', placeholder: 'Describe the feature' },
    ],
  },
  financing: {
    label: 'Financing Options', itemLabel: 'Financing Option', addLabel: 'Add Financing Option',
    fields: [
      { key: 'stat', label: 'Amount or Term', placeholder: 'Enter the amount or term' },
      { key: 't', label: 'Title', placeholder: 'Enter the option title' },
      { key: 'd', label: 'Description', type: 'textarea', placeholder: 'Describe the financing option' },
    ],
  },
  recruiters: {
    label: 'Recruiters', itemLabel: 'Recruiter', addLabel: 'Add Recruiter', scalar: true,
    fields: [{ key: 'value', label: 'Name', placeholder: 'Enter the recruiter name' }],
  },
  banks: {
    label: 'Financing Partners', itemLabel: 'Partner', addLabel: 'Add Partner', scalar: true,
    fields: [{ key: 'value', label: 'Name', placeholder: 'Enter the bank or financing partner' }],
  },
};

export const FIELD_SECTION_PREFERENCE = {
  university: {
    naac_grade: 'accreditation_strip',
    ugc_approved: 'accreditation_strip',
  },
  course: {
    hero_description: 'hero',
    duration: 'stats',
    mode: 'stats',
    naac_grade: 'accreditations',
    ugc_status: 'accreditations',
    total_fee: 'fees',
    num_specializations: 'stats',
  },
  specialization: {
    duration: 'stats',
    mode: 'stats',
    naac_grade: 'stats',
    ugc_status: 'stats',
    total_fee: 'fees',
  },
};

export const SECTION_HELP = {
  hero: 'The first content visitors see on the page.',
  stats: 'Key facts shown near the top of the page.',
  about: 'The full introduction for readers who want more detail.',
  accreditation_strip: 'Recognition displayed below the hero.',
  accreditations: 'Approvals and recognition for this program.',
  programs: 'Programs available in this workspace.',
  specializations: 'Specialization pages linked to this course.',
  why_choose: 'Reasons students may choose this university.',
  highlights: 'The most important benefits and features.',
  admission: 'The steps a student follows to apply.',
  eligibility: 'Who can apply for this program.',
  fees: 'Course fees, instalments, and EMI information.',
  fees_financing: 'Fees, EMI, and financing information.',
  syllabus: 'Curriculum and subjects covered by the program.',
  exam: 'How examinations and assessments work.',
  placement: 'Placement support and certificate information.',
  jobs: 'Career paths available after completion.',
  recruiters: 'Organizations associated with placement outcomes.',
  reviews: 'Feedback from students and graduates.',
  testimonials: 'Feedback from students and graduates.',
  faqs: 'Common questions and their answers.',
  blog_preview: 'Automatically populated from published blogs in this workspace.',
  other_specs: 'Related specializations linked by the workspace.',
};

// These labels affect only the editor navigation. The Blueprint still owns the
// page's sections, order, and fields; this groups them in the vocabulary a
// writer uses when moving through a page.
export const SECTION_NAVIGATION_GROUPS = {
  Content: ['hero', 'about', 'why_choose', 'highlights'],
  Academics: ['stats', 'programs', 'specializations', 'other_specs', 'eligibility', 'fees', 'fees_financing', 'admission', 'syllabus', 'exam'],
  Trust: ['accreditation_strip', 'accreditations', 'placement', 'jobs', 'recruiters', 'reviews', 'testimonials', 'faqs'],
  Media: ['images'],
  System: ['blog_preview'],
};

export function getFieldPresentation(name) {
  return FIELD_PRESENTATION[name] || {
    label: name.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase()),
    placeholder: 'Enter content',
  };
}
