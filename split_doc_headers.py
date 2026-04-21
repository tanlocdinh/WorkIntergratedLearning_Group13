# split_doc_headers.py

import re
from split_doc_utils import (
    normalize_header,
    truncate_logical,
    header_coverage,
    highest_coverage,
    collapse_headers,
    clean_headers,
)


# ===================================================================================
# Main Function: split_docs_headers
# ===================================================================================
# It extracts page headers → determines which pages share the same header →
# groups them → calculates coverage → optionally normalizes
# overlapping/truncated headers.
# The result is a list of logical document sections (doc_ranges)
# with start/end pages and coverage.
# ===================================================================================
def split_doc_headers(RawDataFile):

    # ---------------------------------------------------------------------------
    # Extract one primary TextBlock per page from RawDataFile
    # ---------------------------------------------------------------------------
    # Build a dictionary keyed by page number so each page maps to a single block
    page_blocks = {}
    for block in getattr(RawDataFile, "content", []):
        if block.__class__.__name__ == "TextBlock":
            page = getattr(block, "page", None)
            # Keep only the first TextBlock encountered for each page
            if page not in page_blocks:
                page_blocks[page] = block

    # ---------------------------------------------------------------------------
    # Normalize page numbering to 1-based indexing
    # ---------------------------------------------------------------------------
    # Sort pages in ascending order
    pages = sorted(page_blocks.keys())

    # Convert 0-based pages to 1-based page numbers
    pages_1based = [p + 1 for p in pages]

    # Rebuild page_blocks dictionary using 1-based keys
    page_blocks_1based = {p + 1: page_blocks[p] for p in pages}

    # ---------------------------------------------------------------------------
    # Initialize document range tracking
    # ---------------------------------------------------------------------------
    doc_ranges = []  # Final list of logical document sections
    min_header_len = 25  # Minimum length for header to be "substantial"
    header_prefix_len = (
        25  # Length of prefix to compare for header matching (generalizable default)
    )
    current_range = None  # Active document range being built
    last_substantial_norm = None  # Last normalized substantial header seen

    print("pages_1_based: ", pages_1based)

    # ---------------------------------------------------------------------------
    # Iterate through each page and detect possible header boundaries
    # ---------------------------------------------------------------------------
    for idx, page in enumerate(pages_1based):

        # Get the page's primary text block
        block = page_blocks_1based[page]

        # Extract first ~250 characters as header candidate
        header_candidate_raw = getattr(block, "text", "")[:250].strip()

        # Logically truncate (avoid cutting mid-word etc.)
        header_candidate = truncate_logical(header_candidate_raw, max_len=250)

        # Normalize header (collapse whitespace etc.)
        header_candidate_norm = normalize_header(header_candidate)

        # Determine if this header is substantial enough to define a new document
        is_substantial = len(header_candidate_norm) >= min_header_len

        # -----------------------------------------------------------------------
        # Substantial header detected
        # -----------------------------------------------------------------------
        if is_substantial:

            # Compare only the prefix to determine if this is a new document
            # This groups pages with similar header prefixes together
            header_prefix = header_candidate_norm[:header_prefix_len]
            last_prefix = (
                last_substantial_norm[:header_prefix_len]
                if last_substantial_norm
                else None
            )

            # If first substantial header OR header prefix differs from previous one
            if last_substantial_norm is None or header_prefix != last_prefix:

                # If a range is already open, close it before starting new one
                if current_range:
                    current_range["end_page"] = pages_1based[idx - 1]
                    doc_ranges.append(current_range)

                # Start a new document range
                current_range = {
                    "header": header_candidate,
                    "start_page": page,
                    "end_page": None,
                }

                # Track this header as the latest substantial header
                last_substantial_norm = header_candidate_norm

            else:
                # Same substantial header as previous page
                # Continue extending current range (do nothing)
                pass

        # -----------------------------------------------------------------------
        # Not substantial but already inside a document range
        # -----------------------------------------------------------------------
        elif current_range:
            # Continue extending current document range
            # (Header too short to define a new document)
            pass

        # -----------------------------------------------------------------------
        # No substantial header seen yet (early pages)
        # -----------------------------------------------------------------------
        else:
            # Initialize first document range even if header is weak
            current_range = {
                "header": header_candidate,
                "start_page": page,
                "end_page": None,
            }

            # Only set last_substantial_norm if it qualifies
            last_substantial_norm = header_candidate_norm if is_substantial else None

    # ---------------------------------------------------------------------------
    # Close the final open document range and calculate coverage percentage for each document range
    # ---------------------------------------------------------------------------
    if current_range:
        current_range["end_page"] = pages_1based[-1]
        doc_ranges.append(current_range)
    doc_ranges = header_coverage(doc_ranges)

    # ---------------------------------------------------------------------------
    # Normalize document ranges if > 3 headers detected
    # ---------------------------------------------------------------------------
    if len(doc_ranges) > 4:
        # Find the header with the highest coverage (excluding the first entry)
        inx = highest_coverage(doc_ranges, exclude_first=True)
        # Set all headers to "~~n/a~~" except for doc_ranges[0] and doc_ranges[inx]
        for i in range(len(doc_ranges)):
            if i != 0 and i != inx:
                doc_ranges[i]["header"] = "~~n/a~~"

    doc_ranges = clean_headers(doc_ranges)
    doc_ranges = collapse_headers(doc_ranges)
    doc_ranges = header_coverage(doc_ranges)

    # ---------------------------------------------------------------------------
    # Return final list of logical document sections
    # ---------------------------------------------------------------------------
    return doc_ranges
