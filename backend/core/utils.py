import re
from html import unescape


def summarize_content(value: str, max_words: int = 120) -> str:
    """Return complete leading sentences suitable for compact page sections."""
    if value is None:
        return ""
    text = unescape(re.sub(r"<[^>]+>", " ", str(value)))
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+", text)
    summary: list[str] = []
    word_count = 0
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sentence_words = len(sentence.split())
        if summary and word_count + sentence_words > max_words:
            break
        summary.append(sentence)
        word_count += sentence_words

    return " ".join(summary) or text


def format_fee(amount_str: str) -> str:
    """
    Cleans a raw fee/amount string into a consistent '₹<amount>' format
    (or '' if it can't be parsed / is a non-value like 'NA').
    """
    if not amount_str:
        return ""
    s = str(amount_str).strip()
    if not s or s.upper() in ("NA", "N/A", "NIL", "FREE", "-", "--"):
        return ""
    
    # Strip any existing leading ₹ or INR symbols
    s = re.sub(r'^₹\s*', '', s).strip()
    s = re.sub(r'\bINR\b\s*', '', s, flags=re.IGNORECASE).strip()
    
    # Strip trailing garbage: /-, /--, /year, /sem etc
    s = re.sub(r'\s*/[-–]+.*$', '', s).strip()
    s = re.sub(r'\s*/\s*(year|sem|semester|month|mo).*$', '', s, flags=re.IGNORECASE).strip()
    
    # Strip any non-numeric/comma/dot characters remaining at end
    s = re.sub(r'[^0-9,.].*$', '', s).strip()
    if not s:
        return ""
    return f"₹{s}"


def read_parent_course_data(university_slug: str, parent_slug: str) -> dict:
    """
    Read the parent course's source.json `data` dict for a given workspace.
    Returns {} if parent_slug/university_slug is missing, the course
    doesn't exist, or the file can't be read/parsed.

    Single canonical implementation — previously this same "resolve
    course_dir via resolve_page_dir, open source.json, parse it" block was
    duplicated almost verbatim in three places: main.py's draft-save
    normalization, main.py's /generate-specialization-stub endpoint, and
    ingestion/ingest.py.
    """
    if not parent_slug or not university_slug:
        return {}
    try:
        import json
        from workspace.manager import resolve_page_dir
        course_dir = resolve_page_dir(university_slug, "course", parent_slug)
        course_json_path = course_dir / "source.json"
        if course_json_path.exists():
            course_data = json.loads(course_json_path.read_text(encoding="utf-8"))
            return course_data.get("data", {}) or {}
    except Exception:
        pass
    return {}


def resolve_parent_program_name(parent_course_data: dict, parent_slug: str) -> str:
    """
    Build the parent program's display name from its source data
    (program_name / course_name / title, combined to catch e.g. both
    "EMBA" and "Executive MBA" naming), falling back to a title-cased
    parent_slug if none of those fields are present.
    """
    names = [
        parent_course_data.get("program_name"),
        parent_course_data.get("course_name"),
        parent_course_data.get("title"),
    ]
    parent_program_name = " ".join(filter(None, names))
    if not parent_program_name:
        parent_program_name = parent_slug.replace("-", " ").title() if parent_slug else ""
    return parent_program_name


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

    # A publisher payload may already contain only the specialization name
    # (for example, "Banking & Insurance"). In that case there is no course
    # prefix to remove. Continuing into parent-token stripping would erase
    # legitimate words that also appear in a parent course title.
    prefix_tokens = (
        r"\b(online|mba|emba|bba|mca|bca|pgdm|pgdbm|bsc|msc|btech|mtech|"
        r"specialization|specialisation|program|course|track|pathway)\b"
    )
    if not re.search(prefix_tokens, name, flags=re.IGNORECASE):
        return name

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


def build_public_url(domain: str, slug: str, is_homepage: bool = False) -> str:
    """
    Format a public URL according to trailing-slash normalization rules.
    - Preserve the workspace's configured primary domain.
    - Homepage keeps trailing slash: https://www.domain.com/
    - All other pages must NOT have a trailing slash: https://www.domain.com/slug
    """
    domain = (domain or "").strip().rstrip("/")

    slug = (slug or "").strip()
    # Check if this route represents the homepage
    if is_homepage or not slug or slug == "/":
        return domain + "/" if domain else "/"

    # Format non-homepage route to be slashless
    clean_slug = "/" + slug.strip("/")
    return domain + clean_slug


def normalize_public_slug(slug: str, university_slug: str = "") -> str:
    """Return the public slug for a workspace-backed page."""
    slug = (slug or "").strip().strip("/")
    university_slug = (university_slug or "").strip().strip("/")
    if not slug or not university_slug:
        return slug

    # Numeric workspace suffixes are internal collision-avoidance details.
    # ``nmims-2-nmims-online-mba`` therefore publishes as
    # ``nmims-online-mba`` while an ordinary workspace slug is untouched.
    if re.search(r"-\d+$", university_slug):
        raw_prefix = university_slug + "-"
        if slug.startswith(raw_prefix):
            return slug[len(raw_prefix):]
    return slug


def build_public_route(page_type: str, slug: str = "", university_slug: str = "") -> str:
    """Build the canonical root-relative route for every supported page type."""
    page_type = (page_type or "").strip().lower()
    if page_type in ("homepage", "university"):
        return "/"
    if page_type == "programs_listing":
        return "/programs"
    if page_type == "specializations_listing":
        return "/specializations"
    if page_type == "blog_listing":
        return "/blog"

    public_slug = normalize_public_slug(slug, university_slug)
    if page_type == "blog":
        return f"/blog/{public_slug}" if public_slug else "/blog"
    return f"/{public_slug}" if public_slug else "/"
