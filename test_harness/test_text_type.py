from text_type import text_type


def show_text_type_for_blocks(raw_data_file, expand_blocks=None):
    """
    Display font spans with detected text_type.
    """

    if expand_blocks is None:
        expand_blocks = set()

    print("")
    print("Text Type Diagnostic")
    print("=" * 80)

    for block_index, block in enumerate(raw_data_file.content, start=1):
        block_type = type(block).__name__

        if block_type != "TextBlock":
            continue

        if expand_blocks and block_index not in expand_blocks:
            continue

        print("")
        print(f"[Block {block_index}] TextBlock")
        print("-" * 80)

        font_spans = getattr(block, "font_spans", [])

        if not font_spans:
            print("  No font_spans found.")
            continue

        for span_index, span in enumerate(font_spans, start=1):
            detected_type = text_type(span)

            print(f"  Span [{span_index}] Type: {detected_type}")
            print(f"    {span}")
