from typing import List
from _classes import LogicalDocument, TableBlock, RawDataBlock, TextBlock, FigureBlock
from normalize_cleaning import normalize_cleaning
from normalize_text_blocks import normalize_text_blocks
from normalize_page_headers import normalize_page_headers
from normalize_table_blocks import normalize_table_blocks


def normalize(
    logical_docs: List[LogicalDocument],
    font_tags: dict,
    page_headers: list = None,
    test_mode: bool = False,
) -> List[LogicalDocument]:
    """
    Normalizes the content blocks within each logical document to create a cleaner set of content blocks for downstream processing.

    The goal of this function is to take the raw content blocks within each logical document and apply normalization techniques to create a cleaner and more consistent set of content blocks. This may include:
    - Merging adjacent text blocks that belong together (e.g., lines of the same paragraph) into a single text block with combined content and an updated bounding box.
    - Classifying text blocks into heading levels and body text based on their font properties and layout cues
    - Cleaning up table blocks by removing non-table words (e.g., captions, notes) and separating them into their own blocks if necessary.
    - Associating captions with their corresponding tables and figures based on their proximity and layout relationships.
    - Splitting embedded figures into separate figure blocks with their own content and properties.
    - Removing page headers/footers
    - Removing TOC's
    - Remove Reference lists

    Args:
      logical_docs: List of LogicalDocument objects to normalize
      font_tags: Font tags dict for font analysis and display (required)
      page_headers: Optional list of page header dictionaries for header/footer detection
      test_mode: If True, enables test harness diagnostics with interactive prompts
    """
    # Progress header
    print()
    print()
    print("normalized_docs = normalize(logical_docs, font_tags, page_headers)")
    print("==================================================================\n")

    new_docs = []
    for doc in logical_docs:
        new_doc = LogicalDocument(
            title=doc.title,
            type=doc.type,
            page_range=doc.page_range,
            font_collection=doc.font_collection,
            content=_normalize_blocks(doc.content, doc.font_collection, page_headers),
        )
        new_docs.append(new_doc)

    # Print normalization summary
    total_blocks = sum(len(doc.content) for doc in new_docs)
    text_count = sum(
        1 for doc in new_docs for b in doc.content if isinstance(b, TextBlock)
    )
    table_count = sum(
        1 for doc in new_docs for b in doc.content if isinstance(b, TableBlock)
    )
    figure_count = sum(
        1 for doc in new_docs for b in doc.content if isinstance(b, FigureBlock)
    )
    print(
        f"\nNormalized {len(new_docs)} LogicalDocument(s) with {total_blocks} blocks: {text_count} text, {table_count} tables, {figure_count} figures"
    )

    # -----------------------------------------------------------------------------------
    # TEST MODE: Display diagnostics if enabled
    # -----------------------------------------------------------------------------------
    if test_mode:
        # from test_harness.test_harness_utils import run_logical_docs_diagnostics
        # run_logical_docs_diagnostics(new_docs, font_tags, page_headers, prefix="Normalized")

        ### edit
        from test_harness.test_harness_utils import run_normalized_docs_diagnostics

        run_normalized_docs_diagnostics(new_docs, font_tags, page_headers)
    # -----------------------------------------------------------------------------------

    return new_docs


def _normalize_blocks(
    blocks: List[RawDataBlock], font_tags: dict[str, str], page_headers: list = None
) -> List[RawDataBlock]:
    # First pass is to merge adjacent text blocks that belong together (e.g., lines of the same paragraph) into a single text block with combined content and an updated bounding box.
    new_blocks = normalize_text_blocks(
        blocks, font_tags
    )  # normalize_text_blocks.py - resolve font spans to <tags>
    # new_blocks = normalize_page_headers(new_blocks, page_headers)   # normalize_page_headers.py - remove page headers and footers
    # new_blocks = normalize_table_blocks(new_blocks)                 # normalize_table_blocks.py - consolidate multi-page tables and recongigure as text
    # new_blocks = normalize_cleaning(new_blocks)                     # normalize_cleaning.py - remove table-of-contents, figures, ...
    return new_blocks
