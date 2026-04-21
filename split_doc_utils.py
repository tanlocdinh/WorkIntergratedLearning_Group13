from typing import List, Dict
import math
import re

# -----------------------------
# Normalize Headers
# -----------------------------
def normalize_header(header):
    """
    Normalize header by collapsing whitespace and filtering out non-header patterns.
    Returns empty string if text doesn't look like a valid header.
    """
    if not header:
        return ""
    
    normalized = re.sub(r'\s+', ' ', header).strip()
    
    # Filter out obvious non-header patterns:
    # 1. Starts with symbols that headers wouldn't use: (, [, {, ", ', -, •, �, etc.
    if normalized and normalized[0] in '([{"\'-•–—*�□▪◦○●':
        return ""
    
    # 2. Starts with numbered list markers (e.g., "8. Item", "8) Item", "10. Previous")
    if re.match(r'^\d+[.)\]]\s', normalized):
        return ""
    
    # 3. Starts with lowercase (likely continuation of previous sentence)
    if normalized and normalized[0].islower():
        return ""
    
    # 4. Contains multiple numbered items (body content, not a header)
    numbered_items = re.findall(r'\d+[.)\]]', normalized)
    if len(numbered_items) > 1:
        return ""
    
    # 5. Contains sentence-like structure (verbs, articles) - headers are titles/identifiers
    # Look for common sentence indicators: "of the", "will", "has", "was", "are", etc.
    sentence_indicators = r'\b(of\s+the|in\s+the|on\s+the|for\s+the|will|has|have|had|was|were|are|is|be|been)\b'
    if re.search(sentence_indicators, normalized, re.IGNORECASE):
        return ""
    
    # 6. Contains common document section phrases - these are section headings, not page headers
    section_phrases = r'\b(Table\s+of\s+Contents|Chapter|Appendix|References|Bibliography|Index|Abstract|Introduction|Conclusion|Summary|Acknowledgments?|'
    section_phrases += r'Protocol\s+Summary|Study\s+(Objectives?|Design|Population|Procedures?|Schedule)|'
    section_phrases += r'Eligibility\s+Criteria|Treatment\s+Plan|Safety\s+Monitoring|Statistical\s+Analysis|'
    section_phrases += r'(Inclusion|Exclusion)\s+Criteria|(Primary|Secondary)\s+Endpoint|Outcome\s+Measures?|'
    section_phrases += r'Adverse\s+Events?|Data\s+Collection|Informed\s+Consent|Background|Rationale|Methods?|Results?|Discussion)\b'
    if re.search(section_phrases, normalized, re.IGNORECASE):
        return ""
    
    return normalized

def truncate_logical(text, max_len=250):
    """
    Truncate a string logically at the first strong punctuation, preferring '.'
    over other punctuation, never exceeding max_len, and never cutting inside
    parentheses, brackets, or braces. For headers, stops at first sentence.

    Parameters:
        text (str): Input string.
        max_len (int): Maximum allowed length (default 250).

    Returns:
        str: Logically truncated string.
    """
    if not text:
        return ""

    # For header detection, prefer stopping at first complete sentence (max 150 chars)
    # to avoid treating long body text as headers
    header_max = min(max_len, 150)
    trunc_text = text[:header_max].strip()

    # Truncate at first sentence ending (period, exclamation, or question mark)
    # This helps identify true headers which are typically short, complete statements
    punct_match = re.search(r'[.!?]', trunc_text)
    if punct_match:
        cut_index = punct_match.start() + 1
        # Ensure not inside parentheses/brackets/braces
        segment = trunc_text[:cut_index]
        if (segment.count('(') == segment.count(')') and
            segment.count('[') == segment.count(']') and
            segment.count('{') == segment.count('}')):
            return segment.strip()

    # If no sentence ending found in first 150 chars, likely body text not a header
    # Return shorter segment (up to 100 chars) to avoid long body text as headers
    if len(trunc_text) > 100:
        return trunc_text[:100].strip()

    # Fallback: return truncated string
    return trunc_text

def normalise(h):
    """Return header stripped, uppercase, no trailing numbers or roman numerals"""
    h = h.strip().upper()
    h = re.sub(r'\b\d+\b$', '', h)          # remove trailing digits
    h = re.sub(r'\b[IVXLCDM]+\b$', '', h)   # remove trailing roman numerals
    h = re.sub(r'\s+', ' ', h)              # collapse spaces
    return h.strip()

# -----------------------------
# Coverage Calculation
# -----------------------------
def header_coverage(doc_ranges: List[Dict]) -> List[Dict]:
    """Calculate coverage % for each doc_range (round up)."""
    if not doc_ranges:
        return []

    result = [entry.copy() for entry in doc_ranges]
    total_pages = result[-1]['end_page']
    for doc in result:
        page_count = doc['end_page'] - doc['start_page'] + 1
        doc['coverage %'] = math.ceil(page_count * 100 / total_pages) if total_pages else 0
    return result

def highest_coverage(doc_ranges: List[Dict], exclude_first=True) -> int:
    """Return index of highest coverage %, optionally excluding first entry."""
    start = 1 if exclude_first else 0
    if len(doc_ranges) <= start:
        return 0
    return max(range(start, len(doc_ranges)), key=lambda i: doc_ranges[i].get('coverage %', 0))

# -----------------------------
# Collapse consecutive '~~n/a~~'
# -----------------------------
def collapse_headers(doc_ranges: List[Dict]) -> List[Dict]:
    """Merge consecutive '~~n/a~~' into previous non-n/a entry."""
    if not doc_ranges:
        return []
    collapsed = []
    n = len(doc_ranges)
    i = 0
    while i < n:
        entry = doc_ranges[i]
        if entry['header'] != '~~n/a~~':
            block_start = i
            block_end = i
            j = i + 1
            while j < n and doc_ranges[j]['header'] == '~~n/a~~':
                block_end = j
                j += 1
            new_entry = entry.copy()
            if block_end > block_start:
                new_entry['end_page'] = doc_ranges[block_end]['end_page']
            collapsed.append(new_entry)
            i = block_end + 1
        else:
            collapsed.append(entry.copy())
            i += 1
    return collapsed

# -----------------------------
# Clean headers
# -----------------------------
def clean_headers(doc_ranges: List[Dict]) -> List[Dict]:
    """Set header to '~~n/a~~' for entries with ...
      - coverage % < 30%, except first entry
      - identical to previous header(s)
      - adjoining page ranges (merge into first header)
      """
    if not doc_ranges:
        return []
    
    result = [entry.copy() for entry in doc_ranges]
    original_headers = [entry['header'] for entry in result]  # Store original headers
    
    # First pass: merge adjoining page ranges
    for i in range(len(result) - 1):
        if result[i]['header'] != '~~n/a~~' and result[i+1]['header'] != '~~n/a~~':
            # Check if page ranges are adjoining (end_page + 1 == next start_page)
            if result[i]['end_page'] + 1 == result[i+1]['start_page']:
                # Concatenate headers with delimiter
                result[i]['header'] = result[i]['header'] + ' ~^~ ' + result[i+1]['header']
                # Extend end_page
                result[i]['end_page'] = result[i+1]['end_page']
                # Mark second as n/a
                result[i+1]['header'] = '~~n/a~~'
    
    # Second pass: clean low coverage and duplicates
    for i in range(len(result)):
        if i != 0 and result[i].get('coverage %', 0) < 30:
            result[i]['header'] = '~~n/a~~'
        elif i > 0:
            # Check if this header matches ANY previous non-~~n/a~~ header
            for j in range(i):
                if original_headers[j] != '~~n/a~~' and original_headers[i] == original_headers[j]:
                    result[i]['header'] = '~~n/a~~'
                    break
    
    return result
