from test_harness.test_harness_utils import (
    flatten_content,
    get_block_page_1_based,
    format_block_label,
    sort_font_collection,
)


def show_content_RawDataFile(
    obj, expand_blocks=None, selected_pages=None, font_tags=None
):
    """Display RawDataFile, LogicalDocument(s), or normalizedDocument(s) in human-readable format.

    Args:
        obj: The object to display
        expand_blocks: Optional set of block numbers (int) to show in full detail instead of abbreviated
    """
    import textwrap
    from font_collection import process_font_tags

    def flatten_content(content):
        if isinstance(content, (list, tuple)):
            if all(isinstance(item, str) for item in content):
                yield " | ".join(item.replace("\n", " ") for item in content)
            else:
                for item in content:
                    yield from flatten_content(item)
        else:
            yield str(content)

    if expand_blocks is None:
        expand_blocks = set()

    logger = type("Logger", (), {"print": print})()

    def show_blocks(blocks):
        logger.print(f"\nRawDataFile Content Blocks ({len(blocks)} blocks):")
        logger.print("-" * 80)
        if expand_blocks:
            # Iterate through blocks with 1-based indexing (for user-friendly display).
            # We apply two levels of filtering:
            # 1. Block-level filtering (expand_blocks) → which blocks to show in detail
            # 2. Page-level filtering (selected_pages) → which pages to include
            for idx, block in enumerate(blocks, 1):
                # Only display blocks that are explicitly selected for expansion.
                # This allows users to inspect specific blocks in full detail instead of printing
                # the entire document (which can be very large for long PDFs).
                if idx not in expand_blocks:
                    continue

                page_num_1_based = get_block_page_1_based(block)
                # filter blocks by selected page range
                # ensures that only blocks belonging to the specified pages are displayed
                # if no page filter (None), all pages are shown
                if (
                    selected_pages is not None
                    and page_num_1_based not in selected_pages
                ):
                    continue

                block_type = type(block).__name__
                # Display page number in 1-based format for consistency with user input.
                # If page information is missing, fallback to "?" to avoid runtime errors.
                page_display = page_num_1_based if page_num_1_based is not None else "?"

                ### edit
                block_label = format_block_label("RAW", idx, page_num=page_display)
                logger.print(f"\n{block_label} {block_type}")
                # logger.print(f"\n[{idx}] {block_type} - Page {page_display}")

                logger.print(f"    BBox: {getattr(block, 'bbox', '?')}")
                if block_type == "TableBlock":
                    logger.print(
                        f"    Dimensions: {getattr(block, 'rows', '?')} rows × {getattr(block, 'cols', '?')} columns"
                    )
                    logger.print(
                        f"    Column Headers: {getattr(block, 'col_headers', '?')}"
                    )
                    caption = getattr(block, "caption", "")
                    logger.print(
                        f"    Caption: '{caption[:60]}...'"
                        if len(caption) > 60
                        else f"    Caption: '{caption}'"
                    )
                    logger.print(
                        f"    First Data Row: {getattr(block, 'first_data_row', '?')}"
                    )
                    logger.print(f"    Data Review (all rows):")
                    for row_idx, row in enumerate(getattr(block, "data", []), 1):
                        logger.print(f"      Row {row_idx}: {row}")
                elif block_type == "TextBlock":
                    text = getattr(block, "text", "")
                    logger.print(f"    Text (FULL - Block [{idx}]):")
                    wrapped_lines = textwrap.wrap(
                        text,
                        width=100,
                        initial_indent="    '",
                        subsequent_indent="     ",
                    )
                    if wrapped_lines:
                        for line in wrapped_lines[:-1]:
                            logger.print(line)
                        logger.print(wrapped_lines[-1] + "'")
                    else:
                        logger.print("    ''")
                    font_spans = getattr(block, "font_spans", [])
                    if font_spans:
                        logger.print(
                            f"    Font Spans (FULL - Block [{idx}]): {len(font_spans)} span(s)"
                        )
                        for span_idx, span in enumerate(font_spans, 1):
                            if len(span) >= 3:
                                t = span[0]
                                if t == "\n\n":
                                    logger.print(
                                        f"      [{span_idx}] ['\\n\\n', '', 0]  ← PARAGRAPH BREAK"
                                    )
                                elif t == "\n":
                                    logger.print(
                                        f"      [{span_idx}] ['\\n', '', 0]  ← LINE BREAK"
                                    )
                                elif len(span) == 4:
                                    f, s, c = span[1], span[2], span[3]
                                    logger.print(
                                        f"      [{span_idx}] ['{t}', '{f}', {s}, chars={c}]"
                                    )
                                else:
                                    f, s = span[1], span[2]
                                    logger.print(
                                        f"      [{span_idx}] ['{t}', '{f}', {s}]"
                                    )
                    else:
                        logger.print(f"    Font Spans: {len(font_spans)} span(s)")
                elif block_type == "FigureBlock":
                    logger.print(f"    Image Type: {getattr(block, 'image_type', '?')}")
                    logger.print(
                        f"    Dimensions: {getattr(block, 'width', 0):.1f} × {getattr(block, 'height', 0):.1f} points"
                    )
                    caption_text = getattr(block, "caption", "").replace("\n", " ")
                    if caption_text:
                        logger.print(f"    Caption: '{caption_text}'")
                    logger.print(
                        f"    Image Data: {len(getattr(block, 'image_data', b''))} bytes"
                    )
        else:
            for idx, block in enumerate(blocks, 1):
                ### edit (add new)
                page_num_1_based = get_block_page_1_based(block)
                if (
                    selected_pages is not None
                    and page_num_1_based not in selected_pages
                ):
                    continue

                block_type = type(block).__name__
                page_display = page_num_1_based if page_num_1_based is not None else "?"
                logger.print(f"\n[{idx}] {block_type} - Page {page_display}")

                logger.print(f"    BBox: {getattr(block, 'bbox', '?')}")
                if block_type == "TableBlock":
                    logger.print(
                        f"    Dimensions: {getattr(block, 'rows', '?')} rows × {getattr(block, 'cols', '?')} columns"
                    )
                    logger.print(
                        f"    Column Headers: {getattr(block, 'col_headers', '?')}"
                    )
                    caption = getattr(block, "caption", "")
                    logger.print(
                        f"    Caption: '{caption[:60]}...'"
                        if len(caption) > 60
                        else f"    Caption: '{caption}'"
                    )
                    logger.print(
                        f"    First Data Row: {getattr(block, 'first_data_row', '?')}"
                    )
                    logger.print(f"    Data Review (all rows):")
                    for row_idx, row in enumerate(getattr(block, "data", []), 1):
                        logger.print(f"      Row {row_idx}: {row}")
                elif block_type == "TextBlock":
                    text = getattr(block, "text", "")
                    if len(text) > 200:
                        start_preview = text[:150].replace("\n", " ")
                        end_preview = text[-50:].replace("\n", " ")
                        text_to_display = f"{start_preview}...{end_preview}"
                    else:
                        text_to_display = text.replace("\n", " ")
                    wrapped_lines = textwrap.wrap(
                        text_to_display,
                        width=100,
                        initial_indent="    Text: '",
                        subsequent_indent="           ",
                    )
                    if wrapped_lines:
                        for line in wrapped_lines[:-1]:
                            logger.print(line)
                        logger.print(wrapped_lines[-1] + "'")
                    else:
                        logger.print("    Text: ''")
                    font_spans = getattr(block, "font_spans", [])
                    if font_spans:
                        num_to_show = min(3, len(font_spans))
                        span_previews = []
                        for span in font_spans[:num_to_show]:
                            if len(span) == 4:
                                t, f, s, c = span
                                span_previews.append(f"['{t}', '{f}', {s}, chars={c}]")
                            else:
                                t, f, s = span[:3]
                                span_previews.append(f"['{t}', '{f}', {s}]")
                        first_span_str = (
                            f"    Font Spans: {len(font_spans)} span(s) - "
                            + ", ".join(span_previews)
                            + ", ..."
                        )
                        logger.print(first_span_str)
                    else:
                        logger.print(f"    Font Spans: {len(font_spans)} span(s)")
                elif block_type == "FigureBlock":
                    logger.print(f"    Image Type: {getattr(block, 'image_type', '?')}")
                    logger.print(
                        f"    Dimensions: {getattr(block, 'width', 0):.1f} × {getattr(block, 'height', 0):.1f} points"
                    )
                    caption_text = getattr(block, "caption", "").replace("\n", " ")
                    if caption_text:
                        logger.print(f"    Caption: '{caption_text}'")
                    logger.print(
                        f"    Image Data: {len(getattr(block, 'image_data', b''))} bytes"
                    )

    if hasattr(obj, "font_collection") and hasattr(obj, "content"):
        show_blocks(obj.content)
        text_blocks = sum(1 for b in obj.content if type(b).__name__ == "TextBlock")
        table_blocks = sum(1 for b in obj.content if type(b).__name__ == "TableBlock")
        figure_blocks = sum(1 for b in obj.content if type(b).__name__ == "FigureBlock")
        total_blocks = len(obj.content)
        print()
        logger.print(
            f"Blocks: Text: {text_blocks}, Table: {table_blocks}, Figure: {figure_blocks}, Total: {total_blocks}"
        )

        ### add
        text_block_nums = [
            idx
            for idx, b in enumerate(obj.content, start=1)
            if type(b).__name__ == "TextBlock"
        ]

        table_block_nums = [
            idx
            for idx, b in enumerate(obj.content, start=1)
            if type(b).__name__ == "TableBlock"
        ]

        figure_block_nums = [
            idx
            for idx, b in enumerate(obj.content, start=1)
            if type(b).__name__ == "FigureBlock"
        ]

        logger.print("Block Type Index:")
        logger.print(f"  TextBlock: {text_block_nums}")
        logger.print(f"  TableBlock: {table_block_nums}")
        logger.print(f"  FigureBlock: {figure_block_nums}")

        # logger.print(
        #     f"\nFont Collection for PDF file ({len(obj.font_collection)} entries):"
        # )

        # total_chars = sum(
        #     value[1] if isinstance(value, tuple) and len(value) == 2 else 0
        #     for value in obj.font_collection.values()
        # )

        # for idx, (font_key, value) in enumerate(obj.font_collection.items(), 1):
        #     if isinstance(value, tuple) and len(value) == 2:
        #         tag, char_count = value
        #         percentage = (char_count / total_chars * 100) if total_chars > 0 else 0
        #         logger.print(
        #             f"  {idx}. {font_key}: {char_count} ({percentage:.1f}%) {tag}"
        #         )
        #     else:
        #         logger.print(f"  {idx}. {font_key} {value}")

        ### edit

        logger.print(
            f"\nFont Collection sorted by size and font name for PDF file ({len(obj.font_collection)} entries):"
        )

        total_chars = sum(
            value[1] if isinstance(value, tuple) and len(value) == 2 else 0
            for value in obj.font_collection.values()
        )

        for idx, (font_key, value) in enumerate(
            sort_font_collection(obj.font_collection), 1
        ):
            if isinstance(value, tuple) and len(value) == 2:
                tag, char_count = value
                percentage = (char_count / total_chars * 100) if total_chars > 0 else 0
                logger.print(
                    f"  {idx}. {font_key}: {char_count} ({percentage:.1f}%) {tag}"
                )
            else:
                logger.print(f"  {idx}. {font_key} {value}")

        if font_tags is None:
            font_tags_only = {
                k: v[0] if isinstance(v, tuple) else v
                for k, v in obj.font_collection.items()
            }
            font_tags = process_font_tags(font_tags_only)
    elif (
        isinstance(obj, list)
        and obj
        and (hasattr(obj[0], "content") or hasattr(obj[0], "sections"))
    ):
        for doc_idx, doc in enumerate(obj, 1):
            doc_type = type(doc).__name__
            logger.print(f"\n{'='*40}\n[{doc_type} {doc_idx}]\n{'='*40}")
            if hasattr(doc, "page_range"):
                logger.print(f"Page Range: {getattr(doc, 'page_range', '?')}")
            if hasattr(doc, "font_collection"):
                logger.print(f"Font Collection ({len(doc.font_collection)} entries):")

                total_chars = sum(
                    value[1] if isinstance(value, tuple) and len(value) == 2 else 0
                    for value in doc.font_collection.values()
                )

                # for idx, (font_key, value) in enumerate(doc.font_collection.items(), 1):
                ### edit
                for idx, (font_key, value) in enumerate(
                    sort_font_collection(doc.font_collection), 1
                ):
                    if isinstance(value, tuple) and len(value) == 2:
                        tag, char_count = value
                        percentage = (
                            (char_count / total_chars * 100) if total_chars > 0 else 0
                        )
                        logger.print(
                            f"  {idx}. {font_key}: {char_count} ({percentage:.1f}%) {tag}"
                        )
                    else:
                        logger.print(f"  {idx}. {font_key} {value}")
            if hasattr(doc, "content"):
                show_blocks(doc.content)
            if hasattr(doc, "sections"):
                logger.print(f"Sections: {len(doc.sections)}")
                for sec_idx, sec in enumerate(doc.sections, 1):
                    logger.print(
                        f"  Section {sec_idx}: {getattr(sec, 'title', '')[:60]}"
                    )
    elif (
        isinstance(obj, list)
        and obj
        and hasattr(obj[0], "title")
        and hasattr(obj[0], "content")
    ):
        logger.print(f"Sections: {len(obj)}")
        for sec_idx, sec in enumerate(obj, 1):
            logger.print(f"  Section {sec_idx}: {getattr(sec, 'title', '')[:60]}")
    else:
        logger.print("[show_content] Unsupported object type.")


# Helper function to standardise page numbering. (get_block_page_1_based)
# PyMuPDF (and our extracted blocks) use 0-based indexing (page 0 = first page),
# while user input is naturally 1-based (page 1 = first page).
# This function converts block page numbers to 1-based format so that
# user input (e.g., "1-5") matches the displayed results correctly.


"""
Enhancement: Block and Page Filtering Support

This function was extended to support:
1. Block-level selection (expand_blocks)
2. Page-level filtering (selected_pages)

Rationale:
- Large PDFs (e.g., 200+ pages) can contain hundreds of blocks,
  making full output unreadable in terminal.
- Block filtering allows targeted debugging of specific elements.
- Page filtering enables users to inspect content by document structure.
- Conversion from 0-based → 1-based page indexing ensures alignment
  between system data and user expectations.

These improvements significantly enhance usability and debugging efficiency
in the test harness.
"""
