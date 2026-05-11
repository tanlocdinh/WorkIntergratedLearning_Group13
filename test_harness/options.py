PROMPT_TEXT_TYPE = "\nShow Text Type diagnostic for font_spans? (Y/N/E): "

PROMPT_TEXT_TYPE_BLOCKS = (
    "Select blocks for text_type diagnostic "
    "(for example 3, 3-6, 3,6 or press Enter for all TextBlocks): "
)

PROMPT_LOGICAL_DOCS = "\nShow Extracted 'LogicalDocument(s)' content? (Y/N/E): "

PROMPT_NORMALIZED_DOCS = "\nShow 'NormalizedDocument(s)' content? (Y/N/E): "


# General print helpers


def print_paths(base_dir, parent_dir, documents_folder, folder_exists):
    """Print resolved project paths for debugging."""
    print("Script dir     :", base_dir)
    print("Parent dir     :", parent_dir)
    print("Documents dir  :", documents_folder)
    print("Folder exists? :", folder_exists)


def print_no_file_selected():
    """Print message when no PDF file is selected."""
    print("No file selected. Exiting.")


def print_selected_file(pdf_path):
    """Print selected PDF path."""
    print("Selected file:", pdf_path)


def print_exit_message():
    """Print standard exit message."""
    print("\nExiting test harness.")


def print_return_to_raw_data():
    """Print standard message before returning to RawDataFile selection."""
    print("\nReturning to RawDataFile block/page selection...\n")


# Input helpers


def ask_yes_no_exit(prompt):
    """
    Ask user for Y/N/E input.

    Returns:
        "yes"  -> continue to the next step
        "back" -> go back to RawDataFile block/page selection
        "exit" -> exit program
    """
    while True:
        choice = input(prompt).strip().lower()

        if choice in ["y", "yes"]:
            return "yes"

        if choice in ["n", "no"]:
            return "back"

        if choice in ["e", "exit"]:
            return "exit"

        print("Invalid input. Please enter Y to continue, N to go back, or E to exit.")


def ask_text_type_blocks():
    """Ask user which blocks to use for text_type diagnostic."""
    return input(PROMPT_TEXT_TYPE_BLOCKS).strip()


def switch_to_production_mode():
    # change to production mode
    return None


def print_logical_docs_summary(logical_docs, title="Available LogicalDocument(s)"):
    """
    Print a short summary of available logical documents before user selection.
    """

    print("")
    print(f"{title}:")
    print(f"Created {len(logical_docs)} LogicalDocument(s):")

    for idx, doc in enumerate(logical_docs, start=1):
        # Get page range
        if hasattr(doc, "page_range"):
            page_range = getattr(doc, "page_range")
            start_page = page_range[0]
            end_page = page_range[1]
        else:
            start_page = getattr(doc, "start_page", "?")
            end_page = getattr(doc, "end_page", "?")

        # Get block count
        block_count = len(getattr(doc, "content", []))

        # Get font count
        font_count = len(getattr(doc, "font_collection", {}))

        print(
            f"  Document {idx}: Pages {start_page}-{end_page}, "
            f"{block_count} blocks, {font_count} fonts"
        )


def _get_block_page_1_based_for_options(block):
    """
    Local helper to avoid circular imports with test_harness_utils.
    Converts 0-based page number to 1-based page number.
    """
    raw_page = getattr(block, "page", None)
    if raw_page is not None:
        return raw_page + 1

    raw_page_num = getattr(block, "page_num", None)
    if raw_page_num is not None:
        return raw_page_num + 1

    return None


def _compress_ranges_for_options(numbers):
    """
    Compress list of numbers into readable ranges.
    Example:
        [1, 2, 3, 6, 8, 9] -> '1-3, 6, 8-9'
    """
    if not numbers:
        return ""

    numbers = sorted(numbers)
    ranges = []
    start = prev = numbers[0]

    for n in numbers[1:]:
        if n == prev + 1:
            prev = n
        else:
            if start == prev:
                ranges.append(f"{start}")
            else:
                ranges.append(f"{start}-{prev}")
            start = prev = n

    if start == prev:
        ranges.append(f"{start}")
    else:
        ranges.append(f"{start}-{prev}")

    return ", ".join(ranges)


def print_document_block_index(docs, document_label="LogicalDocument"):
    """
    Print block index for selected logical/normalized documents before asking
    the user to choose block range.

    Block numbers are relative to each displayed document.
    """
    print("")
    print(f"Block index for selected {document_label}(s):")

    for doc_idx, doc in enumerate(docs, start=1):
        blocks = getattr(doc, "content", [])

        print(f"  {document_label} {doc_idx}: {len(blocks)} blocks")

        # Group blocks by page
        page_to_blocks = {}
        type_to_blocks = {}

        for block_idx, block in enumerate(blocks, start=1):
            page_num = _get_block_page_1_based_for_options(block)
            block_type = type(block).__name__

            page_to_blocks.setdefault(page_num, []).append(block_idx)
            type_to_blocks.setdefault(block_type, []).append(block_idx)

        print("    Block distribution by page:")
        for page_num in sorted(page_to_blocks, key=lambda x: (x is None, x)):
            block_ranges = _compress_ranges_for_options(page_to_blocks[page_num])
            page_display = page_num if page_num is not None else "?"
            print(f"      Page {page_display}: blocks [{block_ranges}]")

        print("    Block type index:")
        for block_type in sorted(type_to_blocks):
            block_ranges = _compress_ranges_for_options(type_to_blocks[block_type])
            print(f"      {block_type}: [{block_ranges}]")
