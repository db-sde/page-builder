/**
 * Map payload source tags to user-friendly source labels for webhook submission.
 */
function mapSourceLabel(source) {
  const mapping = {
    'apply': 'Apply Now',
    'brochure': 'Download Brochure',
    'enquiry': 'Enquire Now',
    'fees': 'Get Fee Quote',
    'counselling': 'Book Counselling'
  };
  return mapping[source.toLowerCase()] || 'Web Lead';
}

/**
 * Submit lead details to CRM Webhook.
 * 
 * @param {object} formData - Form input values (name, email, mobile, city, message)
 * @param {object} payload - Decoded URL context variables (uni_name, program_name, specialization_name, source)
 * @returns {Promise<boolean>} Success status
 */
export async function submitLead(formData, payload) {
  const webhookUrl = import.meta.env.VITE_WEBHOOK_URL || 'https://erbicxhavmekqwwkcqcs.supabase.co/functions/v1/webhook-inbound';
  const apiKey = import.meta.env.VITE_WEBHOOK_API_KEY || 'whk_development_default';
  
  // Format program of interest display
  let courseDisplay = payload.program_name || 'General';
  let specDisplay = payload.specialization_name || '';
  
  const leadBody = {
    source: mapSourceLabel(payload.source || 'enquiry'),
    lead: {
      full_name: formData.fullName || '',
      mobile_number: formData.mobileNumber || '',
      email: formData.email || '',
      city: formData.city || '',
      state: '',
      country: 'India',
      company: '',
      course: courseDisplay,
      specialization: specDisplay,
      campaign_name: payload.uni_name || 'PageBuilder Online',
      campaign_id: '',
      adgroup_id: ''
    }
  };

  console.log('Sending Lead Webhook payload:', leadBody);

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': apiKey
      },
      body: JSON.stringify(leadBody)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`CRM Webhook submission failed with status ${response.status}:`, errorText);
      throw new Error(`Server returned error status ${response.status}`);
    }

    const responseData = await response.json().catch(() => ({}));
    console.log('CRM Webhook response data:', responseData);
    return true;
  } catch (error) {
    console.error('Error submitting lead to webhook:', error);
    throw error;
  }
}
