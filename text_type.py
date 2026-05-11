import re


def unpack_font_span(font_span):
    """
    Convert a font span into text, font_name, and font_size.

    Expected formats:
        ['text', 'font_name', 12.0]
        ('text', 'font_name', 12.0)
        ['text', 'font_name', 12.0, chars]
    """

    if not isinstance(font_span, (list, tuple)):
        return "", "", 0

    text = font_span[0] if len(font_span) > 0 else ""
    font_name = font_span[1] if len(font_span) > 1 else ""
    font_size = font_span[2] if len(font_span) > 2 else 0

    return text, font_name, font_size


def is_line_break(text, font_name, font_size):
    return text in ["\n", "\n\n"] or text.strip() == "" and font_size == 0


def is_bullet_or_symbol(text):
    stripped = text.strip()

    if stripped in ["•", "◦", "▪", "▫", "-", "–", "—"]:
        return True

    # Common private-use bullet/symbol chars from PDFs
    if "\uf0b7" in stripped:
        return True

    # Very short non-alphanumeric symbol
    if len(stripped) <= 2 and not any(ch.isalnum() for ch in stripped):
        return True

    return False


def is_table_of_contents(text):
    stripped = text.strip()

    # Example: "1.0 Summary ........ 3"
    if re.search(r"\.{3,}\s*\d+$", stripped):
        return True

    # Example: "1.2 Project Background 4"
    if re.match(r"^\d+(\.\d+)+\s+.+\s+\d+$", stripped):
        return True

    return False


def is_heading(text, font_name, font_size):
    stripped = text.strip()

    if not stripped:
        return False

    # Larger font usually means heading
    try:
        size = float(font_size)
    except (TypeError, ValueError):
        size = 0

    font_lower = str(font_name).lower()

    if size >= 14:
        return True

    # Bold short line can be a heading
    if "bold" in font_lower and size >= 11 and len(stripped) <= 120:
        return True

    # ALL CAPS short line can be heading
    if stripped.isupper() and len(stripped.split()) <= 12:
        return True

    # Numbered heading e.g. "1.0 Introduction"
    if re.match(r"^\d+(\.\d+)*\s+[A-Z]", stripped):
        return True

    return False

    # def is_heading(text, font_name, font_size):
    #     stripped = text.strip()

    #     if not stripped:
    #         return False

    #     # Avoid classifying very short spans such as single letters,
    #     # punctuation, or broken words as headings.
    #     if len(stripped) <= 2:
    #         return False

    #     # Larger font usually means heading
    #     try:
    #         size = float(font_size)
    #     except (TypeError, ValueError):
    #         size = 0

    #     font_lower = str(font_name).lower()

    #     if size >= 14:
    #         return True

    #     # Bold short line can be a heading
    #     if "bold" in font_lower and size >= 11 and len(stripped) <= 120:
    #         return True

    #     # ALL CAPS short line can be heading
    #     if stripped.isupper() and len(stripped.split()) <= 12:
    #         return True

    #     # Numbered heading e.g. "1.0 Introduction"
    #     if re.match(r"^\d+(\.\d+)*\s+[A-Z]", stripped):
    #         return True

    return False


def is_sentence(text):
    stripped = text.strip()

    if not stripped:
        return False

    # Ends like a full sentence
    if stripped.endswith((".", "?", "!")):
        return True

    return False


def is_part_sentence(text):
    stripped = text.strip()

    if not stripped:
        return False

    # Has words, but does not look complete
    if any(ch.isalpha() for ch in stripped):
        return True

    return False


# def is_part_sentence(text):
#     stripped = text.strip()

#     if not stripped:
#         return False

#     # Avoid classifying isolated single letters as meaningful part-sentences.
#     if len(stripped) <= 1:
#         return False

#     # Has words, but does not look complete
#     if any(ch.isalpha() for ch in stripped):
#         return True

#     return False


def text_type(font_span):
    """
    Assign a text type to a single font span.

    Returns:
        line_break
        bullet_or_symbol
        table_of_contents
        heading
        sentence
        part_sentence
        unknown
    """

    text, font_name, font_size = unpack_font_span(font_span)

    if is_line_break(text, font_name, font_size):
        return "line_break"

    if is_bullet_or_symbol(text):
        return "bullet_or_symbol"

    if is_table_of_contents(text):
        return "table_of_contents"

    if is_heading(text, font_name, font_size):
        return "heading"

    if is_sentence(text):
        return "sentence"

    if is_part_sentence(text):
        return "part_sentence"

    return "unknown"
