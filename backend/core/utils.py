import re

def normalize_specialization_name(raw_name: str, parent_program_name: str, university_name: str = None) -> str:
    """
    Cleans the specialization name to keep only the academic specialization itself
    by removing parent program names, degree abbreviations, and university names.
    
    Examples:
      - parent="Online MBA", raw="MBA Finance" -> "Finance"
      - parent="Online MBA", raw="Online MBA Marketing" -> "Marketing"
      - parent="Online BBA", raw="BBA Business Analytics" -> "Business Analytics"
      - parent="Executive MBA (MBA WX)", raw="EMBA Applied Finance" -> "Applied Finance"
    """
    if not raw_name:
        return ""
    
    # 1. Standardize and lowercase
    name = raw_name.strip()
    parent = parent_program_name.strip() if parent_program_name else ""
    
    # Clean university name out first if provided
    if university_name:
        uni_pat = rf"\b{re.escape(university_name)}\b"
        name = re.sub(uni_pat, "", name, flags=re.IGNORECASE)
        parent = re.sub(uni_pat, "", parent, flags=re.IGNORECASE)
        
    # Standardize spaces
    name = re.sub(r"\s+", " ", name)
    parent = re.sub(r"\s+", " ", parent)
    
    # 2. Generate candidates to remove from the specialization name
    candidates = set()
    
    # Add parent program name as a whole candidate (lowercase)
    if parent:
        parent_lc = parent.lower()
        candidates.add(parent_lc)
        # Also clean parent of parenthesis contents
        parent_no_parens = re.sub(r"\(.*?\)", "", parent_lc).strip()
        if parent_no_parens:
            candidates.add(parent_no_parens)
            
        # Extract phrases from parent (words inside parens, words outside parens)
        phrases = [parent_no_parens]
        parens = re.findall(r"\((.*?)\)", parent_lc)
        phrases.extend(parens)
        
        for phrase in phrases:
            phrase = phrase.strip()
            if not phrase:
                continue
            candidates.add(phrase)
            
            # Split into individual words
            words = re.findall(r"[a-z0-9]+", phrase)
            if not words:
                continue
                
            # Add all individual words (except very generic ones like 'of', 'in', 'and')
            for w in words:
                if w not in ("of", "in", "and", "for", "with"):
                    candidates.add(w)
            
            # Generate acronyms
            # Acronym 1: First letter of each word
            acronym_1 = "".join(w[0] for w in words if w not in ("of", "in", "and", "for", "with"))
            if len(acronym_1) >= 2:
                candidates.add(acronym_1)
                
            # Acronym 2: First letter of non-acronym words + acronym words
            acronym_2_parts = []
            for w in words:
                if w in ("of", "in", "and", "for", "with"):
                    continue
                if w in ("mba", "bba", "mca", "bca", "pgdm", "pgdbm", "emba", "bsc", "msc", "btech", "mtech"):
                    acronym_2_parts.append(w)
                else:
                    acronym_2_parts.append(w[0])
            acronym_2 = "".join(acronym_2_parts)
            if len(acronym_2) >= 2:
                candidates.add(acronym_2)
                
            # Also standard acronyms like emba if 'executive' and 'mba' are present
            if "executive" in words and "mba" in words:
                candidates.add("emba")
                
    # Sort candidates by length descending so we remove longer matches first
    sorted_candidates = sorted(list(candidates), key=len, reverse=True)
    
    # We also want to strip noise words/prefixes at the start/end
    noise_patterns = [
        r"^\s*in\b",
        r"^\s*online\b",
        r"^\s*specialization\s*in\b",
        r"^\s*specialisation\s*in\b",
        r"^\s*specialization\b",
        r"^\s*specialisation\b",
        r"^\s*pathway\b",
        r"^\s*track\b",
        r"^\s*program\b",
        r"^\s*course\b",
    ]
    
    # We will repeatedly clean the string until it doesn't change
    current_name = name.lower()
    prev_name = None
    
    while current_name != prev_name:
        prev_name = current_name
        
        # 1. Try to strip each candidate from the start
        for cand in sorted_candidates:
            cand = cand.strip()
            if not cand:
                continue
            pattern = rf"^{re.escape(cand)}\b"
            current_name = re.sub(pattern, "", current_name).strip()
            
        # 2. Try to strip noise patterns from start or end
        for noise in noise_patterns:
            current_name = re.sub(noise, "", current_name, flags=re.IGNORECASE).strip()
            current_name = re.sub(rf"\b{noise.replace('^', '')}$", "", current_name, flags=re.IGNORECASE).strip()
            
        # Clean up any leading/trailing non-alphanumeric except spaces
        current_name = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", current_name).strip()
        
    return current_name.title()
