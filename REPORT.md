# DegreeBaba Workspace System - Full Forensic Audit Report

---

## SECTION 1 — Project Overview

### 1.1 Current System Architecture
The DegreeBaba system operates as a static website generator and compiler. It compiles page definitions represented as ACF JSON configurations (`source.json` files) into rich, responsive static HTML pages. It does this by combining a server-side Python compilation phase with a client-side React-based template mounting stage.

### 1.2 Data and Render Pipeline
The progression of content through the system is structured as follows:

```text
DOCX (Input)
  │
  ▼ [API: POST /parse-docx]
JSON (Raw ACF JSON)
  │
  ▼ [Transformer Layer: Class transforms fields to schema]
Transformer Context
  │
  ▼ [Compiler Layer: Pass 1-3 builds index and resolves relations]
Jinja2 HTML Page (Jinja renders static base, templates remain deferred)
  │
  ▼ [Builder Layer: Pass 4 rewrites links and structures build/]
Static Output Folder (Clean routes, routes.json sitemap, assets)
  │
  ▼ [Browser Runtime: support.js mounts React components]
Rendered DOM (Variables evaluated, directives compiled)
```

### 1.3 Exact Files Involved

#### 1. Ingestion and Parsing
- **`backend/main.py`**: Exposes the APIs for parsing (`/parse-docx`), saving (`/save-to-workspace`), compiling (`/compile-workspace`), building (`/build-website`), and serving preview files (`/build-file`).
- **`process_jamia_e2e.py`**: Batch processing CLI utility.

#### 2. Transformer Layer
- **`backend/core/router.py`**: Router selecting correct transformer class based on page type.
- **`backend/transformers/base.py`**: Common abstract transformer logic.
- **`backend/transformers/university.py`**: University-level data transformer.
- **`backend/transformers/course.py`**: Course-level data transformer.
- **`backend/transformers/specialization.py`**: Specialization-level data transformer.
- **`backend/transformers/blog.py`**: Blog article data transformer.
- **`backend/transformers/programs_listing.py`**: Programs directory listing transformer.
- **`backend/transformers/specializations_listing.py`**: Specialization directory listing transformer.
- **`backend/transformers/blog_listing.py`**: Blog list transformer.

#### 3. Compiler & Template Engine
- **`backend/workspace/compiler.py`**: Orchestrates two-pass compilation of the workspace database.
- **`backend/renderer/engine.py`**: Jinja2 wrapper. Sets up custom filters, serializes data structures into JSON for components, and renders pages.
- **`backend/templates/`**:
  - `university.html`, `course.html`, `specialization.html`, `blog.html`, `programs_listing.html`, `specializations_listing.html`, `blog_listing.html`.

#### 4. Website Builder
- **`backend/workspace/builder.py`**: Static website builder. Copies files, handles image/download assets copying, generates sitemaps and manifests, and executes link rewrites.

#### 5. Client-Side Runtime
- **`support.js`**: React UMD bootloader and web component virtual compiler (`dc-runtime`). Parses custom `<x-dc>` elements and components dynamically in the client's browser.

---

## SECTION 2 — Complete Workspace Audit

The workspace folder is stored under `backend/workspaces/`. Currently, only one workspace named `nodia` exists.

### 2.1 Workspace Directory Structure
The recursive file list of the `nodia` workspace is as follows:

```text
backend/workspaces/nodia/
├── metadata.json
├── Blogs/
│   └── untitled/
│       ├── blog.html
│       └── source.json
├── University/
│   ├── university.html
│   └── source.json
├── Specializations/
│   └── nodia-manipal-online-mba-in-human-resource-management/
│       ├── source.json
│       └── specialization.html
├── Pages/
│   ├── blog/
│   │   ├── blog_listing.html
│   │   └── source.json
│   ├── programs/
│   │   ├── programs_listing.html
│   │   └── source.json
│   └── specializations/
│       ├── specializations_listing.html
│       └── source.json
├── Assets/
│   ├── images/
│   │   ├── blog-untitled-hero.jpg
│   │   ├── nodia-manipal-online-mba-in-human-resource-management-hero.png
│   │   └── university-hero.jpg
│   └── downloads/
└── build/
    ├── index.html
    ├── sitemap.xml
    ├── routes.json
    ├── assets/
    │   ├── support.js
    │   └── images/
    │       ├── blog-untitled-hero.jpg
    │       ├── nodia-manipal-online-mba-in-human-resource-management-hero.png
    │       └── university-hero.jpg
    ├── programs/
    │   └── index.html
    ├── specializations/
    │   └── index.html
    ├── nodia-manipal-online-mba-in-human-resource-management/
    │   └── index.html
    └── blog/
        ├── index.html
        └── untitled/
            └── index.html
```

### 2.2 File and Folder Counts

- **Total Folder Count**: 21 (including nested subfolders)
- **Total File Count**: 26 (including source configs, compiled HTMLs, assets, and builds)

---

## SECTION 3 — Source JSON Audit

Below are the complete, unmodified JSON configurations of all workspace sources.

### 3.1 Workspace Global Metadata (`metadata.json`)
```json
{
  "university_slug": "nodia",
  "university_name": "Nodia",
  "established_year": "",
  "default_theme": {
    "primary_color": "#6B4FC9",
    "secondary_color": "#FF5C35",
    "background_color": "#F6F4FB"
  },
  "global_contact": {
    "phone": "",
    "email": "",
    "address": ""
  },
  "lead_url": "https://apply.degreebaba.com",
  "created_at": "2026-06-20T15:52:43.196173+00:00",
  "last_compiled_at": "2026-06-20T19:27:44.878306+00:00"
}
```

### 3.2 University Page Source (`University/source.json`)
```json
{
  "university_slug": "nodia",
  "page_type": "university",
  "slug": "noida-international",
  "parent_slug": null,
  "saved_at": "2026-06-20T15:52:56.343301+00:00",
  "data": {
    "_meta": {
      "document_title": "Copy of Noida International University Page.docx",
      "page_type": "university",
      "generated_by": "DegreeBaba Content Publisher"
    },
    "mode_of_learning": "Online and on-campus learning",
    "university_full_name": "Noida International University Online",
    "admission_fee_note": "Step 4. Fill out the application form with the required information and pay the application fee.",
    "facts": [
      {
        "fact_title": "Interdisciplinary Courses",
        "fact_description": "The NIU online focuses on interdisciplinary courses for the holistic development of students."
      },
      {
        "fact_title": "Equivalent Degree",
        "fact_description": "The Noida International University Online degree is equivalent to a traditional campus degree."
      },
      {
        "fact_title": "Practical Learning Approach",
        "fact_description": "To offer practical learning, the learning pedagogy includes real-world application-based assignments for well-rounded skill development."
      }
    ],
    "why_choose_content": "<h3>Noida International University Online Pros</h3><ul><li><strong>Global Collaborations:</strong> The Noida International University has global collaborations with several international universities in Malaysia, Georgia, Russia, Turkey, USA, Kazakhstan, Switzerland, Uzbekistan, and China.</li><li><strong>Best B-School:</strong> NIU has been awarded India's best B-school 2025 and rated AA+ by Careers360.</li></ul>",
    "emi_content": "<p>The NIU Online offers several financial aid options to assist students in acquiring an online professional degree without financial burden. However, the university also provides no-cost EMI directly, but students can seek third-party assistance from banking institutions or NBFCs for easy EMI, loan, or financing options.</p>\n<p>NIU Online also provides scholarships and loan assistance. The university has Propelld as an education loan partner. Some of the NIU Online scholarships available are:</p>\n<ul>\n<li>Regular Scholarship</li>\n<li>CUET Scholarship</li>\n</ul>",
    "faculty_intro": "Some of the faculty members of Noida International University Online are mentioned below, along with their assigned program and designation:",
    "exam_content": "<h3>Noida International University Online Examination Process</h3><p>NIU Online course examinations are conducted completely online. It provides students with the flexibility to appear for the examinations from the comfort of their homes, at their convenience, and at a preferred time schedule.</p><p>To appear for the Noida International University's Online examinations, students can select the date, slot time, and subject through the slot booking process at the university website.</p><p>The NIU Online student assessment is based on the term-end online examination and continuous internal evaluation, abbreviated as TEE and CIA.</p>",
    "admission_steps": "<p>Applicants who fulfill the eligibility criteria and admission requirements of their chosen NIU Online course must follow the step-by-step admission process below for an easy enrollment process at Noida International University Online.</p><ol><li><p>Visit the official NIU Online website.</p></li><li><p>Every applicant is given personalized online counselling, which helps them opt for the right online program.</p></li><li><p>Students are required to register online on the NIU Online admission portal to access My Account.</p></li><li><p>Fill out the application form with the required information and pay the application fee.</p></li><li><p>Upload supporting documents, and the university will verify them.</p></li><li><p>Once the application form and documents are verified, you are asked to pay the course fee.</p></li><li><p>Eligible candidates will receive access to My Account and LMS (Learning Management System) within 2 days of paying the program fee.</p></li></ol>",
    "faculty_members": [
      {
        "member_name": "Dr. Neha",
        "member_program": "NIU Online MBA",
        "member_designation": "Assistant Professor",
        "member_qualification": null
      },
      {
        "member_name": "Dr. Om Prakash",
        "member_program": "NIU Online MBA",
        "member_designation": "Associate Professor",
        "member_qualification": null
      },
      {
        "member_name": "Dr. Sadhana Sargam",
        "member_program": "NIU Online MBA",
        "member_designation": "Faculty Member",
        "member_qualification": null
      },
      {
        "member_name": "Keerthi Jain",
        "member_program": "NIU Online MBA",
        "member_designation": "Faculty Member",
        "member_qualification": null
      },
      {
        "member_name": "Dr. Swati Chaudhary",
        "member_program": "NIU Online MBA",
        "member_designation": "Faculty Member",
        "member_qualification": null
      }
    ],
    "hero_description": "Noida International University Online (NIU Online) provides an extensive range of undergraduate and postgraduate online programs, designed to fulfill the needs of students and working professionals who require flexibility without compromising education quality. With globally recognized degrees, industry-oriented syllabi, and a blend of live and recorded classes, NIU Online enables students to pursue higher education and develop their careers remotely. The university gives access to experienced faculty members, digital libraries, and placement opportunities, thus creating a complete and supportive learning environment.",
    "about_content": "<p>The Noida International University was established in 2010 under the U.P. LEGISLATURE ACT NO. 27 OF 2010. Later, it started offering full-fledged online learning courses under Noida International University Online, abbreviated as NIU Online. The university is globally recognized and considered to be one of the most renowned private universities in India, with students enrolled from 64+ nations.</p><p>With 14 years of excellence in academics, the university has established itself as a prominent institution in the field of higher education. The curriculum for every NIU online course is aligned with industry standards and delivered through a digital library, recorded lectures, and live sessions. Students can also opt for easy financing and convenient financing options.</p><p>Students enrolled at NIU online can study at their own pace without any physical on-campus requirement. The university provides a 24*7 comprehensive support that includes access to career counseling, technical help, and academic guidance. To build a successful career, enrolled students can avail themselves of networking opportunities that foster building connections with peers, faculty, and industry professionals.</p>",
    "accreditations": [
      {
        "body_name": "National Assessment and Accreditation Council",
        "body_descriptor": "NAAC",
        "body_detail": "A+ Grade"
      },
      {
        "body_name": "Association of Indian Universities",
        "body_descriptor": "AIU",
        "body_detail": "Member"
      },
      {
        "body_name": "Bar Council of India",
        "body_descriptor": "BCI",
        "body_detail": "Accredited"
      },
      {
        "body_name": "National Council for Teacher Education",
        "body_descriptor": "NCTE",
        "body_detail": "Accredited"
      },
      {
        "body_name": "University Grants Commission",
        "body_descriptor": "UGC",
        "body_detail": "Entitled"
      }
    ],
    "faqs": [
      {
        "question": "Can you do NIU online?",
        "answer": "Yes, if you qualify for the eligibility criteria of your preferred program offered by NIU online. You can definitely enroll at the university."
      },
      {
        "question": "Is NIU online UGC approved?",
        "answer": "Yes, NIU Online is approved by Section 2(f) of the UGC Act, 1956."
      },
      {
        "question": "Is NIU's online tuition free?",
        "answer": "No, students are required to pay the tuition fee for their enrolled program. However, the fee structure is cost-effective but not free."
      },
      {
        "question": "What are the fees for NIU online?",
        "answer": "The NIU online course fee depends on the chosen course and specialization. Meanwhile, the average NIU online fee for every course varies between INR 75,000 /- & INR 1,65,000 /- approx."
      },
      {
        "question": "What is the NIU online acceptance rate?",
        "answer": "NIU Online's acceptance rate is 100% as it accepts direct admission without any entrance exam or admission test."
      }
    ],
    "placement_content": "<p>NIU Online provides placement assistance to guide students in achieving their career goals and ambitions. The placement cell of the university remains active throughout the academic year and provides several benefits. Some of the major benefits of NIU online placement assistance are:</p><ul><li>Resume building.</li><li>Workshop.</li><li>Interview preparation.</li><li>Connection with top recruiters.</li></ul><p>The major NIU online recruiters include Wipro, Honda, Synergy, TCS, Cognizant, Bluelupin, etc.</p>",
    "programs_table": [
      {
        "program_name": "Online MBA",
        "program_fee": "INR 1,64,000 /- (complete course fee)",
        "program_eligibility": "A valid bachelor's degree in any stream from a recognized university. A minimum of 50% marks are essential at the graduation level."
      },
      {
        "program_name": "Online BBA",
        "program_fee": "INR 1,62,000 /- (complete course fee)",
        "program_eligibility": "10+2 educational qualification from a recognized education board."
      },
      {
        "program_name": "Online MSc",
        "program_fee": "INR 1,32,000 /- (complete course fee)",
        "program_eligibility": "A valid bachelor's degree with mathematics as a main subject from a recognized university."
      },
      {
        "program_name": "Online MA",
        "program_fee": "INR 1,16,000 /- (complete course fee)",
        "program_eligibility": "A valid bachelor's degree in any stream from a recognized university."
      },
      {
        "program_name": "Online MCA",
        "program_fee": "INR 1,12,000 /- (complete course fee)",
        "program_eligibility": "A valid bachelor's degree in any stream from a recognized university."
      },
      {
        "program_name": "Online BCA",
        "program_fee": "INR 1,11,000 /- (complete course fee)",
        "program_eligibility": "10+2 educational qualification from a recognized education board."
      },
      {
        "program_name": "Online MCom",
        "program_fee": "INR 82,000 /- (complete course fee)",
        "program_eligibility": "A valid bachelor's degree in any stream from a recognized university."
      },
      {
        "program_name": "Online BCom",
        "program_fee": "INR 75,000 /- (complete course fee)",
        "program_eligibility": "A valid bachelor's degree in any stream from a recognized university."
      }
    ],
    "reviews": [
      {
        "review_text": "At first when my friend suggested me about Noida International University Online. I wasn't sure about it but it turned out to be an amazing journey.",
        "reviewer_label": "Student"
      },
      {
        "review_text": "My and my cousin both completed our online MBA from Noida International University Online and we both got placement. Highly recommended to others.",
        "reviewer_label": "MBA Graduate"
      },
      {
        "review_text": "The faculty support and other assistance are up to the mark. It was an amazing journey with the university.",
        "reviewer_label": "Student"
      },
      {
        "review_text": "I am in my third sem, but as of now, there is nothing as such i disliked about the university. Rest, let's wait for the placements…. fingers crossed!",
        "reviewer_label": "MBA Student"
      }
    ],
    "established_year": "2010",
    "naac_grade": "A",
    "ugc_approved": "Entitled",
    "starting_fee": "INR 75,000 /-",
    "num_programs": "8+",
    "university_name": "Noida International",
    "stat_years": "2010",
    "seo_title": "NIU Online: Top Ranked University for Online Degrees",
    "meta_description": "Noida International University Online offers 8+ accredited online programs. Study flexibly with globally recognized degrees, expert faculty & placement support.",
    "programs_intro": "Explore 8+ undergraduate and postgraduate online programs designed for working professionals and students seeking flexible, quality education.",
    "about_heading": "About Noida International University Online",
    "why_choose_heading": "Noida International University Online Pros:",
    "facts_heading": "NIU Online Facts",
    "accreditations_heading": "NIU Online Details",
    "programs_heading": "NIU Online Courses",
    "admission_heading": "Noida International Online University Admission Process",
    "emi_heading": "Noida International University Online EMI details",
    "exam_heading": "Noida International University Online Examination Process",
    "faculty_heading": "Noida International University Online Faculty Members",
    "placement_heading": "Noida International University Online Placement Partners",
    "reviews_heading": "Noida International University Online Reviews",
    "faqs_heading": "Noida International University Online FAQs",
    "hero_image_url": "/assets/images/university-hero.jpg",
    "mode": "100% Online"
  }
}
```

### 3.3 Specialization Page Source (`Specializations/nodia-manipal-online-mba-in-human-resource-management/source.json`)
```json
{
  "university_slug": "nodia",
  "page_type": "specialization",
  "slug": "nodia-manipal-online-mba-in-human-resource-management",
  "parent_slug": "nodia-online-mba",
  "saved_at": "2026-06-20T16:56:07.357545+00:00",
  "data": {
    "_meta": {
      "document_title": "Copy of Manipal Online MBA in Human Resource Management.docx",
      "page_type": "specialization",
      "generated_by": "DegreeBaba Content Publisher"
    },
    "eligibility_content": "<p>Students and interested working professionals to enroll in an Online MBA program offered at Manipal Online University are required to fulfill the below-mentioned eligibility criteria and admission requirements of the program:</p><p>The applicant must have completed a bachelor's degree in any stream with a 10+2+3 education qualification pattern.</p><p>The graduation must be completed from a university recognised by the Association of Indian Universities (AIU).</p><p>A minimum of 50% of the aggregate marks must be scored in the graduation.</p>",
    "fee_heading": "Fee Structure",
    "admission_steps": "<p>The admission process for an online MBA program at Manipal University Online is quite simple and student friendly. Interested students are required to follow the below-mentioned steps:</p><ol><li><strong>Register</strong> for the Online MBA program at the official website of Manipal University Online.</li><li><strong>Pay the fee</strong> according to the chosen specialization.</li><li><strong>Upload the required documents</strong> and submit the application form.</li><li><strong>Receive confirmation</strong> once the university verifies the student's information and documents.</li></ol>",
    "highlights": [
      {
        "highlight_title": "Equally Valid Credential",
        "highlight_description": "An Online MBA degree program from Manipal Online is equally valid and credible as a traditional MBA program."
      },
      {
        "highlight_title": "Ranked #1 by Careers360",
        "highlight_description": "The Manipal Online MBA is ranked #1 by careers360 making it an ideal program for students and working professionals."
      },
      {
        "highlight_title": "Access to 10K+ Courses",
        "highlight_description": "The Manipal University Online MBA provides access to 10K+ courses and professional certifications from top global universities through Coursera."
      },
      {
        "highlight_title": "Work While You Study",
        "highlight_description": "This program allows working professionals to earn a professional degree without quitting their work schedule."
      },
      {
        "highlight_title": "Placement-Supported Program",
        "highlight_description": "It is a placement-supported program offering better future aspects and career advancement opportunities to students."
      },
      {
        "highlight_title": "Interactive Faculty Engagement",
        "highlight_description": "Despite being an online learning program, students can interact with their faculty members through online classes, virtual classrooms, and discussion forums."
      },
      {
        "highlight_title": "Affordable Fees",
        "highlight_description": "The Manipal University Jaipur Online MBA fees are comparatively affordable and pocket-friendly as a regular postgraduate degree program."
      },
      {
        "highlight_title": "Scholarships & Financial Aid",
        "highlight_description": "To lessen the financial burden on students, the program includes attractive scholarships and various financial aids."
      }
    ],
    "admission_fee_note": "Step 2. After the registration process pay the fee according to the chosen specialization.",
    "fee_plans": "NA",
    "about_content": "<p>Manipal University Online offers a 2 year online Master of Business Administration (MBA) in Human Resource Management course, designed to equip students with essential skills in strategic HR management and change management. The Online MBA in HR Management from the Manipal University program covers key subjects such as employee relations management, compensation and benefits, and organizational behaviour, providing a comprehensive understanding of HR practices.</p><p>Graduates of an Online MBA in Human Resource Management from Manipal Online are prepared to pursue leadership roles in HR departments, consulting firms, and multinational corporations. The curriculum emphasizes practical knowledge and strategic thinking so that the students are well-versed in the effective management of human resources.</p>",
    "emi_content": "INR 7,292 /- per month with no-cost EMI facility. Total fee: INR 1,75,000 /-, Per semester: INR 43,750 /-",
    "reviews": [
      {
        "review_text": "My experience with online manipal is quite okay and honestly, the university is good there facilities were far good from my expectations.",
        "reviewer_label": "Student"
      },
      {
        "review_text": "The best thing I liked about the Online Manipal is there placement assistance.",
        "reviewer_label": "Student"
      },
      {
        "review_text": "The faculty members are very cooperative and supportive because of them I was able to complete my online BBA with good marks.",
        "reviewer_label": "Student"
      },
      {
        "review_text": "Good facilities and affordable fee, I highly recommend it to others.",
        "reviewer_label": "Student"
      }
    ],
    "exam_content": "<p>The Online Manipal examinations are conducted digitally via computer-based and online procured means. The examinations for Manipal Online programs are highly flexible and allow students to appear for term-end examinations from any corner of the world. However, students must have a laptop or desktop/computer with a good connection to the internet and a functional webcam. The evaluation of the online degree program at Online Manipal is carried out with two major components i.e. theory papers and practical papers. Simultaneously, students are required to score a minimum of 40% aggregate score in both parts to be considered as pass.</p>",
    "job_profiles": [
      {
        "job_title": "Human Resources Manager",
        "avg_salary": "INR 3 LPA"
      },
      {
        "job_title": "Learning and Development Manager",
        "avg_salary": "INR 5 LPA"
      },
      {
        "job_title": "Employee Relations Manager",
        "avg_salary": "INR 6.1 LPA"
      },
      {
        "job_title": "Compensation and Benefits Manager",
        "avg_salary": "INR 9 LPA"
      },
      {
        "job_title": "Organizational Development Manager",
        "avg_salary": "INR 4 LPA"
      },
      {
        "job_title": "HR Consultant",
        "avg_salary": "INR 3.5 LPA"
      }
    ],
    "faqs": [
      {
        "question": "What is the eligibility to apply for the HR Management Course from Manipal Online?",
        "answer": "The applicant must have completed 10 + 2 + 3 years of educational qualification from a recognized institute with a minimum of 50% aggregate marks, to fall under the eligibility criteria of the HR Management Course from Manipal Online."
      },
      {
        "question": "Is the HR Management online MBA from Manipal Online valid?",
        "answer": "Yes, HR Management Course from Manipal Online is UGC-recognized making it a completely valid degree course."
      },
      {
        "question": "What is the average package for Manipal Online University MBA HR Management?",
        "answer": "The average package offered to Manipal Online University HR Management and other online MBA courses is INR 5.2 LPA approx."
      }
    ],
    "placement_content": "<p>The Online Manipal University Jaipur (MUJ) offers placement assistance to every enrolled student. To ensure a fruitful career for students Manipal Online offers various facilities along with its placement assistance including:</p><ul><li>Assistance in preparing an impactful resume with the advanced placement portal of Manipal Online.</li><li>Alumni interaction during and after the program for better industry insight and career guidance.</li><li>Multiple industry readiness sessions to make students familiar with global market trends, requirements, and recruiter behaviour.</li><li>Mock interviews to motivate students and help them identify their strengths and weaknesses.</li><li>Virtual placement drives are conducted by Manipal University Online to make the job research journey easy and compatible.</li></ul><p>A few major active hiring partners of Online Manipal University Jaipur (MUJ) are:</p><ul><li>Genpact</li><li>Accenture</li><li>KPMG</li><li>Capgemini</li><li>Infosys</li><li>TATA Communications</li><li>MyGate</li><li>IBM, etc.</li></ul>",
    "other_specs": [
      {
        "other_spec_name": "Finance"
      },
      {
        "other_spec_name": "Marketing"
      },
      {
        "other_spec_name": "Retail Management"
      },
      {
        "other_spec_name": "Digital Marketing"
      },
      {
        "other_spec_name": "BFSI"
      },
      {
        "other_spec_name": "Project Management"
      },
      {
        "other_spec_name": "IT & FinTech"
      },
      {
        "other_spec_name": "Human Resource Management"
      },
      {
        "other_spec_name": "Operations Management"
      },
      {
        "other_spec_name": "International Business"
      },
      {
        "other_spec_name": "Information System Management"
      },
      {
        "other_spec_name": "Analytics and Data Science"
      },
      {
        "other_spec_name": "Supply Chain Management"
      }
    ],
    "syllabus_content": "<p>The Manipal Online MBA in Human Resource Management syllabus is crafted to offer an overall grasp of HR industry trends and requirements to aspiring HR professionals. The Manipal Online MBA in Human Resource Management follows a semester pattern, referred to as the table mentioned below:</p><h4>Year I</h4><h4>Semester I</h4><ul><li>Entrepreneurial Practice</li><li>Business Communication (WAC)</li><li>Managerial Economics</li><li>Financial Accounting</li><li>Data Visualisation (Excel/Tableau)</li><li>Organizational Behaviour</li><li>Marketing Management</li></ul><h4>Semester II</h4><ul><li>Business Research Methods (R/Python)</li><li>Operation Management</li><li>Human Resource Management</li><li>Management Accounting</li><li>Financial Management</li><li>Legal Aspects of Business</li><li>Business Communication (VAC)</li></ul><h4>Year II</h4><h4>Semester III</h4><ul><li>Strategic Management</li><li>Electives/Specializations subjects</li><li>Manpower Planning and Sourcing</li><li>Management and Organizational Development</li><li>Employee Relations Management</li><li>HR Audit</li><li>Term Paper</li></ul><h4>Semester IV</h4><ul><li>International Business Management</li><li>Electives/Specializations subjects</li><li>Compensation and Benefits</li><li>Performance Management and Appraisal</li><li>Talent Management and Employee Retention</li><li>Change Management</li><li>Project</li></ul>",
    "duration": "2 years",
    "naac_grade": "A",
    "ugc_status": "Entitled",
    "total_fee": "INR 1,75,000/-",
    "num_programs": "Manipal Online Jaipur MBA",
    "spec_name": "Human Resource Management",
    "course_name": "Manipal Online Mba In Human Resource Management",
    "program_name": "MBA",
    "university_name": "Manipal",
    "mode": "Online",
    "starting_fee": "INR 1,75,000/-",
    "eligibility_summary": "Students and interested working professionals to enroll in an Online MBA program offered at Manipal Online University ar...",
    "seo_title": "Online MBA in HR Management | Manipal University",
    "meta_description": "Online MBA in Human Resource Management from Manipal University. 2-year program, NAAC A-rated, UGC entitled. ₹1,75,000 total fee. Enroll now!",
    "about_heading": "Manipal Online MBA in HR Course Details",
    "admission_heading": "Manipal Online MBA Admission process",
    "emi_heading": "Manipal Online MBA in Human Resource EMI Details",
    "exam_heading": "Examination process at Online Manipal",
    "placement_heading": "Placement Partners of Online Manipal",
    "reviews_heading": "Online Manipal University Reviews (Online Manipal University Jaipur - MUJ)",
    "faqs_heading": "FAQs",
    "highlights_heading": "Course Facts",
    "eligibility_heading": "Eligibility Criteria",
    "syllabus_heading": "Online Human Resource Management Syllabus of Manipal Online",
    "jobs_heading": "Manipal Online MBA in HR Job Opportunities",
    "other_specs_heading": "Specializations offered",
    "hero_description": "This is what user have put in not extracted by the parser.",
    "hero_image_url": "/assets/images/nodia-manipal-online-mba-in-human-resource-management-hero.png"
  }
}
```

### 3.4 Blog Article Page Source (`Blogs/untitled/source.json`)
```json
{
  "university_slug": "nodia",
  "page_type": "blog",
  "slug": "untitled",
  "parent_slug": null,
  "saved_at": "2026-06-20T16:19:34.724173+00:00",
  "data": {
    "title": "Is an Online Degree Valid in India? UGC Rules, Recognition & Career Value Explained (2026 Guide)",
    "excerpt": "The phase where students view online education has shifted from curiosity to credibility in India. Over the last few years, a plethora of candidates have enrolled in online degree programs for higher education while still working and with no geographical constraint.",
    "content_html": "<h3>Introduction</h3>\n<p>The phase where students view online education has shifted from curiosity to credibility in India. Over the last few years, a plethora of candidates have enrolled in online degree programs for higher education while still working and with no geographical constraint.</p>\n<p>However, there is still one question that continues to dominate discussions among students: “Is an online degree actually valid in India?”</p>\n<p>Most of this confusion arises as people do not understand that there are different types of degrees available through flexible learning: distance education, online degrees, and others. There are now numerous recognized universities offering online degree programs, but the concern for students is whether their online degree will be accepted for government jobs, in private industry, or for pursuing further education.</p>\n<p>On the positive side, the Government of India has now established regulatory guidelines on online degrees. The University Grants Commission (UGC) has been formally recognized to regulate online degrees, thereby providing regulation and transparency to online education in India.</p>\n<p>This blog explains in detail about: the rules regarding online degrees; recognition of online degrees, acceptance of online degrees by employers, and universities offering online degree programs in India.</p>\n<h2>Are Online Degrees Valid in India? (Quick Answer)</h2>\n<p>Yes, online degrees are completely valid in India only if they are pursued from a university recognized by the University Grants Commission (UGC).</p>\n<p>Thus, a valid online degree in India offers the following advantages:</p>\n<ul>\n  <li>Holds the same academic value as regular degrees.</li>\n  <li>It is valid across India.</li>\n  <li>Accepted for jobs, promotions, and higher education.</li>\n  <li>They are eligible to appear for competitive exams and government recruitment.</li>\n</ul>\n<p>Online degree programs in India operate under regulatory guidelines through the UGC Distance Education Bureau (UGC-DEB) framework, ensuring universities follow academic quality standards similar to traditional programs.</p>\n<h2>What Does UGC Say About Online Degrees?</h2>\n<p>The UGC has introduced a set of structured guidelines to ensure that an online degree is valid in India and follows a standardized and structured learning environment at par with traditional education.</p>\n<p>Key guidelines include:</p>\n<ul>\n  <li>Universities must obtain UGC entitlement before delivering online degree programs.</li>\n  <li>Online degree courses must be delivered through approved LMS (Learning Management Systems).</li>\n  <li>Course curriculum must be equivalent to regular on-campus courses with the same learning outcomes.</li>\n  <li>Teaching and assessment must be carried out by skilled and qualified faculty members.</li>\n  <li>Online and digital assessment methods are permitted for students taking online courses.</li>\n</ul>\n<p>These guidelines ensure online learners experience the same level of academic rigour as campus-based learners.</p>\n<p>The objective of the UGC guidelines is simply to demonstrate that while the method of delivering higher education may change with technological advancements, its value and credibility remain the same.</p>\n<h2>Online Degree vs Distance Degree vs Regular Degree</h2>\n<p>The detailed comparison between online, distance, and regular degree programs are mentioned in the following table:</p>\n<h2>Are Online Degrees Accepted for Government Jobs in India?</h2>\n<p>Yes, degrees obtained from UGC-recognized universities via online learning mode are accepted for public service and government employment within India.</p>\n<p>The acceptance of degrees obtained through online education will extend to:</p>\n<ul>\n  <li>UPSC examinations.</li>\n  <li>SSC recruitment processes.</li>\n  <li>State government positions.</li>\n  <li>Public Sector Undertakings (PSU).</li>\n</ul>\n<p>For candidates with an objective of entering government services, they must focus on degree recognition rather than online or traditional classroom delivery.</p>\n<h2>Are Online Degrees Accepted by Private Companies?</h2>\n<p>Acceptance of online education from private corporations continues to grow. Today’s employers evaluate potential employees based on three criteria:</p>\n<ul>\n  <li>Knowledge/Skills</li>\n  <li>Reputation of the university</li>\n  <li>Prior work experience</li>\n  <li>Industry exposure</li>\n</ul>\n<p>Online education has been particularly accepted in the following sectors:</p>\n<ul>\n  <li>IT and Software Development</li>\n  <li>Management and Business Operations</li>\n  <li>Data Science and Analytics</li>\n  <li>Finance and Digital Marketing</li>\n</ul>\n<p>A growing number of professionals are pursuing online MBAs or other master's programs while they work to achieve continuous growth in their careers through online education.</p>\n<h2>Can You Pursue Higher Education After an Online Degree?</h2>\n<p>Yes, one can easily pursue higher education after an online degree if it is awarded by a UG-recognized university.</p>\n<p>You can easily pursue:</p>\n<ul>\n  <li>A traditional or online MBA after an online bachelor’s.</li>\n  <li>Online or regular MCA or MSc programs.</li>\n  <li>PhD, online DBA, ot other doctoral courses.</li>\n  <li>Professional certification.</li>\n</ul>\n<p>Universities treat approved online degrees as academically equivalent qualifications for higher education in both traditional and virtual environments.</p>\n<h2>How to Check If an Online Degree Is Valid in India</h2>\n<p>To secure the cost, time, and hard work put into an academic program, students must always verify the validity of an online degree program before enrolling:</p>\n<ul>\n  <li>Check the official portal of UGC.</li>\n  <li>Confirm the university and online program approval.</li>\n  <li>Verify program recognition status on the official website of the university.</li>\n  <li>Avoid unauthorized study centers.</li>\n  <li>Check the NAAC accreditation grade.</li>\n  <li>Ensure admission happens directly through the university.</li>\n</ul>\n<h2>Top UGC-Approved Universities Offering Online Degrees</h2>\n<p>There are numerous UGC-recognized universities in India offering valid online degree programs, among which the most popular ones are listed below:</p>\n<ul>\n  <li>Indira Gandhi National Open University (IGNOU Online)</li>\n  <li>Amity University Online</li>\n  <li>Manipal University Jaipur Online</li>\n  <li>Jain University Online</li>\n  <li>Lovely Professional University Online (LPU Online)</li>\n  <li>NMIMS Online</li>\n  <li>DPU Online (Pune)</li>\n  <li>UPES Online</li>\n  <li>Amrita University Online (Amrita AHEAD Online)</li>\n  <li>Shoolini University Online</li>\n</ul>\n<h2>Advantages of a Valid Online Degree</h2>\n<p>There are numerous benefits of pursuing a valid online degree program, such as:</p>\n<ul>\n  <li>Study while working full-time</li>\n  <li>Cost-effective fee structure</li>\n  <li>Flexible learning schedules</li>\n  <li>Industry-oriented curriculum</li>\n  <li>Digital skill development</li>\n  <li>Global academic recognition</li>\n  <li>Accessible education from anywhere in India</li>\n</ul>\n<h2>Common Myths About Online Degrees (Myth vs Reality)</h2>\n<p>There are multiple myths about online degrees prevailing in the students' subconscious minds. For better clarity, the table below states common misconceptions and the reality about online degree programs.</p>\n<h2>When an Online Degree May NOT Be Valid</h2>\n<p>An online degree can be considered invalid in the following scenarios:</p>\n<ul>\n  <li>Not approved by UGC.</li>\n  <li>Foreign universities offering online degrees without authorization in India.</li>\n  <li>Unauthorized franchise study centers.</li>\n  <li>EdTech certificates marketed as “degrees.”</li>\n  <li>Universities not listed on official regulatory portals (UGC-DEB).</li>\n</ul>\n<h2>Frequently Asked Questions (FAQs)</h2>\n<ul>\n  <li>Is online degree valid for government jobs?</li>\n  <li>Yes, an online degree from a UGC-recognized university is valid for government jobs.</li>\n  <li>Is online MBA valid in India?</li>\n  <li>Yes, online MBAs are completely valid in India if they are offered by an institution recognized by UGC.</li>\n  <li>Can I do UPSC after online graduation?</li>\n  <li>Yes, if you have a UGC-entitled bachelor’s online degree, then you can do UPSC after graduation.</li>\n  <li>Are online degrees valid abroad?</li>\n  <li>Yes, online degrees are valid abroad only if they are awarded by a reputable, renowned, and accredited institution.</li>\n  <li>Do companies reject online degrees?</li>\n  <li>No, companies do not reject online degrees. Employers have shifted their prime consideration from the learning mode to skills, abilities, and experience of a candidate.</li>\n</ul>\n<table><thead><tr><th>Factor</th><th>Online Degree</th><th>Distance Degree</th><th>Regular Degree</th></tr></thead><tbody><tr><td>Classes</td><td>Live + Recorded</td><td>Self-paced learning</td><td>Classroom learning</td></tr><tr><td>Flexibility</td><td>High</td><td>Medium</td><td>Low</td></tr><tr><td>Interaction</td><td>High (live sessions, forums)</td><td>Limited</td><td>High</td></tr><tr><td>Learning Method</td><td>Virtual learning</td><td>Printed/self modules</td><td>Physical on-campus</td></tr><tr><td>Recognition</td><td>Valid (UGC Approved)</td><td>Valid (UGC-DEB approved)</td><td>Valid</td></tr><tr><td>Ideal For</td><td>Working professionals</td><td>Independent learners</td><td>Full-time students</td></tr></tbody></table>\n<table><thead><tr><th>Myth</th><th>Reality</th></tr></thead><tbody><tr><td>Online degrees are fake</td><td>False if UGC-approved</td></tr><tr><td>Companies don’t accept them</td><td>Increasingly accepted (employer perception)</td></tr><tr><td>Academic quality is lower</td><td>Same curriculum standards</td></tr><tr><td>Only weak students choose online</td><td>Widely used by professionals (time-saving and cost-effective)</td></tr><tr><td>No career growth</td><td>Strong upskilling pathway</td></tr></tbody></table>",
    "tag": "Career",
    "author": "Aditi Rao",
    "author_role": "Career Editor",
    "read_time": "6 min read",
    "date": "Jun 20, 2026",
    "blocks": [
      { "type": "h1", "text": "Is an Online Degree Valid in India? UGC Rules, Recognition & Career Value Explained (2026 Guide)" },
      { "type": "h3", "text": "Introduction" },
      { "type": "paragraph", "text": "The phase where students view online education has shifted from curiosity to credibility in India. Over the last few years, a plethora of candidates have enrolled in online degree programs for higher education while still working and with no geographical constraint." },
      { "type": "paragraph", "text": "However, there is still one question that continues to dominate discussions among students: “Is an online degree actually valid in India?”" },
      { "type": "paragraph", "text": "Most of this confusion arises as people do not understand that there are different types of degrees available through flexible learning: distance education, online degrees, and others. There are now numerous recognized universities offering online degree programs, but the concern for students is whether their online degree will be accepted for government jobs, in private industry, or for pursuing further education." },
      { "type": "paragraph", "text": "On the positive side, the Government of India has now established regulatory guidelines on online degrees. The University Grants Commission (UGC) has been formally recognized to regulate online degrees, thereby providing regulation and transparency to online education in India." },
      { "type": "paragraph", "text": "This blog explains in detail about: the rules regarding online degrees; recognition of online degrees, acceptance of online degrees by employers, and universities offering online degree programs in India." },
      { "type": "h2", "text": "Are Online Degrees Valid in India? (Quick Answer)" },
      { "type": "paragraph", "text": "Yes, online degrees are completely valid in India only if they are pursued from a university recognized by the University Grants Commission (UGC)." },
      { "type": "paragraph", "text": "Thus, a valid online degree in India offers the following advantages:" },
      { "type": "list_item", "text": "Holds the same academic value as regular degrees." },
      { "type": "list_item", "text": "It is valid across India." },
      { "type": "list_item", "text": "Accepted for jobs, promotions, and higher education." },
      { "type": "list_item", "text": "They are eligible to appear for competitive exams and government recruitment." },
      { "type": "paragraph", "text": "Online degree programs in India operate under regulatory guidelines through the UGC Distance Education Bureau (UGC-DEB) framework, ensuring universities follow academic quality standards similar to traditional programs." },
      { "type": "h2", "text": "What Does UGC Say About Online Degrees?" },
      { "type": "paragraph", "text": "The UGC has introduced a set of structured guidelines to ensure that an online degree is valid in India and follows a standardized and structured learning environment at par with traditional education." },
      { "type": "paragraph", "text": "Key guidelines include:" },
      { "type": "list_item", "text": "Universities must obtain UGC entitlement before delivering online degree programs." },
      { "type": "list_item", "text": "Online degree courses must be delivered through approved LMS (Learning Management Systems)." },
      { "type": "list_item", "text": "Course curriculum must be equivalent to regular on-campus courses with the same learning outcomes." },
      { "type": "list_item", "text": "Teaching and assessment must be carried out by skilled and qualified faculty members." },
      { "type": "list_item", "text": "Online and digital assessment methods are permitted for students taking online courses." },
      { "type": "paragraph", "text": "These guidelines ensure online learners experience the same level of academic rigour as campus-based learners." },
      { "type": "paragraph", "text": "The objective of the UGC guidelines is simply to demonstrate that while the method of delivering higher education may change with technological advancements, its value and credibility remain the same." },
      { "type": "h2", "text": "Online Degree vs Distance Degree vs Regular Degree" },
      { "type": "paragraph", "text": "The detailed comparison between online, distance, and regular degree programs are mentioned in the following table:" },
      { "type": "h2", "text": "Are Online Degrees Accepted for Government Jobs in India?" },
      { "type": "paragraph", "text": "Yes, degrees obtained from UGC-recognized universities via online learning mode are accepted for public service and government employment within India." },
      { "type": "paragraph", "text": "The acceptance of degrees obtained through online education will extend to:" },
      { "type": "list_item", "text": "UPSC examinations." },
      { "type": "list_item", "text": "SSC recruitment processes." },
      { "type": "list_item", "text": "State government positions." },
      { "type": "list_item", "text": "Public Sector Undertakings (PSU)." },
      { "type": "paragraph", "text": "For candidates with an objective of entering government services, they must focus on degree recognition rather than online or traditional classroom delivery." },
      { "type": "h2", "text": "Are Online Degrees Accepted by Private Companies?" },
      { "type": "paragraph", "text": "Acceptance of online education from private corporations continues to grow. Today’s employers evaluate potential employees based on three criteria:" },
      { "type": "list_item", "text": "Knowledge/Skills" },
      { "type": "list_item", "text": "Reputation of the university" },
      { "type": "list_item", "text": "Prior work experience" },
      { "type": "list_item", "text": "Industry exposure" },
      { "type": "paragraph", "text": "Online education has been particularly accepted in the following sectors:" },
      { "type": "list_item", "text": "IT and Software Development" },
      { "type": "list_item", "text": "Management and Business Operations" },
      { "type": "list_item", "text": "Data Science and Analytics" },
      { "type": "list_item", "text": "Finance and Digital Marketing" },
      { "type": "paragraph", "text": "A growing number of professionals are pursuing online MBAs or other master's programs while they work to achieve continuous growth in their careers through online education." },
      { "type": "h2", "text": "Can You Pursue Higher Education After an Online Degree?" },
      { "type": "paragraph", "text": "Yes, one can easily pursue higher education after an online degree if it is awarded by a UG-recognized university." },
      { "type": "paragraph", "text": "You can easily pursue:" },
      { "type": "list_item", "text": "A traditional or online MBA after an online bachelor’s." },
      { "type": "list_item", "text": "Online or regular MCA or MSc programs." },
      { "type": "list_item", "text": "PhD, online DBA, ot other doctoral courses." },
      { "type": "list_item", "text": "Professional certification." },
      { "type": "paragraph", "text": "Universities treat approved online degrees as academically equivalent qualifications for higher education in both traditional and virtual environments." },
      { "type": "h2", "text": "How to Check If an Online Degree Is Valid in India" },
      { "type": "paragraph", "text": "To secure the cost, time, and hard work put into an academic program, students must always verify the validity of an online degree program before enrolling:" },
      { "type": "list_item", "text": "Check the official portal of UGC." },
      { "type": "list_item", "text": "Confirm the university and online program approval." },
      { "type": "list_item", "text": "Verify program recognition status on the official website of the university." },
      { "type": "list_item", "text": "Avoid unauthorized study centers." },
      { "type": "list_item", "text": "Check the NAAC accreditation grade." },
      { "type": "list_item", "text": "Ensure admission happens directly through the university." },
      { "type": "h2", "text": "Top UGC-Approved Universities Offering Online Degrees" },
      { "type": "paragraph", "text": "There are numerous UGC-recognized universities in India offering valid online degree programs, among which the most popular ones are listed below:" },
      { "type": "list_item", "text": "Indira Gandhi National Open University (IGNOU Online)" },
      { "type": "list_item", "text": "Amity University Online" },
      { "type": "list_item", "text": "Manipal University Jaipur Online" },
      { "type": "list_item", "text": "Jain University Online" },
      { "type": "list_item", "text": "Lovely Professional University Online (LPU Online)" },
      { "type": "list_item", "text": "NMIMS Online" },
      { "type": "list_item", "text": "DPU Online (Pune)" },
      { "type": "list_item", "text": "UPES Online" },
      { "type": "list_item", "text": "Amrita University Online (Amrita AHEAD Online)" },
      { "type": "list_item", "text": "Shoolini University Online" },
      { "type": "h2", "text": "Advantages of a Valid Online Degree" },
      { "type": "paragraph", "text": "There are numerous benefits of pursuing a valid online degree program, such as:" },
      { "type": "list_item", "text": "Study while working full-time" },
      { "type": "list_item", "text": "Cost-effective fee structure" },
      { "type": "list_item", "text": "Flexible learning schedules" },
      { "type": "list_item", "text": "Industry-oriented curriculum" },
      { "type": "list_item", "text": "Digital skill development" },
      { "type": "list_item", "text": "Global academic recognition" },
      { "type": "list_item", "text": "Accessible education from anywhere in India" },
      { "type": "h2", "text": "Common Myths About Online Degrees (Myth vs Reality)" },
      { "type": "paragraph", "text": "There are multiple myths about online degrees prevailing in the students' subconscious minds. For better clarity, the table below states common misconceptions and the reality about online degree programs." },
      { "type": "h2", "text": "When an Online Degree May NOT Be Valid" },
      { "type": "paragraph", "text": "An online degree can be considered invalid in the following scenarios:" },
      { "type": "list_item", "text": "Not approved by UGC." },
      { "type": "list_item", "text": "Foreign universities offering online degrees without authorization in India." },
      { "type": "list_item", "text": "Unauthorized franchise study centers." },
      { "type": "list_item", "text": "EdTech certificates marketed as “degrees.”" },
      { "type": "list_item", "text": "Universities not listed on official regulatory portals (UGC-DEB)." },
      { "type": "h2", "text": "Frequently Asked Questions (FAQs)" },
      { "type": "list_item", "text": "Is online degree valid for government jobs?" },
      { "type": "list_item", "text": "Yes, an online degree from a UGC-recognized university is valid for government jobs." },
      { "type": "list_item", "text": "Is online MBA valid in India?" },
      { "type": "list_item", "text": "Yes, online MBAs are completely valid in India if they are offered by an institution recognized by UGC." },
      { "type": "list_item", "text": "Can I do UPSC after online graduation?" },
      { "type": "list_item", "text": "Yes, if you have a UGC-entitled bachelor’s online degree, then you can do UPSC after graduation." },
      { "type": "list_item", "text": "Are online degrees valid abroad?" },
      { "type": "list_item", "text": "Yes, online degrees are valid abroad only if they are awarded by a reputable, renowned, and accredited institution." },
      { "type": "list_item", "text": "Do companies reject online degrees?" },
      { "type": "list_item", "text": "No, companies do not reject online degrees. Employers have shifted their prime consideration from the learning mode to skills, abilities, and experience of a candidate." },
      {
        "type": "table",
        "rows": [
          [ "Factor", "Online Degree", "Distance Degree", "Regular Degree" ],
          [ "Classes", "Live + Recorded", "Self-paced learning", "Classroom learning" ],
          [ "Flexibility", "High", "Medium", "Low" ],
          [ "Interaction", "High (live sessions, forums)", "Limited", "High" ],
          [ "Learning Method", "Virtual learning", "Printed/self modules", "Physical on-campus" ],
          [ "Recognition", "Valid (UGC Approved)", "Valid (UGC-DEB approved)", "Valid" ],
          [ "Ideal For", "Working professionals", "Independent learners", "Full-time students" ]
        ]
      },
      {
        "type": "table",
        "rows": [
          [ "Myth", "Reality" ],
          [ "Online degrees are fake", "False if UGC-approved" ],
          [ "Companies don’t accept them", "Increasingly accepted (employer perception)" ],
          [ "Academic quality is lower", "Same curriculum standards" ],
          [ "Only weak students choose online", "Widely used by professionals (time-saving and cost-effective)" ],
          [ "No career growth", "Strong upskilling pathway" ]
        ]
      }
    ],
    "hero_image_url": "/assets/images/blog-untitled-hero.jpg"
  }
}
```

### 3.5 Programs Listing Page Source (`Pages/programs/source.json`)
```json
{
  "university_slug": "nodia",
  "page_type": "programs_listing",
  "slug": "programs",
  "parent_slug": null,
  "saved_at": "2026-06-20T15:52:43.200566+00:00",
  "data": {
    "university_slug": "nodia",
    "university_name": "Nodia"
  }
}
```

### 3.6 Specializations Listing Page Source (`Pages/specializations/source.json`)
```json
{
  "university_slug": "nodia",
  "page_type": "specializations_listing",
  "slug": "specializations",
  "parent_slug": null,
  "saved_at": "2026-06-20T15:52:43.205991+00:00",
  "data": {
    "university_slug": "nodia",
    "university_name": "Nodia"
  }
}
```

### 3.7 Blog Listing Page Source (`Pages/blog/source.json`)
```json
{
  "university_slug": "nodia",
  "page_type": "blog_listing",
  "slug": "blog",
  "parent_slug": null,
  "saved_at": "2026-06-20T15:52:43.211625+00:00",
  "data": {
    "university_slug": "nodia",
    "university_name": "Nodia"
  }
}
```

---

## SECTION 4 — Build Folder Audit

Static export directory for workspace `nodia`: `backend/workspaces/nodia/build/`.

### 4.1 Build Folder Tree
```text
backend/workspaces/nodia/build/
├── index.html
├── sitemap.xml
├── routes.json
├── assets/
│   ├── support.js
│   └── images/
│       ├── blog-untitled-hero.jpg
│       ├── nodia-manipal-online-mba-in-human-resource-management-hero.png
│       └── university-hero.jpg
├── programs/
│   └── index.html
├── specializations/
│   └── index.html
├── nodia-manipal-online-mba-in-human-resource-management/
│   └── index.html
└── blog/
    ├── index.html
    └── untitled/
        └── index.html
```

---

## SECTION 5 — Route Audit

Auditing mappings specified in `routes.json`:

### 5.1 Route Mapping Analysis
| Expected Route | Actual File on Disk | File Exists? | Serving Status (FastAPI port 8000) |
| :--- | :--- | :--- | :--- |
| `/` | `build/index.html` | **Yes** | Returns 404 (Not Found) |
| `/programs` | `build/programs/index.html` | **Yes** | Returns 404 (Not Found) |
| `/specializations` | `build/specializations/index.html` | **Yes** | Returns 404 (Not Found) |
| `/blog` | `build/blog/index.html` | **Yes** | Returns 404 (Not Found) |
| `/blog/untitled` | `build/blog/untitled/index.html` | **Yes** | Returns 404 (Not Found) |
| `/nodia-manipal-online-mba-in-human-resource-management` | `build/nodia-manipal-online-mba-in-human-resource-management/index.html` | **Yes** | Returns 404 (Not Found) |

### 5.2 Broken Route Identification
All clean routes return `{"detail":"Not Found"}` when requested directly on the backend server (`http://localhost:8000/programs`, `/blog/untitled`, etc.). This is because the FastAPI backend does not register wildcards or catch-alls routing clean routes to their respective static directory folders. They are only viewable when utilizing the `/build-file` endpoint via queries (e.g. `http://localhost:8000/build-file?university_slug=nodia&path=programs/index.html`).

---

## SECTION 6 — Template Resolution Audit

Auditing generated HTML templates inside the `nodia` workspace to identify remaining Jinja variables and client-side DC runtime directives.

### 6.1 Remaining Jinja Variables in Final Compiled/Built Output
The following double-braced template syntax remains completely untouched in the final compiled HTML files (and built files):

#### 1. In `Pages/specializations/specializations_listing.html` (and `build/specializations/index.html`):
- Line 64: `specGroups` -> `<sc-for list="{{ specGroups }}" as="g">`
- Line 68: `g.courseName` -> `{{ g.courseName }}`
- Line 70: `g.courseHref` -> `{{ g.courseHref }}`
- Line 74: `g.specs` -> `<sc-for list="{{ g.specs }}" as="sp">`
- Line 75: `sp.href` -> `href="{{ sp.href }}"`
- Line 77: `sp.name` -> `{{ sp.name }}`
- Line 78: `sp.description` -> `{{ sp.description }}`
- Line 80: `sp.feeFormatted` -> `{{ sp.feeFormatted }}`

#### 2. In `Pages/blog/blog_listing.html` (and `build/blog/index.html`):
- Line 65: `categories` -> `<sc-for list="{{ categories }}" as="c">`
- Line 66: `c.label`, `c.color`, `c.bg`, `c.border` -> `{{ c.label }}` etc.
- Line 72: `hasFeatured` -> `<sc-if value="{{ hasFeatured }}">`
- Line 74: `featured.href` -> `href="{{ featured.href }}"`
- Line 77: `featured.tag` -> `{{ featured.tag }}`
- Line 78: `featured.title` -> `{{ featured.title }}`
- Line 79: `featured.excerpt` -> `{{ featured.excerpt }}`
- Line 81: `featured.authorInitial` -> `{{ featured.authorInitial }}`
- Line 82: `featured.author`, `featured.meta` -> `{{ featured.author }}` etc.
- Line 93: `posts` -> `<sc-for list="{{ posts }}" as="p">`
- Line 94: `p.href` -> `href="{{ p.href }}"`
- Line 95, 97: `p.tag` -> `{{ p.tag }}`
- Line 98: `p.title` -> `{{ p.title }}`
- Line 99: `p.excerpt` -> `{{ p.excerpt }}`
- Line 100: `p.meta` -> `{{ p.meta }}`

#### 3. In `Pages/programs/programs_listing.html` (and `build/programs/index.html`):
- Line 65: `programs` -> `<sc-for list="{{ programs }}" as="p">`
- Line 66: `p.href` -> `href="{{ p.href }}"`
- Line 68: `p.name` -> `{{ p.name }}`
- Line 69: `p.description` -> `{{ p.description }}`
- Line 73: `p.duration` -> `{{ p.duration }}`
- Line 77: `p.mode` -> `{{ p.mode }}`
- Line 81: `p.eligibility` -> `{{ p.eligibility }}`
- Line 86: `p.feeFormatted` -> `{{ p.feeFormatted }}`

#### 4. In `Blogs/untitled/blog.html` (and `build/blog/untitled/index.html`):
- Line 211: `toc` -> `<sc-for list="{{ toc }}" as="t">`
- Line 212: `t` -> `{{ t }}`
- Line 229: `related` -> `<sc-for list="{{ related }}" as="p">`
- Line 231: `p.tag` -> `{{ p.tag }}`
- Line 233: `p.tag` -> `{{ p.tag }}`
- Line 234: `p.title` -> `{{ p.title }}`
- Line 235: `p.meta` -> `{{ p.meta }}`

#### 5. In `University/university.html` (and `build/index.html`):
- Line 57: `heroWrap` -> `style="{{ heroWrap }}"`
- Line 60: `heroBadge` -> `style="{{ heroBadge }}"`
- Line 61: `heroH1` -> `color:{{ heroH1 }}`
- Line 62: `heroSub` -> `color:{{ heroSub }}`
- Line 65: `heroSecBtn` -> `style="{{ heroSecBtn }}"`
- Line 68: `heroStatLabel` -> `color:{{ heroStatLabel }}`
- Line 69: `heroStatDivider` -> `border-left:1px solid {{ heroStatDivider }}`
- Line 104: `programs` -> `<sc-for list="{{ programs }}" as="p">`
- Line 105: `p.cardStyle`, `p.href` -> `href="{{ p.href }}"` etc.
- Line 106: `p.badgeStyle`, `p.level` -> `{{ p.level }}` etc.
- Line 107: `p.name` -> `{{ p.name }}`
- Line 110: `p.duration` -> `{{ p.duration }}`
- Line 114: `p.eligibility` -> `{{ p.eligibility }}`
- Line 117: `p.starting_fee` -> `{{ p.starting_fee }}`

### 6.2 Remaining DC Runtime Directives
The custom directives `<x-dc>`, `<helmet>`, `<sc-for>`, `<sc-if>`, and `<script type="text/x-dc" data-dc-script>` remain fully present in the output. The server-side Jinja compiler intentionally ignores them so they can be processed inside the client browser.

---

## SECTION 7 — Listing Page Investigation

Analyzing why variables like `{{ p.level }}` and `{{ p.name }}` appear literal in the final page outputs.

### 7.1 What Data was Expected
The `sc-for` loops in listing pages expect complete objects with standard fields.
For example, in `programs_listing.html`:
- Expected fields on program `p`: `name`, `description`, `duration`, `mode`, `eligibility`, `feeFormatted`, `href`.

### 7.2 What Data was Provided
The compiler's mock fallback data block (`uni_programs` in `engine.py` line 476, used when the workspace has no courses) provides mismatching fields:
- Provided fields: `level`, `name`, `dur` (mismatch), `fee`, `feeUnit`, `elig` (mismatch), `d` (mismatch), `href`, `featured`.
- Completely missing fields: `mode` (mismatch), `slug` (causes `href` mapping to fallback to `'#'`).

### 7.3 What Data was Rendered
If the client-side parser successfully executes:
- `p.name` is rendered as `"Online MBA"`.
- `p.level` is rendered as `"Postgraduate"`.
- Fields like `duration`, `eligibility`, `description`, and `mode` render as `undefined` (empty) because the fallback key names do not match the template keys!
- The link resolves to `#`.

### 7.4 What Remained Unresolved (and Why it Appears in final output)
Because the builder rewrote the client runtime loading source to `<script src="/assets/support.js"></script>`, the browser tried to load `/assets/support.js` from the FastAPI root domain and received a **404 Not Found** response.
As a result:
- The script `support.js` failed to execute.
- The web component template compiler did not run at all.
- The browser fell back to rendering the uncompiled `<x-dc>` elements as standard text, showing the literal double-braced template syntax `{{ p.level }}`, `{{ p.name }}`, `{{ p.d }}` directly on the screen!

---

## SECTION 8 — Builder Audit

### 8.1 Inputs
- **Directory Paths**: The workspace folder `backend/workspaces/nodia/`.
- **Files**: Individual page compiled `.html` files in subdirectory folders.
- **Assets**: Raw assets from `Assets/images` and `Assets/downloads`.
- **Runtime**: Base client boot script `/Users/aryankinha/Documents/Degree/temp/acfTOhtml copy/support.js`.

### 8.2 Outputs
- Outputs a deployable static package under `build/`.
- Generated files include `index.html`, `sitemap.xml`, `routes.json`, `assets/support.js`, and copied image files.

### 8.3 Copied Files
- `support.js` -> `build/assets/support.js`
- `nodia-manipal-online-mba-in-human-resource-management-hero.png` -> `build/assets/images/nodia-manipal-online-mba-in-human-resource-management-hero.png`
- `university-hero.jpg` -> `build/assets/images/university-hero.jpg`
- `blog-untitled-hero.jpg` -> `build/assets/images/blog-untitled-hero.jpg`

### 8.4 Skipped Files
- None. All parsed items were mapped correctly.

### 8.5 Route Rewrites
The builder executes the following exact replaces in HTML files during export:
1. Replaces `src="./support.js"` with `src="/assets/support.js"`.
2. Replaces `href="nodia.dc.html"` with `href="/"`.
3. Replaces listing navigation pages with clean folder URLs:
   - `href="programs_listing.html"` -> `href="/programs/"`
   - `href="specializations_listing.html"` -> `href="/specializations/"`
   - `href="blog_listing.html"` -> `href="/blog/"`
   - `href="nodia-blog.dc.html"` -> `href="/blog/"`
4. Replaces client-side JS mappings:
   - `p.slug + '.html'` -> `'/' + p.slug + '/'`
   - `sp.slug + '.html'` -> `'/' + sp.slug + '/'`
5. Replaces any `{slug}.html` or `{slug}.dc.html` with their clean route from `routes.json` (longest slug first to avoid collisions).

---

## SECTION 9 — Compiler Audit

The compiler (`compiler.py`) runs in a structured execution plan:

### 9.1 Pass 1 — Indexing
Scans all workspace folders to map existing `source.json` configurations.
- **Files processed**:
  - `University/source.json`
  - `Specializations/nodia-manipal-online-mba-in-human-resource-management/source.json`
  - `Blogs/untitled/source.json`

### 9.2 Pass 2 — Context Injection
Enriches items by parsing relations and mapping listings.
- **Context injected**:
  - Injects `_workspace_courses` (empty), `_workspace_specs` (contains 1 spec), and `_workspace_blogs` (contains 1 blog).
  - Resolves template variables and outputs JSON payloads like `spec_groups_json` and `programs_json`.

### 9.3 Pass 3 — File Generation
Renders templates via Jinja2 (`render_resolved`) and writes the output HTML files.
- **Files generated**:
  - `University/university.html`
  - `Specializations/nodia-manipal-online-mba-in-human-resource-management/specialization.html`
  - `Blogs/untitled/blog.html`
  - `Pages/programs/programs_listing.html`
  - `Pages/specializations/specializations_listing.html`
  - `Pages/blog/blog_listing.html`

### 9.4 Validation Errors
- **Dangling course slug**:
  - Specialization `nodia-manipal-online-mba-in-human-resource-management` references `parent_slug: "nodia-online-mba"`.
  - The index has no course matching `nodia-online-mba`.
  - The compiler successfully finishes but records a validation warning.

---

## SECTION 10 — Runtime Dependency Audit

### 10.1 Is `support.js` Required?
**Yes.** The system cannot run without `support.js`. The HTML generated on the server is a skeleton container enclosing a React-compatible template representation under `<x-dc>` elements. `support.js` imports React/ReactDOM CDNs, parses the DOM, executes component scripts, and mounts the compiled views.

### 10.2 Can Build Run Without `support.js`?
**No.** Without `support.js`, the browser renders the uncompiled elements literally.

### 10.3 Direct Build Audit Results
When loading files inside `build/`:
- The browser console reports `GET http://localhost:8000/assets/support.js 404 (Not Found)`.
- The compilation scripts do not trigger.
- The raw double-braced template syntax is visible on-screen.

---

## SECTION 11 — Broken Link Audit

Crawl and routing trace on static files in `build/` (assuming static hosting environment):

- **Homepage (`/`)**:
  - Link to programs listing: `/programs/` (**Working**)
  - Link to specializations listing: `/specializations/` (**Working**)
  - Link to blog listing: `/blog/` (**Working**)
  - Link to specialization page: `/nodia-manipal-online-mba-in-human-resource-management/` (**Working**)
- **Programs Listing (`/programs/`)**:
  - Program card links: `href="#"` (**Broken**; fallback `rawPrograms` lacks slug property, leading to hash href).
- **Specializations Listing (`/specializations/`)**:
  - Specialization card link: `/nodia-manipal-online-mba-in-human-resource-management/` (**Working**)
- **Blog Listing (`/blog/`)**:
  - Blog post link: `/blog/untitled/` (**Working**)
- **Server Serving Status**:
  - All routing links (like `/programs/`, `/blog/untitled/`) return `{"detail":"Not Found"}` when requested on port 8000 because they are not registered endpoints on the FastAPI backend.

---

## SECTION 12 — Asset Audit

Assets in `Assets/images` compared to build output `build/assets/images`:

- **Copied Assets**:
  - `nodia-manipal-online-mba-in-human-resource-management-hero.png` (Successfully copied to build)
  - `university-hero.jpg` (Successfully copied to build)
  - `blog-untitled-hero.jpg` (Successfully copied to build)
- **Missing / Unused Assets**:
  - No assets are missing from copy.
- **Broken References**:
  - Since the runtime `support.js` fails to execute, raw image links inside templates like `<img src="{{ p.image }}">` remain unrendered or show empty images.

---

## SECTION 13 — End-to-End Build Trace

Tracing the flow of one selected workspace (`nodia`):

### 13.1 University Page
1. **Source**: `University/source.json` contains university descriptors like name ("Noida International"), starting fee, modes, and faqs.
2. **Compile**: `compiler.py` reads `source.json` -> calls `UniversityTransformer` -> enriches data variables -> runs Jinja2 on `templates/university.html` -> outputs `University/university.html`.
3. **Build Export**: `builder.py` reads `University/university.html` -> rewrites links -> writes output file `build/index.html`.
4. **Route**: Evaluates mapping `/` -> serves `build/index.html`.
5. **Browser Output**: Renders raw html. Requests `/assets/support.js` -> fails with 404 -> raw template is displayed.

### 13.2 Course Page
1. **Source**: None exists in the workspace.
2. **Compile / Export / Route**: Mapped default/stub objects are bypassed or skipped.

### 13.3 Specialization Page
1. **Source**: `Specializations/nodia-manipal-online-mba-in-human-resource-management/source.json` contains specialization name and parent course slug.
2. **Compile**: `compiler.py` runs `SpecializationTransformer` -> enriches syllabus parser data -> renders `templates/specialization.html` -> outputs `Specializations/.../specialization.html`.
3. **Build Export**: `builder.py` rewrites link definitions -> writes file `build/nodia-manipal-online-mba-in-human-resource-management/index.html`.
4. **Route**: Serves clean path `/nodia-manipal-online-mba-in-human-resource-management`.

### 13.4 Blog Page
1. **Source**: `Blogs/untitled/source.json` contains article details and author meta information.
2. **Compile**: `compiler.py` runs `BlogTransformer` -> renders `templates/blog.html` -> outputs `Blogs/untitled/blog.html`.
3. **Build Export**: `builder.py` rewrites paths -> writes `build/blog/untitled/index.html`.
4. **Route**: Serves path `/blog/untitled`.

---

## SECTION 14 — Root Cause Analysis

### 14.1 Why listing pages show remaining placeholders
- **Root Cause A**: Mismatching script assets route. The builder rewrites script imports to point to absolute path `/assets/support.js`. The FastAPI developer backend does not mount static files or register `/assets/support.js` (only `/support.js` is registered). This results in a 404 error, blocking runtime execution.
- **Root Cause B**: Fallback mockup data mismatch. In the absence of course sources in the workspace database, the Jinja template compiler injects fallback mock programs (`uni_programs` in `engine.py`). This fallback data has key definitions (`dur`, `elig`, `d`) that do not match the expected keys in listing templates (`duration`, `eligibility`, `description`). This mismatch breaks data-binding.

### 14.2 Why clean routes return `{"detail":"Not Found"}`
- **Root Cause**: Missing static mount wildcards. The builder maps clean routes like `/programs` or `/blog/untitled` by organizing files under `/programs/index.html`, etc. But the FastAPI dev server is only configured to route absolute API targets and `/build-file` queries. It doesn't host static files under clean URLs directly on the server root.

### 14.3 Mapped Failure Matrix
| Component / Layer | Nature of Bug | Effect on Final Page |
| :--- | :--- | :--- |
| **FastAPI Backend (Router)** | Missing static files mounting & routing | Serves 404 detail on clean URLs |
| **Builder Pipeline** | Asset script rewrite mapping | Generates 404 route for assets/support.js |
| **Jinja Engine (engine.py)** | Fallback data structure key mismatch | Mismatches key variables (`dur`/`duration`) |

---

## SECTION 15 — Final Findings

### 15.1 Working (`✓`)
- Ingestion of ACF JSON inputs from parsed document DOCX models (`POST /parse-docx`).
- Tree metadata generation and tree scanning logic (`GET /workspace-tree`).
- Creation of workspaces and initializing list pages on local server filesystem.
- Static zip compilation and download pipelines (`GET /download-build`).

### 15.2 Broken (`✗`)
- Serving built files correctly: Absolute script path `/assets/support.js` fails with a 404 response on the FastAPI backend.
- Fallback data structures in `engine.py` contain key structures that mismatch the templates.
- Clean routing URLs mapping directly on the dev server root.

### 15.3 Risk Areas (`⚠`)
- **Dangling Course References**: Workspace data references specialization course parent paths (`nodia-online-mba`) that do not exist, leading to warning structures on build pipeline runs.
- **CDN Dependency**: `support.js` requires an active internet connection to load React and ReactDOM libraries from CDN `unpkg.com`. In local offline environments, rendering will fail.

### 15.4 Recommended Fix Order (Investigation Only - DO NOT IMPLEMENT)
1. **Asset Endpoint Fix**: Add a route mapping in `backend/main.py` to serve `/assets/support.js` (in addition to `/support.js`) or mount `/assets` statically.
2. **Wildcard Route Serving**: Mount static directory configurations in `backend/main.py` so requests to `/programs`, `/blog/untitled`, etc. are correctly routed to their respective `index.html` files inside the build directory.
3. **Fallback Schema Alignment**: Align the dictionary keys in `uni_programs` within `backend/renderer/engine.py` to match the exact properties used in listing templates:
   - Rename `dur` to `duration`.
   - Rename `elig` to `eligibility`.
   - Rename `d` to `description`.
   - Add missing properties (`mode` and `slug`).
4. **Offline Resilience**: Package React and ReactDOM local scripts inside `support.js` or copy them to `build/assets/` to remove external CDN dependence.
