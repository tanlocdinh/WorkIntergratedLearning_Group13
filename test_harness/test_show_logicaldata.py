from test_harness.test_harness_utils import format_block_label


def show_content_LogicalDocument(
    logical_docs, expand_blocks=None, font_tags=None, page_headers=None
):
    """Display LogicalDocument(s) in human-readable format.

    Args:
        logical_docs: List of LogicalDocument objects to display
        expand_blocks: Optional set of block numbers (int) to show in full detail instead of abbreviated
        font_tags: Optional font tags for the overall document (provides context across all logical documents)
        page_headers: Optional list of page header dictionaries containing 'header', 'start_page', 'end_page' keys
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

    def show_blocks(blocks, doc_num):
        """Display content blocks with sequential numbering within each document."""
        logger.print(
            f"\nLogicalDocument [{doc_num}] Content Blocks ({len(blocks)} blocks):"
        )
        logger.print("-" * 80)

        if expand_blocks:
            for idx, block in enumerate(blocks, 1):
                if idx in expand_blocks:
                    # block_type = type(block).__name__
                    # logger.print(
                    #     f"\n[{idx}] {block_type} - Page {getattr(block, 'page', '?')}"
                    # )

                    ### edit add new
                    block_type = type(block).__name__
                    page_num = getattr(block, "page", "?")
                    block_label = format_block_label(
                        "LOGICAL",
                        idx,
                        page_num=page_num,
                        doc_index=doc_num,
                    )
                    logger.print(f"\n{block_label} {block_type}")

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
                        # Simple wrap - text field has no line breaks (use font_spans for structure)
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

                        # Check if font_spans are tagged strings (normalized) or raw tuples
                        font_spans = getattr(block, "font_spans", [])
                        if font_spans:
                            # Check if first span is a string (normalized) or tuple (raw)
                            if isinstance(font_spans[0], str):
                                # Normalized: show as tagged strings
                                logger.print(
                                    f"    Tagged Text (FULL - Block [{idx}]): {len(font_spans)} span(s)"
                                )
                                for span_idx, tagged_span in enumerate(font_spans, 1):
                                    logger.print(
                                        f"      [{span_idx}] ['{tagged_span}']"
                                    )
                            else:
                                # Raw: show font information
                                logger.print(
                                    f"    Font Spans (FULL - Block [{idx}]): {len(font_spans)} span(s)"
                                )
                                for span_idx, span in enumerate(font_spans, 1):
                                    if len(span) >= 3:
                                        t = span[0]
                                        # Add human-readable annotation for line breaks (debugging aid)
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
                        logger.print(
                            f"    Image Type: {getattr(block, 'image_type', '?')}"
                        )
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
                # block_type = type(block).__name__
                # logger.print(
                #     f"\n[{idx}] {block_type} - Page {getattr(block, 'page', '?')}"
                # )
                ### edit add new
                block_type = type(block).__name__
                page_num = getattr(block, "page", "?")
                block_label = format_block_label(
                    "LOGICAL",
                    idx,
                    page_num=page_num,
                    doc_index=doc_num,
                )
                logger.print(f"\n{block_label} {block_type}")

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

                    # Check if font_spans are tagged strings (normalized) or raw tuples
                    font_spans = getattr(block, "font_spans", [])
                    if font_spans:
                        # Check if first span is a string (normalized) or tuple (raw)
                        if isinstance(font_spans[0], str):
                            # Normalized: show first 3 tagged spans
                            num_to_show = min(3, len(font_spans))
                            span_previews = [
                                f"['{s}']" for s in font_spans[:num_to_show]
                            ]
                            first_span_str = (
                                f"    Tagged Text: {len(font_spans)} span(s) - "
                                + ", ".join(span_previews)
                                + ", ..."
                            )
                            logger.print(first_span_str)
                        else:
                            # Raw: show first 3 with font info
                            num_to_show = min(3, len(font_spans))
                            span_previews = []
                            for span in font_spans[:num_to_show]:
                                if len(span) == 4:
                                    t, f, s, c = span
                                    span_previews.append(
                                        f"['{t}', '{f}', {s}, chars={c}]"
                                    )
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

    # Handle list of LogicalDocument objects
    if isinstance(logical_docs, list) and logical_docs:
        for doc_idx, doc in enumerate(logical_docs, 1):
            doc_type = type(doc).__name__

            # Build header title with document header if available
            if page_headers and doc_idx <= len(page_headers):
                header_text = page_headers[doc_idx - 1].get("header", "")
                if header_text and header_text != "~~n/a~~":
                    title = f"[{doc_type} {doc_idx}] - {header_text}"
                else:
                    title = f"[{doc_type} {doc_idx}]"
            else:
                title = f"[{doc_type} {doc_idx}]"

            logger.print(f"\n{'='*80}\n[{doc_type} {doc_idx}]\n{'='*80}")

            # Display page range
            if hasattr(doc, "page_range"):
                page_range = getattr(doc, "page_range", "?")
                logger.print(f"Page Range: {page_range[0]} - {page_range[1]}")

            # Display name (title)
            if hasattr(doc, "title"):
                doc_title = getattr(doc, "title", "")
                if doc_title:
                    # Check for delimiter and split if present
                    if " ~^~ " in doc_title:
                        parts = doc_title.split(" ~^~ ", 1)
                        logger.print(f"Name: {parts[0]}")
                        logger.print(f"      {parts[1]}")
                    else:
                        logger.print(f"Name: {doc_title}")

            # Display type
            if hasattr(doc, "type"):
                doc_type_value = getattr(doc, "type", "")
                if doc_type_value:
                    logger.print(f"Type: {doc_type_value}")

            # Display font tags (per-document analyzed font collection)
            if hasattr(doc, "font_collection"):
                font_collection = doc.font_collection
                logger.print(f"\nFont Tags ({len(font_collection)} entries):")

                # Calculate total characters for percentage calculation
                total_chars = sum(
                    value[1] if isinstance(value, tuple) and len(value) == 2 else 0
                    for value in font_collection.values()
                )

                for idx, (font_key, value) in enumerate(font_collection.items(), 1):
                    if isinstance(value, tuple) and len(value) == 2:
                        tag, char_count = value
                        percentage = (
                            (char_count / total_chars * 100) if total_chars > 0 else 0
                        )
                        logger.print(
                            f"  {idx}. {font_key}: {char_count} ({percentage:.1f}%) {tag}"
                        )
                    else:
                        # Fallback for old format
                        logger.print(f"  {idx}. {font_key}: {value}")

                # Process font tags for this logical document (processing retained, display removed)
                if font_collection:
                    # Extract tags only for process_font_tags
                    font_tags_only = {
                        k: v[0] if isinstance(v, tuple) else v
                        for k, v in font_collection.items()
                    }
                    font_tags = process_font_tags(font_tags_only)

            # Display content blocks
            if hasattr(doc, "content"):
                show_blocks(doc.content, doc_idx)

                # Summary statistics
                text_blocks = sum(
                    1 for b in doc.content if type(b).__name__ == "TextBlock"
                )
                table_blocks = sum(
                    1 for b in doc.content if type(b).__name__ == "TableBlock"
                )
                figure_blocks = sum(
                    1 for b in doc.content if type(b).__name__ == "FigureBlock"
                )
                total_blocks = len(doc.content)

                logger.print()
                logger.print(
                    f"Document [{doc_idx}] Summary - Blocks: Text: {text_blocks}, Table: {table_blocks}, Figure: {figure_blocks}, Total: {total_blocks}"
                )
    else:
        logger.print(
            "[show_content_LogicalDocument] No LogicalDocument objects to display or unsupported object type."
        )
