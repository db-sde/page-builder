/**
 * Decode and normalize the Base64 URL-safe JSON payload from the 'd' query parameter.
 * Handles fallbacks if uni_name, program_name, or specialization_name are missing or if
 * the payload only contains slugs.
 * 
 * @param {string} dParam - Base64 encoded payload string
 * @returns {object|null} Decoded and normalized payload, or null if invalid
 */
export function decodePayload(dParam) {
  if (!dParam) return null;
  try {
    // Base64 URL-safe decode
    let base64 = dParam.replace(/-/g, '+').replace(/_/g, '/');
    
    // Add padding if necessary
    while (base64.length % 4) {
      base64 += '=';
    }
    
    const decodedStr = atob(base64);
    const raw = JSON.parse(decodedStr);
    
    // 1. Normalize University
    const uni = raw.uni || '';
    let uni_name = raw.uni_name || '';
    if (!uni_name && uni) {
      const uniMap = {
        'nmims': 'NMIMS Online',
        'chandigarh-university': 'Chandigarh University Online',
        'nodia': 'Nodia Online',
        'test-1': 'Test 1 Online',
        'sharda': 'Sharda University Online',
        'srm': 'SRM University Online'
      };
      
      let mapped = uniMap[uni.toLowerCase()];
      if (!mapped) {
        if (uni.length <= 4) {
          mapped = uni.toUpperCase() + ' Online';
        } else {
          mapped = uni.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) + ' Online';
        }
      }
      uni_name = mapped;
    }
    
    const logo_letter = raw.logo_letter || (uni_name ? uni_name.charAt(0).toUpperCase() : 'U');
    
    // 2. Normalize Program
    const program = raw.program || '';
    let program_name = raw.program_name || '';
    if (!program_name && program) {
      program_name = program.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
      program_name = program_name
        .replace(/\bMba\b/gi, 'MBA')
        .replace(/\bMca\b/gi, 'MCA')
        .replace(/\bMsc\b/gi, 'MSc')
        .replace(/\bBba\b/gi, 'BBA')
        .replace(/\bBca\b/gi, 'BCA')
        .replace(/\bBcom\b/gi, 'B.Com')
        .replace(/\bMcom\b/gi, 'M.Com');
    }
    
    // 3. Normalize Specialization
    const specialization = raw.specialization || '';
    let specialization_name = raw.specialization_name || '';
    if (!specialization_name && specialization) {
      let cleanSpec = specialization;
      // Strip program prefix if any
      if (program && specialization.startsWith(program + '-')) {
        cleanSpec = specialization.substring(program.length + 1);
      }
      // Strip university prefix if any
      if (uni && cleanSpec.startsWith(uni + '-')) {
        cleanSpec = cleanSpec.substring(uni.length + 1);
      }
      specialization_name = cleanSpec.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }
    
    // 4. Normalize Source
    const source = raw.source || 'enquiry';
    
    // 5. Normalize Return URL
    let return_url = raw.return_url || '';
    if (!return_url) {
      if (typeof document !== 'undefined' && document.referrer) {
        return_url = document.referrer;
      } else if (uni) {
        // Fallback relative home
        return_url = `/${uni}.html`;
      } else {
        return_url = '#';
      }
    }
    
    // 6. Normalize Phone number (optional field for Call CTA)
    const phoneMap = {
      'nmims': '1800-102-5136',
      'chandigarh-university': '1800-1213-888',
      'nodia': '1800-102-5136',
      'test-1': '1800-102-5136',
      'sharda': '1800-102-6999',
      'srm': '1800-102-5136'
    };
    const phone = raw.phone || phoneMap[uni.toLowerCase()] || '';
    
    return {
      uni,
      uni_name,
      logo_letter,
      program,
      program_name,
      specialization,
      specialization_name,
      source,
      return_url,
      phone
    };
  } catch (e) {
    console.error('Failed to decode payload:', e);
    return null;
  }
}
