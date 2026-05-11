import os
import ctypes
import ctypes.wintypes
import time
import tkinter as tk
from test_harness.options import print_logical_docs_summary, print_document_block_index


# -----------------------------------------------------------------------------------
# Multi-Monitor Helpers
# -----------------------------------------------------------------------------------

import re
from collections import Counter, defaultdict


def summarize_blocks_by_type(blocks):
    """
    Return block numbers grouped by block type.
    Example:
        {
            "TextBlock": [3, 6, 10],
            "TableBlock": [12],
            "FigureBlock": [1, 2, 4]
        }
    """
    type_to_blocks = {}

    for idx, block in enumerate(blocks, start=1):
        block_type = type(block).__name__
        type_to_blocks.setdefault(block_type, []).append(idx)

    return type_to_blocks


def make_font_key(font_name, font_size):
    """
    Build the same font key style used in font_collection.

    Example:
        font_name = CIDFont+F2-Bold
        font_size = 15.0
        -> CIDFont+F2-Bold-15.0
    """
    try:
        size = f"{float(font_size):.1f}"
    except (TypeError, ValueError):
        size = str(font_size)

    return f"{font_name}-{size}"


def get_tag_order(tag):
    """
    Sort tags in a readable order:
        <h1>, <h2>, <h3>, ..., <p>, others
    """
    tag = str(tag).lower()

    if tag.startswith("<h") and tag.endswith(">"):
        try:
            level = int(tag.replace("<h", "").replace(">", ""))
            return (level, tag)
        except ValueError:
            pass

    if tag == "<p>":
        return (99, tag)

    return (100, tag)


def extract_tag_from_span(span, font_collection):
    """
    Extract a tag from either:
    1. Normalized span string:
        '<h1>Some text</h1>'
    2. Raw font span tuple:
        ('Some text', 'CIDFont+F2-Bold', 15.0, chars=20)

    Returns:
        '<h1>', '<h2>', '<p>', etc., or None.
    """

    # Case 1: normalized tagged string
    if isinstance(span, str):
        match = re.search(r"<(h[1-6]|p)>", span.lower())
        if match:
            return f"<{match.group(1)}>"
        return None

    # Case 2: raw tuple span
    if isinstance(span, tuple) and len(span) >= 3 and font_collection:
        font_name = span[1]
        font_size = span[2]
        font_key = make_font_key(font_name, font_size)

        value = font_collection.get(font_key)

        if isinstance(value, tuple) and len(value) >= 1:
            return value[0]

        if isinstance(value, str):
            return value

    return None


def build_tag_distribution(blocks, font_collection=None):
    """
    Build tag distribution from document blocks.

    Returns:
        by_block:
            [(block_index, Counter({'<h1>': 1, '<p>': 2})), ...]

        by_tag:
            {
                '<h1>': [2, 8],
                '<h2>': [5],
                '<p>': [2, 3, 4]
            }
    """

    by_block = []
    by_tag = defaultdict(list)

    for block_index, block in enumerate(blocks, start=1):
        font_spans = getattr(block, "font_spans", [])
        tag_counts = Counter()

        for span in font_spans:
            tag = extract_tag_from_span(span, font_collection)

            if tag:
                tag_counts[tag] += 1

        if tag_counts:
            by_block.append((block_index, tag_counts))

            for tag in tag_counts:
                by_tag[tag].append(block_index)

    return by_block, dict(by_tag)


def print_tag_distribution(
    logger, blocks, font_collection=None, title="Tag Distribution"
):
    """
    Print tag distribution in two views:
    1. By block
    2. By tag
    """

    by_block, by_tag = build_tag_distribution(blocks, font_collection)

    logger.print("")
    logger.print(title)
    logger.print("-" * 80)

    if not by_block:
        logger.print("  No tag distribution data available.")
        return

    logger.print("By block:")
    for block_index, tag_counts in by_block:
        parts = []

        for tag in sorted(tag_counts.keys(), key=get_tag_order):
            parts.append(f"{tag} x {tag_counts[tag]}")

        logger.print(f"  Block [{block_index}]: " + ", ".join(parts))

    logger.print("")
    logger.print("By tag:")
    for tag in sorted(by_tag.keys(), key=get_tag_order):
        block_refs = ", ".join(f"[{block_num}]" for block_num in by_tag[tag])
        logger.print(f"  {tag}: {block_refs}")


def extract_font_size(font_key):
    """
    Extract font size from a font key such as:
        CIDFont+F2-Bold-15.0
        CIDFont+F4-Italic-8.4
        -0

    Returns a float font size. Unknown sizes are sorted first as 0.0.
    """
    try:
        size_part = str(font_key).split("-")[-1]
        return float(size_part)
    except (ValueError, TypeError):
        return 0.0


def sort_font_collection(font_collection):
    """
    Sort font collection by font size first, then font name.

    Expected font_collection format:
        {
            font_key: (tag, char_count)
        }
    """
    return sorted(
        font_collection.items(),
        key=lambda item: (extract_font_size(item[0]), str(item[0]).lower()),
    )


def get_block_page_1_based(block):
    raw_page = getattr(block, "page", None)
    if raw_page is not None:
        return raw_page + 1

    raw_page_num = getattr(block, "page_num", None)
    if raw_page_num is not None:
        return raw_page_num + 1

    return None


def get_console_hwnd():
    """Return the HWND of the Python console window."""
    return ctypes.windll.kernel32.GetConsoleWindow()


def maximize_console():
    """
    Maximizes the Python console window.
    """
    time.sleep(0.3)  # allow console to initialize
    hwnd = get_console_hwnd()
    if hwnd:
        SW_MAXIMIZE = 3
        ctypes.windll.user32.ShowWindow(hwnd, SW_MAXIMIZE)


def move_console_to_monitor2():
    """
    Moves the Python console window to Monitor 2 (right of primary).
    Adjust width/height if needed.
    """
    time.sleep(0.3)  # allow console to initialize
    hwnd = get_console_hwnd()
    if hwnd:
        ctypes.windll.user32.MoveWindow(hwnd, 1920, 0, 1200, 900, True)


def get_console_position():
    """
    Returns (x, y) of the console window's top-left corner.
    """
    hwnd = get_console_hwnd()
    if not hwnd:
        return 0, 0
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top


def set_monitor_CMD():
    """
    Setup console on Monitor 2, maximize it, and create a positioned Tk root window for dialogs.
    Returns the Tk root window positioned at the console location.
    """
    move_console_to_monitor2()
    maximize_console()

    x, y = get_console_position()

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.geometry(f"+{x}+{y}")  # place root on same monitor as CMD

    return root


def flatten_content(content):
    """Recursively flatten nested lists/tuples and yield strings for output."""
    if isinstance(content, (list, tuple)):
        if all(isinstance(item, str) for item in content):
            yield " | ".join(item.replace("\n", " ") for item in content)
        else:
            for item in content:
                yield from flatten_content(item)
    else:
        yield str(content)


def parse_block_range(input_str):
    """Parse block input string into a set of block numbers.

    Supports:
        - Single number: '110'
        - Range: '110-112' (inclusive)
        - Comma-separated: '110,112,115'
        - Combination: '110-112,115'

    Returns:
        set: Set of block numbers (integers)
    """

    if not input_str:
        return set()

    blocks = set()
    parts = input_str.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            # Handle range
            try:
                start, end = part.split("-")
                start, end = int(start.strip()), int(end.strip())

                ### edit 7-5 => 5-7
                if start > end:
                    start, end = end, start

                blocks.update(range(start, end + 1))
            except ValueError:
                pass
        elif part.isdigit():
            blocks.add(int(part))

    return blocks


# -----------------------------------------------------------------------------------
# Test Harness Diagnostic Display Functions
# -----------------------------------------------------------------------------------
# NOTE: Diagnostic wrappers (extract_raw_data_with_diagnostics,
# split_logical_docs_with_diagnostics) are no longer needed.
# The production functions now accept test_mode and trace parameters to handle
# diagnostics internally while maintaining clean return signatures.
# -----------------------------------------------------------------------------------


# def run_raw_data_diagnostics(raw_data_file, font_tags):
#     """
#     Handles all RawDataFile printing and interactive display.
#     Consolidates test harness display logic for raw data extraction phase.

#     Args:
#         raw_data_file: The RawDataFile object to display
#         font_tags: Font tags for display context
#     """
#     from test_harness.test_show_rawdata import show_content_RawDataFile

#     print("")
#     print("")
#     if input("Show 'RawDataFile' content? (y/n): ").lower().startswith("y"):
#         expand_input = input(
#             "Expand specific block range or press Enter to skip): "
#         ).strip()
#         expand_blocks = parse_block_range(expand_input)
#         show_content_RawDataFile(
#             raw_data_file, expand_blocks=expand_blocks, font_tags=font_tags
#         )


### edit
def run_raw_data_diagnostics(raw_data_file, font_tags, ask_show=True):  ### ask_show
    """
    Handles all RawDataFile printing and interactive display.
    Consolidates test harness display logic for raw data extraction phase.

    Args:
        raw_data_file: The RawDataFile object to display
        font_tags: Font tags for display context
    """
    from test_harness.test_show_rawdata import show_content_RawDataFile

    print("")
    print("")

    # if input("Show 'RawDataFile' content? (y/n): ").lower().startswith("y"):
    if (not ask_show) or input(
        "Show 'RawDataFile' content? (y/n): "
    ).lower().startswith(
        "y"
    ):  ### edit

        # Show page-to-block summary BEFORE asking for block range.
        # This helps the user know which block numbers are available.
        page_map = summarize_blocks_by_page(raw_data_file.content)
        print("\nBlock distribution by page:")

        for page_num in sorted(page_map):
            block_ranges = compress_ranges(page_map[page_num])
            print(f"  Page {page_num}: blocks [{block_ranges}]")

        # Show block type index BEFORE asking for block range.
        # This helps users choose TextBlock/TableBlock/FigureBlock numbers.
        type_map = summarize_blocks_by_type(raw_data_file.content)
        print("\nBlock type index:")

        for block_type in sorted(type_map):
            block_ranges = compress_ranges(type_map[block_type])
            print(f"  {block_type}: [{block_ranges}]")

        while True:
            expand_input = input(
                "Expand specific block range or press Enter to skip): "
            ).strip()

            if expand_input == "":
                expand_blocks = None
                break

            expand_blocks = parse_block_range(expand_input)

            if expand_blocks:
                break

            print(f"Invalid block selection: '{expand_input}'")
            print("Try examples: 5, 1-5, 1,3,7, 1-5,8,10-12")

        # show a page-to-block summary before page filtering
        # help the user understand which block numbers belong to which pages
        # making page selection easier

        page_map = summarize_blocks_by_page(raw_data_file.content)
        print("\nBlock distribution by page:")

        for page_num in sorted(page_map):
            block_ranges = compress_ranges(page_map[page_num])
            print(f"  Page {page_num}: blocks [{block_ranges}]")

        while True:

            page_input = input(
                "Select page to view (for example 5, 5-6, 1,3 or press Enter to skip): "
            ).strip()

            if page_input == "":
                selected_pages = None
                break

            selected_pages = parse_page_range(page_input)

            if selected_pages:
                break

            print(f"Invalid page selection: '{page_input}'")
            print("Try examples: 5, 5-6, 1,3,7")

        show_content_RawDataFile(
            raw_data_file,
            expand_blocks=expand_blocks,
            selected_pages=selected_pages,
            font_tags=font_tags,
        )


# def run_logical_docs_diagnostics(logical_docs, font_tags, page_headers, prefix=""):
#     """
#     Handles all LogicalDocument printing and interactive display.
#     Consolidates test harness display logic for logical document splitting phase.

#     Args:
#         logical_docs: List of LogicalDocument objects to display
#         font_tags: Font tags for display context
#         page_headers: Page header information for display context
#         prefix: Optional prefix for the prompt (e.g., "Extracted", "Normalized")
#     """
#     from test_harness.test_show_logicaldata import show_content_LogicalDocument

#     print("")
#     print("")
#     prompt = (
#         f"Show {prefix} 'LogicalDocument(s)' content? (y/n): "
#         if prefix
#         else "Show 'LogicalDocument(s)' content? (y/n): "
#     )
#     if input(prompt).lower().startswith("y"):
#         expand_input = input(
#             "Expand specific block range or press Enter to skip): "
#         ).strip()
#         expand_blocks = parse_block_range(expand_input)
#         show_content_LogicalDocument(
#             logical_docs,
#             expand_blocks=expand_blocks,
#             font_tags=font_tags,
#             page_headers=page_headers,
#         )


### edit (add new)


def parse_page_range(input_str):

    #  Parse page input string into a set of page numbers.

    #     Single number: '5'
    #     Range: '5-7'
    #     Comma-separated: '5,7,9'
    #     Combination: '5-7,9'

    # Return a set: Set of page numbers (integers)

    if not input_str:
        return set()

    pages = set()
    parts = input_str.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-")
                start, end = int(start.strip()), int(end.strip())

                if start > end:
                    start, end = end, start

                pages.update(range(start, end + 1))
            except ValueError:
                pass
        elif part.isdigit():
            pages.add(int(part))

    return pages


### edit add new


def compress_ranges(numbers):
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


### edit add new


def summarize_blocks_by_page(blocks):
    page_to_blocks = {}

    for idx, block in enumerate(blocks, 1):
        page = get_block_page_1_based(block)
        # raw_page = getattr(block, "page", None)

        # if raw_page is not None:
        #     page = raw_page + 1
        # else:
        #     raw_page_num = getattr(block, "page_num", None)
        #     if raw_page_num is not None:
        #         page = raw_page_num + 1
        #     else:
        #         continue

        page_to_blocks.setdefault(page, []).append(idx)

    return page_to_blocks


### edit add new


def parse_doc_selection(input_str, max_docs):
    if not input_str:
        return set()

    input_str = input_str.strip().lower()
    if input_str == "all":
        return set(range(1, max_docs + 1))

    docs = set()
    parts = input_str.split(",")

    for part in parts:
        part = part.strip()
        if "-" in part:
            try:
                start, end = part.split("-")
                start, end = int(start.strip()), int(end.strip())

                if start > end:
                    start, end = end, start

                for n in range(start, end + 1):
                    if 1 <= n <= max_docs:
                        docs.add(n)
            except ValueError:
                pass
        elif part.isdigit():
            n = int(part)
            if 1 <= n <= max_docs:
                docs.add(n)

    return docs


### edit add new
def format_block_label(phase, block_index, page_num=None, doc_index=None):

    #        block labels
    #        RAW   -> [RAW 5 | Page 2]
    #        LOGIC -> [DOC 1 | BLOCK 5 | Page 2]
    #        NORM  -> [NORM DOC 1 | BLOCK 5 | Page 2]

    phase = phase.upper().strip()

    if phase == "RAW":
        parts = [f"RAW {block_index}"]
    elif phase == "LOGICAL":
        if doc_index is not None:
            parts = [f"DOC {doc_index}", f"BLOCK {block_index}"]
        else:
            parts = [f"LOGICAL {block_index}"]
    elif phase == "NORM":
        if doc_index is not None:
            parts = [f"NORM DOC {doc_index}", f"BLOCK {block_index}"]
        else:
            parts = [f"NORM {block_index}"]
    else:
        parts = [f"{phase} {block_index}"]

    if page_num is not None:
        parts.append(f"Page {page_num}")

    return "[" + " | ".join(parts) + "]"


### edit


def run_logical_docs_diagnostics(
    logical_docs, font_tags, page_headers, prefix="", ask_show=True
):
    """
    Handles all LogicalDocument printing and interactive display.
    Consolidates test harness display logic for logical document splitting phase.

    Args:
        logical_docs: List of LogicalDocument objects to display
        font_tags: Font tags for display context
        page_headers: Page header information for display context
        prefix: Optional prefix for the prompt (e.g., "Extracted", "Normalized")
    """
    from test_harness.test_show_logicaldata import show_content_LogicalDocument

    print("")
    print("")

    prompt = (
        f"Show {prefix} 'LogicalDocument(s)' content? (y/n): "
        if prefix
        else "Show 'LogicalDocument(s)' content? (y/n): "
    )

    # if input(prompt).lower().startswith("y"):
    if (not ask_show) or input(prompt).lower().startswith("y"):  ### edit

        ### add: show available logical documents before asking user to select
        print_logical_docs_summary(
            logical_docs, title="Available LogicalDocument(s) for selection"
        )

        while True:
            doc_input = input(
                "Select logical document to view (for example: 1, 1-2,...or press Enter for all): "
            ).strip()

            if doc_input == "":
                selected_docs = None
                break

            selected_docs = parse_doc_selection(doc_input, len(logical_docs))

            if selected_docs:
                break

            print(f"Invalid logical document selection: '{doc_input}'")
            print("for examples: 1, 1-3, or all")

        if selected_docs is None:
            docs_to_show = logical_docs
        else:
            docs_to_show = [
                doc
                for idx, doc in enumerate(logical_docs, start=1)
                if idx in selected_docs
            ]

        ### add
        print_document_block_index(docs_to_show, document_label="LogicalDocument")

        while True:
            expand_input = input(
                "Expand specific block range based on the index above "
                "(for example 1, 1-3, 1,3 or press Enter to skip): "
            ).strip()

            if expand_input == "":
                expand_blocks = None
                break

            expand_blocks = parse_block_range(expand_input)

            if expand_blocks:
                break

            print(f"Invalid block selection: '{expand_input}'")
            print("For examples: 1, 1-3, or 1,3")

        show_content_LogicalDocument(
            docs_to_show,
            expand_blocks=expand_blocks,
            font_tags=font_tags,
            page_headers=page_headers,
        )


def run_normalized_docs_diagnostics(
    normalized_docs, font_tags, page_headers, ask_show=True
):
    """
    Handles all NormalizedDocument printing and interactive display.
    """
    from test_harness.test_show_normdata import show_content_NormalizeDocument

    print("")
    print("")

    # if input("Show 'NormalizedDocument(s)' content? (y/n): ").lower().startswith("y"):
    if (not ask_show) or input(
        "Show 'NormalizedDocument(s)' content? (y/n): "
    ).lower().startswith(
        "y"
    ):  ### edit

        ### add
        print_logical_docs_summary(
            normalized_docs, title="Available NormalizedDocument(s) for selection"
        )

        while True:
            doc_input = input(
                "Select normalized document to view (for example 1, 1-3, or press Enter for all): "
            ).strip()

            if doc_input == "":
                selected_docs = None
                break

            selected_docs = parse_doc_selection(doc_input, len(normalized_docs))

            if selected_docs:
                break

            print(f"Invalid normalized document selection: '{doc_input}'")
            print("for examples: 1, 1-3, 1,3 or all")

        if selected_docs is None:
            docs_to_show = normalized_docs
        else:
            docs_to_show = [
                doc
                for idx, doc in enumerate(normalized_docs, start=1)
                if idx in selected_docs
            ]

        ### add
        print_document_block_index(docs_to_show, document_label="NormalizedDocument")

        while True:
            expand_input = input(
                "Expand specific block range based on the index above "
                "(for example 1, 1-3, 1,3 or press Enter to skip): "
            ).strip()

            if expand_input == "":
                expand_blocks = None
                break

            expand_blocks = parse_block_range(expand_input)

            if expand_blocks:
                break

            print(f"Invalid block selection: '{expand_input}'")
            print("For examples: 1, 1-3, or 1,3")

        show_content_NormalizeDocument(
            docs_to_show,
            expand_blocks=expand_blocks,
            font_tags=font_tags,
            page_headers=page_headers,
        )


### Need to do 1
# [1] FigureBlock - Page 1
# => raw [Raw 5 | Page 1]
# => logical [Document 1 | Block 5 | Page 1]
# => Norm [Normalize Document 1 | Block 1 | Page 1]


### Need to do 2
# by block: Block 1: <h1> x 2, <h2> x 1, <p> x2
# by tag: <h1>: [1], [2],... ([]: block)
# by tag: <h2>: [3], [4],...
