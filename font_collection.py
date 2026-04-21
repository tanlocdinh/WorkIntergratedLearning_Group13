
from typing import List, Tuple
from _classes import RawDataBlock, FontCollection, FontSpan
from font_tags import process_font_tags

def extract_font_collection(blocks: List[RawDataBlock]) -> tuple:
    """
    Build a font collection from extracted blocks
    Args:
        blocks: List of RawDataBlock (TextBlock, TableBlock, etc.)
    Returns:
        tuple: (font_collection dict mapping font_name-size to (tag, char_count), 
                font_tags dict with processed font information)
    """
    font_collection = {}
    for block in blocks:
        # Only process TextBlock instances (they have font_spans)
        if hasattr(block, 'font_spans'):
            for span in getattr(block, 'font_spans', []):
                # span: (span_text, font_name, font_size, char_count, flags)
                # Handle both 4-tuple (legacy) and 5-tuple (with flags) formats
                if len(span) >= 3:
                    _, font_name, font_size = span[0], span[1], span[2]
                    char_count = span[3] if len(span) >= 4 else 0
                    flags = span[4] if len(span) >= 5 else 0
                    
                    # Build key with style info from flags
                    style_suffix = ""
                    if flags > 0:
                        if (flags & 16) != 0:  # Bold
                            style_suffix += "-Bold"
                        if (flags & 2) != 0:   # Italic
                            style_suffix += "-Italic"
                    
                    key = f"{font_name}{style_suffix}-{font_size}"
                    
                    if key not in font_collection:
                        font_collection[key] = ("<?>", 0)
                    
                    # Accumulate character count for this font
                    current_tag, current_count = font_collection[key]
                    font_collection[key] = (current_tag, current_count + char_count)

    # Process font collection to generate font_tags (for downstream use)
    font_tags = process_font_tags(font_collection)
   
    return font_collection, font_tags


def extract_font_collection_rich(blocks: List[RawDataBlock]) -> FontCollection:
    """
    Build a rich FontCollection from extracted blocks using new structured classes.
    
    Args:
        blocks: List of RawDataBlock (TextBlock, TableBlock, etc.)
    
    Returns:
        FontCollection: Rich font collection with analysis and structured data
    """
    collection = FontCollection()
    
    for block in blocks:
        # Only process TextBlock instances (they have font_spans)
        if hasattr(block, 'font_spans'):
            for span_tuple in getattr(block, 'font_spans', []):
                # Convert tuple to FontSpan and add to collection
                # Handles both 4-tuple (legacy) and 5-tuple (with flags)
                if len(span_tuple) >= 4:
                    span = FontSpan.from_tuple(span_tuple)
                    collection.add_span(span)
    
    # Analyze to infer roles and hierarchy
    collection.analyze()
    
    return collection


def get_font_tag(font_name: str, font_size: float, font_collection: dict[str, tuple[str, int]]) -> str:
    """
    Get the semantic tag for a given font from the analyzed font collection.
    
    Args:
        font_name: Font name (e.g., "ArialMT", "Arial-BoldMT")
        font_size: Font size in points
        font_collection: Analyzed font collection dict with tags
    
    Returns:
        str: Semantic tag like "<h1>", "<h2>", "<p>", or "<?>" if not found
    """
    key = f"{font_name}-{font_size}"
    if key in font_collection:
        tag, _ = font_collection[key]
        return tag
    return "<?>"


def tag_font_spans(font_spans: List[Tuple], font_collection: dict[str, tuple[str, int]]) -> List[Tuple[str, str]]:
    """
    Convert font spans to (text, tag) tuples using analyzed font collection.
    
    Args:
        font_spans: List of font span tuples (text, font_name, font_size, char_count, [flags])
        font_collection: Analyzed font collection dict with tags
    
    Returns:
        List of (text, semantic_tag) tuples
        
    Example:
        >>> tagged = tag_font_spans(spans, analyzed_font_collection)
        >>> tagged
        [("Main Title", "<h1>"), ("Body text here", "<p>"), ("Subheading", "<h2>")]
    """
    tagged_spans = []
    for span in font_spans:
        if len(span) >= 3:
            text = span[0]
            font_name = span[1]
            font_size = span[2]
            
            tag = get_font_tag(font_name, font_size, font_collection)
            tagged_spans.append((text, tag))
    
    return tagged_spans

