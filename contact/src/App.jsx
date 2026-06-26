import { useState, useEffect } from 'react';
import { 
  MapPin, 
  Mail, 
  Phone, 
  ArrowLeft, 
  CheckCircle2, 
  Plus, 
  Minus, 
  Clock, 
  AlertCircle, 
  Send,
  MessageSquare
} from 'lucide-react';
import { decodePayload } from './utils/payload';
import { submitLead } from './services/webhook';
import './App.css';

function App() {
  const [payload, setPayload] = useState({
    uni: '',
    uni_name: 'DegreeBaba Online',
    logo_letter: 'D',
    program: '',
    program_name: '',
    specialization: '',
    specialization_name: '',
    source: 'enquiry',
    phone: ''
  });

  const [formValues, setFormValues] = useState({
    fullName: '',
    email: '',
    mobileNumber: '',
    city: '',
    message: ''
  });

  const [faqOpen, setFaqOpen] = useState({
    0: true,
    1: false,
    2: false,
    3: false
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [hasBackButton, setHasBackButton] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const dParam = params.get('d');
    const decoded = decodePayload(dParam);
    if (decoded) {
      setPayload(decoded);
    }

    // Capture and store browser referrer
    if (typeof document !== 'undefined' && document.referrer) {
      if (!sessionStorage.getItem("return_url") && !document.referrer.includes(window.location.host)) {
        sessionStorage.setItem("return_url", document.referrer);
      }
    }
  }, []);

  // Determine back button visibility client-side
  useEffect(() => {
    const storedUrl = sessionStorage.getItem("return_url");
    if ((storedUrl && storedUrl !== '#') || (typeof window !== 'undefined' && window.history.length > 1)) {
      setHasBackButton(true);
    }
  }, [payload]);

  // Set page document title based on university and program context
  useEffect(() => {
    if (payload.uni_name) {
      let title = `${payload.uni_name} Admissions Portal`;
      if (payload.program_name) {
        title = `${payload.program_name} | ${payload.uni_name} Admissions`;
      }
      document.title = title;
    }
  }, [payload]);

  const toggleFaq = (index) => {
    setFaqOpen(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormValues(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitError(null);
    
    // Basic validations
    if (!formValues.fullName.trim()) {
      setSubmitError('Please enter your full name.');
      return;
    }
    if (!formValues.email.trim() || !/\S+@\S+\.\S+/.test(formValues.email)) {
      setSubmitError('Please enter a valid email address.');
      return;
    }
    if (!formValues.mobileNumber.trim() || formValues.mobileNumber.length < 10) {
      setSubmitError('Please enter a valid 10-digit mobile number.');
      return;
    }

    setIsSubmitting(true);
    try {
      await submitLead(formValues, payload);
      setSubmitSuccess(true);
    } catch (err) {
      setSubmitError('Unable to submit right now. Please try again in a few moments.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setFormValues({
      fullName: '',
      email: '',
      mobileNumber: '',
      city: '',
      message: ''
    });
    setSubmitSuccess(false);
    setSubmitError(null);
  };

  const getUniEmail = () => {
    if (!payload.uni_name) return 'admissions@degreebaba.com';
    const clean = payload.uni_name
      .toLowerCase()
      .replace(/online/g, '')
      .replace(/university/g, '')
      .replace(/[^a-z0-9]/g, '');
    return `admissions@${clean || 'degreebaba'}online.edu`;
  };

  // Generate dynamic hero titles based on source/action
  const getHeroTitle = () => {
    const src = (payload.source || 'enquiry').toLowerCase();
    const courseText = payload.program_name ? ` ${payload.program_name}` : 'Online Degree';
    const specText = payload.specialization_name ? ` - ${payload.specialization_name}` : '';
    const fullProgram = `${courseText}${specText}`;

    if (src === 'apply') {
      return `Apply for ${fullProgram}`;
    } else if (src === 'brochure') {
      return `Download ${fullProgram} Brochure`;
    } else if (src === 'enquiry') {
      return `Speak with an Admissions Advisor`;
    } else if (src === 'counselling') {
      return `Book a Free Counselling Session`;
    } else if (src === 'fees') {
      return `Get Fee Quote for ${fullProgram}`;
    }
    return `Speak with an Admissions Advisor`;
  };

  const getFormTitle = () => {
    const src = (payload.source || 'enquiry').toLowerCase();
    if (src === 'apply') return 'Start your application';
    if (src === 'brochure') return 'Request syllabus & brochure';
    if (src === 'fees') return 'Get fee structure online';
    if (src === 'counselling') return 'Book counselling call';
    return 'Request a callback & brochure';
  };

  const getFormButtonLabel = () => {
    const src = (payload.source || 'enquiry').toLowerCase();
    if (src === 'apply') return 'Submit Application';
    if (src === 'brochure') return 'Download Syllabus & Brochure';
    if (src === 'fees') return 'Get Fee Structure';
    if (src === 'counselling') return 'Confirm Counselling Booking';
    return 'Request Callback & Brochure';
  };

  const returnToWebsite = () => {
    const storedUrl = sessionStorage.getItem("return_url");
    if (storedUrl && storedUrl !== '#') {
      window.location.href = storedUrl;
    } else if (typeof window !== 'undefined' && window.history.length > 1) {
      window.history.back();
    }
  };

  const faqData = [
    { 
      q: 'How soon will I hear back after submitting the form?', 
      a: 'An admissions advisor typically calls within one working hour during counselling hours (Mon–Sat, 9 AM – 8 PM). Outside these hours, you will hear from us the next morning.' 
    },
    { 
      q: 'Can I apply directly without speaking to anyone?', 
      a: 'Yes. You can register and apply on the university online portal directly. This form gets you the official brochure, detailed semester fees, and a guided counsellor callback first.' 
    },
    { 
      q: 'Is there a processing fee for submitting this form?', 
      a: 'No. Requesting a brochure, fee quote, or counsellor callback is completely free. Processing or enrollment fees apply only when you register for admission.' 
    },
    { 
      q: 'What documents will I need to submit for admission?', 
      a: 'You will need to scan and upload your high school transcripts, graduation marksheets, a government-issued photo ID, and passport-size photographs.' 
    }
  ];

  return (
    <div className="bg-[#F6F4FB] text-[#434346] min-h-screen flex flex-col font-sans antialiased selection:bg-[#FF5C35] selection:text-[#1C1B22] leading-relaxed">
      
      {/* ===== TOP BAR ===== */}
      <div className="bg-[#6B4FC9] text-[#C9BEEC] text-xs">
        <div className="max-w-[1180px] mx-auto px-5 py-2 flex items-center justify-between">
          <span>Admissions open for the 2026 batch · Limited seats</span>
          <div className="hidden sm:flex items-center gap-5">
            <span>Official Admissions Desk</span>
            <span className="h-3 w-[1px] bg-white/20"></span>
            <span className="text-white font-semibold">UGC Approved Degrees</span>
          </div>
        </div>
      </div>

      {/* ===== HEADER / NAVBAR ===== */}
      <header className="bg-white border-b border-[#E9E5F2] sticky top-0 z-50 shadow-xs">
        <div className="max-w-[1180px] mx-auto px-5 py-3 flex items-center justify-between">
          {/* Logo Brand Context */}
          <div className="flex items-center gap-3">
            <div className="leading-[1.04]">
              <div className="font-extrabold text-sm sm:text-lg text-[#1C1B22] whitespace-nowrap">
                {payload.uni_name} <span className="text-[#FF5C35]">Admissions</span>
              </div>
              <div className="hidden sm:block text-[9px] tracking-widest text-[#9A93A8] font-bold uppercase mt-0.5">
                Distance &amp; Online Education
              </div>
            </div>
          </div>

          {/* Simplified Navigation */}
          <div className="flex items-center gap-4">
            {hasBackButton && (
              <button 
                onClick={returnToWebsite}
                className="text-sm font-semibold text-[#6E6A78] hover:text-[#1C1B22] flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <ArrowLeft size={16} />
                <span className="hidden sm:inline">Back to Website</span>
              </button>
            )}
            <a 
              href="#form-section" 
              className="bg-[#1C1B22] text-[#F3C77C] hover:bg-[#2C2A35] text-sm font-bold px-4 py-2 rounded-lg transition-colors shadow-xs"
            >
              Apply Now
            </a>
          </div>
        </div>
      </header>
 
      {/* ===== HERO SECTION ===== */}
      <div className="bg-white border-b border-[#ECE8F6] pt-12 pb-24 md:pt-16 md:pb-32 text-[#434346]">
        <div className="max-w-[1180px] mx-auto px-5">
          <div className="text-xs text-[#9A93A8] mb-3 flex items-center gap-1.5">
            {hasBackButton ? (
              <span onClick={returnToWebsite} className="hover:underline cursor-pointer">Home</span>
            ) : (
              <span>Home</span>
            )}
            <span>›</span>
            <span>Contact &amp; Admissions</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-[#5737C5] leading-tight max-w-[800px]">
            {getHeroTitle()}
          </h1>
          <p className="text-base text-[#6E6A78] max-w-[650px] mt-3">
            Submit your callback request, download the official course curriculum, or book a counselling call with an advisor. Desk response time is typically under one working hour.
          </p>
        </div>
      </div>

      {/* ===== CONTENT SECTION (FORM + DETAILS) ===== */}
      <div id="form-section" className="max-w-[1180px] mx-auto px-5 w-full -mt-16 md:-mt-20 flex-1 grid grid-cols-1 lg:grid-cols-[1.3fr_0.9fr] gap-6 items-start pb-16">
        
        {/* LEFT COLUMN: LEAD FORM */}
        <div className="bg-white border border-[#E9E5F2] rounded-2xl p-6 md:p-8 shadow-lg">
          {submitSuccess ? (
            /* SUCCESS STATE SCREEN */
            <div className="text-center py-10 px-4">
              <div className="w-16 h-16 rounded-full bg-[#E7F7EE] text-[#1A9D57] flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 size={36} />
              </div>
              <h2 className="text-3xl font-extrabold text-[#1C1B22] mb-4">✓ Thank You</h2>
              <p className="text-base font-semibold text-[#1a9d57] mb-2">
                Your request has been submitted successfully.
              </p>
              <p className="text-[#6E6A78] text-sm md:text-base max-w-[420px] mx-auto mb-8">
                An admissions advisor will contact you shortly.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
                {hasBackButton && (
                  <button 
                    onClick={returnToWebsite}
                    className="w-full sm:w-auto bg-[#6B4FC9] text-white hover:bg-[#5737C5] font-bold text-sm px-6 py-3 rounded-lg transition-colors cursor-pointer"
                  >
                    Back to Website
                  </button>
                )}
                <button 
                  onClick={handleReset}
                  className="w-full sm:w-auto bg-[#F6F4FB] text-[#1C1B22] border border-[#E9E5F2] hover:bg-[#ECE8F6] font-bold text-sm px-6 py-3 rounded-lg transition-colors cursor-pointer"
                >
                  Submit Another Enquiry
                </button>
              </div>
            </div>
          ) : (
            /* FORM STATE SCREEN */
            <div>
              <h2 className="text-xl font-extrabold text-[#1C1B22]">{getFormTitle()}</h2>
              <p className="text-xs text-[#6E6A78] mt-1">Complete your registration to receive official fee sheets and syllabus files.</p>
              
              {submitError && (
                <div className="mt-4 bg-[#FFF0EB] border border-[#FFD3C6] rounded-lg p-3 text-sm text-[#9E3B22] flex items-center gap-2.5">
                  <AlertCircle size={18} className="flex-shrink-0" />
                  <span>{submitError}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Full Name */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#434346]">Full Name *</label>
                    <input 
                      type="text" 
                      name="fullName"
                      value={formValues.fullName}
                      onChange={handleInputChange}
                      placeholder="Your name"
                      required
                      className="w-full border border-[#E9E5F2] rounded-lg h-12 px-3.5 text-sm bg-[#FBFAFE]"
                    />
                  </div>

                  {/* Email */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#434346]">Email Address *</label>
                    <input 
                      type="email" 
                      name="email"
                      value={formValues.email}
                      onChange={handleInputChange}
                      placeholder="you@email.com"
                      required
                      className="w-full border border-[#E9E5F2] rounded-lg h-12 px-3.5 text-sm bg-[#FBFAFE]"
                    />
                  </div>

                  {/* Mobile Number */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#434346]">Mobile Number *</label>
                    <input 
                      type="tel" 
                      name="mobileNumber"
                      value={formValues.mobileNumber}
                      onChange={handleInputChange}
                      placeholder="+91 00000 00000"
                      required
                      className="w-full border border-[#E9E5F2] rounded-lg h-12 px-3.5 text-sm bg-[#FBFAFE]"
                    />
                  </div>

                  {/* City */}
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs font-bold text-[#434346]">City (Optional)</label>
                    <input 
                      type="text" 
                      name="city"
                      value={formValues.city}
                      onChange={handleInputChange}
                      placeholder="Your city"
                      className="w-full border border-[#E9E5F2] rounded-lg h-12 px-3.5 text-sm bg-[#FBFAFE]"
                    />
                  </div>
                </div>

                {/* Program representation (auto-filled and displayed cleanly) */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-[#434346]">Program of Interest</label>
                  <input 
                    type="text" 
                    readOnly
                    disabled
                    value={payload.specialization_name 
                      ? `${payload.program_name} - ${payload.specialization_name}` 
                      : (payload.program_name || 'General Admission Enquiry')}
                    className="w-full border border-[#E9E5F2] rounded-lg h-12 px-3.5 text-sm bg-[#ECE7F5] text-[#1C1B22] font-semibold cursor-not-allowed outline-none select-none"
                  />
                </div>

                {/* Message */}
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-bold text-[#434346]">Message (Optional)</label>
                  <textarea 
                    rows={3} 
                    name="message"
                    value={formValues.message}
                    onChange={handleInputChange}
                    placeholder="Tell us about your background or questions here"
                    className="w-full border border-[#E9E5F2] rounded-lg p-3.5 text-sm bg-[#FBFAFE] resize-none"
                  />
                </div>

                {/* Submit button */}
                <button 
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full bg-[#1C1B22] text-[#F3C77C] border-none rounded-lg p-4 font-bold text-base cursor-pointer hover:bg-[#2C2A35] transition-all flex items-center justify-center gap-2 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send size={16} />
                  {isSubmitting ? 'Submitting Request...' : getFormButtonLabel()}
                </button>

                <div className="flex items-center justify-center gap-2 mt-3 text-xs text-[#9A93A8]">
                  <span>Your details are completely safe with us · Official Admissions Channel</span>
                </div>
              </form>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: CONTACT DETAILS CARD */}
        <div className="flex flex-col gap-5">
          <div className="bg-white border border-[#E9E5F2] rounded-2xl p-6 shadow-sm">
            <h3 className="text-base font-extrabold text-[#1C1B22] mb-4">Admissions Desk</h3>
            
            <div className="flex flex-col gap-4">
              
              {/* Phone details (Only if phone is available) */}
              {payload.phone && (
                <div className="flex gap-3.5 items-start">
                  <div className="w-10 h-10 rounded-xl bg-[#FFE7E0] text-[#E0431F] flex items-center justify-center flex-shrink-0">
                    <Phone size={18} />
                  </div>
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-wider text-[#9A93A8]">Helpline Number</div>
                    <div className="text-sm font-semibold text-[#434346] mt-0.5">
                      {payload.phone}
                    </div>
                  </div>
                </div>
              )}

              {/* Email details */}
              <div className="flex gap-3.5 items-start">
                <div className="w-10 h-10 rounded-xl bg-[#FFE7E0] text-[#E0431F] flex items-center justify-center flex-shrink-0">
                  <Mail size={18} />
                </div>
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[#9A93A8]">Official Email</div>
                  <div className="text-sm font-semibold text-[#434346] mt-0.5 break-all">
                    {getUniEmail()}
                  </div>
                </div>
              </div>

              {/* Office hours details */}
              <div className="flex gap-3.5 items-start">
                <div className="w-10 h-10 rounded-xl bg-[#FFE7E0] text-[#E0431F] flex items-center justify-center flex-shrink-0">
                  <Clock size={18} />
                </div>
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[#9A93A8]">Working Hours</div>
                  <div className="text-sm font-semibold text-[#434346] mt-0.5">
                    Mon–Sat · 9:00 AM – 8:00 PM
                  </div>
                </div>
              </div>

              {/* Visit location (Only if address is available) */}
              <div className="flex gap-3.5 items-start">
                <div className="w-10 h-10 rounded-xl bg-[#FFE7E0] text-[#E0431F] flex items-center justify-center flex-shrink-0">
                  <MapPin size={18} />
                </div>
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[#9A93A8]">Campus Address</div>
                  <div className="text-sm font-semibold text-[#434346] mt-0.5 leading-relaxed">
                    {payload.uni === 'nmims' 
                      ? 'V. L. Mehta Road, Vile Parle (W), Mumbai 400056' 
                      : `${payload.uni_name} Corporate Campus, Admissions Block`}
                  </div>
                </div>
              </div>
            </div>

            {/* CTAs */}
            <div className="flex gap-3 mt-6">
              {payload.phone && (
                <a 
                  href={`tel:${payload.phone.replace(/[^0-9+]/g, '')}`}
                  className="flex-1 text-center bg-[#6B4FC9] text-white hover:bg-[#5737C5] font-bold text-sm h-12 rounded-lg flex items-center justify-center gap-2 transition-colors cursor-pointer"
                >
                  <Phone size={16} />
                  Call Now
                </a>
              )}
              <a 
                href="https://wa.me/911800102513" 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex-1 text-center bg-[#25D366] text-[#06301a] hover:bg-[#20ba5a] font-bold text-sm h-12 rounded-lg flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                <MessageSquare size={16} />
                WhatsApp
              </a>
            </div>
          </div>

        </div>

      </div>

      {/* ===== ADMISSIONS STATUS STRIP ===== */}
      <div className="max-w-[1180px] mx-auto px-5 w-full mb-12">
        <div className="bg-white border border-[#E9E5F2] rounded-xl grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[#E9E5F2]">
          <div className="p-5 flex flex-col justify-center">
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#9A93A8]">Support Availability</div>
            <div className="text-sm font-bold text-[#1C1B22] mt-1">Mon–Sat · 9 AM – 8 PM</div>
          </div>
          <div className="p-5 flex flex-col justify-center">
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#9A93A8]">Average Response</div>
            <div className="text-sm font-bold text-[#1C1B22] mt-1">Under 1 working hour</div>
          </div>
          <div className="p-5 flex flex-col justify-center">
            <div className="text-[10px] font-bold uppercase tracking-wider text-[#9A93A8]">Enrollment Desk</div>
            <div className="text-sm font-bold text-[#1a9d57] mt-1 flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-[#1a9d57] inline-block animate-pulse"></span>
              Open for 2026 batch
            </div>
          </div>
        </div>
      </div>

      {/* ===== FAQ ACCORDION SECTION ===== */}
      <div className="max-w-[1180px] mx-auto px-5 w-full mb-16">
        <div className="text-center mb-8">
          <div className="text-xs font-bold uppercase tracking-widest text-[#FF5C35]">Admissions FAQ</div>
          <h2 className="text-2xl md:text-3xl font-extrabold text-[#1C1B22] mt-2">Frequently Asked Questions</h2>
        </div>
        
        <div className="max-w-[760px] mx-auto bg-white border border-[#E9E5F2] rounded-2xl px-6 md:px-8 py-2 shadow-xs">
          {faqData.map((faq, i) => (
            <div key={i} className="border-b border-[#ECE7F5] last:border-b-0 py-4">
              <button 
                onClick={() => toggleFaq(i)}
                className="w-full flex items-center justify-between text-left font-bold text-sm md:text-base text-[#1C1B22] hover:text-[#5737C5] transition-colors cursor-pointer focus:outline-none"
              >
                <span>{faq.q}</span>
                <span className="text-[#FF5C35] flex-shrink-0 ml-4">
                  {faqOpen[i] ? <Minus size={18} /> : <Plus size={18} />}
                </span>
              </button>
              
              <div className={`mt-3 text-xs md:text-sm text-[#6E6A78] leading-relaxed transition-all duration-300 ${faqOpen[i] ? 'block' : 'hidden'}`}>
                {faq.a}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ===== FOOTER ===== */}
      <footer className="bg-[#6B4FC9] text-[#C9BEEC] pt-12 pb-6 px-5 mt-auto">
        <div className="max-w-[1180px] mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1.2fr] gap-8">
          
          {/* Column 1: Logo and details */}
          <div>
            <div className="flex items-center gap-2.5 mb-4">
              <div className="font-extrabold text-base text-white">
                {payload.uni_name.toLowerCase().endsWith('online') ? (
                  <>
                    {payload.uni_name.substring(0, payload.uni_name.length - 6).trim()}{' '}
                    <span className="text-[#FF5C35]">Online</span>
                  </>
                ) : (
                  <>
                    {payload.uni_name} <span className="text-[#FF5C35]">Online</span>
                  </>
                )}
              </div>
            </div>
            <p className="text-xs max-w-[300px] leading-relaxed text-[#C9BEEC]/80">
              UGC-entitled online degree programs, built for working professionals who want to grow without pausing their careers.
            </p>
          </div>

          {/* Column 2: Programs */}
          <div>
            <h4 className="text-white font-bold text-sm mb-3">Programs</h4>
            <div className="flex flex-col gap-2 text-xs">
              <span className="text-[#C9BEEC]/80 select-none">Online MBA</span>
              <span className="text-[#C9BEEC]/80 select-none">MBA Marketing</span>
              <span className="text-[#C9BEEC]/80 select-none">MBA Finance</span>
              <span className="text-[#C9BEEC]/80 select-none">MBA HR</span>
            </div>
          </div>

          {/* Column 3: Company */}
          <div>
            <h4 className="text-white font-bold text-sm mb-3">Company</h4>
            <div className="flex flex-col gap-2 text-xs">
              {hasBackButton ? (
                <button onClick={returnToWebsite} className="text-left hover:text-white transition-colors cursor-pointer">
                  Home
                </button>
              ) : (
                <span className="text-[#C9BEEC]/80 select-none">Home</span>
              )}
              <span className="text-[#C9BEEC]/80 select-none">Blog</span>
              <span className="text-[#C9BEEC]/80 select-none">Admissions</span>
              <span className="text-[#C9BEEC]/80 select-none">Contact Us</span>
            </div>
          </div>

          {/* Column 4: Get in touch */}
          <div>
            <h4 className="text-white font-bold text-sm mb-3">Get in Touch</h4>
            <div className="flex flex-col gap-2 text-xs">
              {payload.phone && (
                <span>Call: {payload.phone}</span>
              )}
              <span className="break-all">Email: {getUniEmail()}</span>
              <span>
                {payload.uni === 'nmims' 
                  ? 'V. L. Mehta Road, Vile Parle (W), Mumbai 400056' 
                  : `${payload.uni_name} Corporate Campus`}
              </span>
            </div>
          </div>

        </div>
        
        <div className="max-w-[1180px] mx-auto mt-10 pt-5 border-t border-[#3E2A7A] text-[11px] flex flex-col sm:flex-row items-center justify-between gap-4 text-[#C9BEEC]/60">
          <span>
            &copy; 2026 {payload.uni_name.toLowerCase().endsWith('online') 
              ? payload.uni_name 
              : `${payload.uni_name} Online`}. All rights reserved.
          </span>
          <div className="flex gap-4">
            <span>Privacy Policy</span>
            <span>Terms of Service</span>
            <span>Refund Policy</span>
          </div>
        </div>
      </footer>

    </div>
  );
}

export default App;
