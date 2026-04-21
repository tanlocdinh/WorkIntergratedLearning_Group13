# Imports
import fitz
from typing import List
from _classes import TextBlock
#  bbxob: Tuple[int, int, int, int]  # (x0, y0, x1, y1) [RawDataBlock]
#  page: int [RawDataBlock]
#  text: str  # Full concatenated text content of the block (after merging all spans)
#  font_spans: List[Tuple[str, str, float, int]] # All the font spans that make up this text block (span_text, font_name, font_size, char_count)

# This module provides a function to extract text from a PDF page (using PyMuPDF), excluding regions that overlap with
# detected tables. It returns a TextBlock dataclass instance containing:
#   - bbox: bounding box covering all non-table text
#   - page: page number
#   - text: concatenated text content (all non-table words)
#   - font_spans: list of (span_text, font_name, font_size, char_count) tuples for each text span

# ===================================================================================
# Main Function: extract_text
# ===================================================================================
def extract_text_blocks(page, table_bboxes, header_threshold=None, footer_threshold=None):
    # print("[DEBUG] Entering extract_text")
    # Separate collections for header, body, and footer spans
    header_spans = []
    body_spans = []
    footer_spans = []
    
    all_x0, all_y0, all_x1, all_y1 = [], [], [], []
    
    # Track line positions for gap detection (separate for each region)
    prev_header_line_y1 = None
    prev_body_line_y1 = None
    prev_footer_line_y1 = None
    
    # Track previous region to detect transitions
    prev_region = None
    
    # Gap threshold for paragraph break detection
    PARAGRAPH_BREAK_THRESHOLD = 12  # pixels - paragraph/heading break

    # Extract all text blocks from the page using PyMuPDF
    text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            line_bbox = line.get("bbox", (0, 0, 0, 0))
            line_y0 = line_bbox[1]  # top of current line
            line_y1 = line_bbox[3]  # bottom of current line
            
            # Pre-scan to determine line region (need to know before adding spans)
            temp_line_region = None
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                x0, y0, x1, y1 = span.get("bbox", (0, 0, 0, 0))
                in_table = _point_in_any_bbox(x0, y0, table_bboxes)
                
                if not in_table:
                    # Determine if span is in header, footer, or body region
                    is_header = header_threshold is not None and y1 <= header_threshold
                    is_footer = footer_threshold is not None and y0 >= footer_threshold
                    
                    if is_header:
                        temp_line_region = 'header'
                    elif is_footer:
                        temp_line_region = 'footer'
                    else:
                        temp_line_region = 'body'
                    break  # Found first non-table span, that determines the region
            
            # Check for region transition and add line break marker BEFORE processing spans
            if temp_line_region and prev_region is not None and prev_region != temp_line_region:
                # Region transition - add line break to the NEW region before adding its content
                if temp_line_region == 'body':
                    body_spans.append(("\n", "", 0, 0, 0))
                elif temp_line_region == 'footer':
                    footer_spans.append(("\n", "", 0, 0, 0))
            
            # Now process all spans in this line
            line_has_content = False
            line_region = None  # Track which region this line belongs to
            
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                x0, y0, x1, y1 = span.get("bbox", (0, 0, 0, 0))
                font_size_raw = span.get("size", 12)
                font_size = round(font_size_raw, 1)  # Round to 1 decimal to reduce duplicates
                font_name = span.get("font", "")
                flags = span.get("flags", 0)  # Extract font flags (bold, italic, etc.)
                in_table = _point_in_any_bbox(x0, y0, table_bboxes)
                
                # Determine if span is in header, footer, or body region
                is_header = header_threshold is not None and y1 <= header_threshold
                is_footer = footer_threshold is not None and y0 >= footer_threshold
                
                if not in_table:
                    line_has_content = True
                    # Determine region for line break tracking
                    if is_header:
                        line_region = 'header'
                    elif is_footer:
                        line_region = 'footer'
                    else:
                        line_region = 'body'
                    
                    # Classify span into header, body, or footer
                    if is_header:
                        header_spans.append((text, font_name, font_size, len(text), flags))
                    elif is_footer:
                        footer_spans.append((text, font_name, font_size, len(text), flags))
                    else:
                        # Body content
                        body_spans.append((text, font_name, font_size, len(text), flags))
                        all_x0.append(x0)
                        all_y0.append(y0)
                        all_x1.append(x1)
                        all_y1.append(y1)
            
            # After processing all spans in this line, add line break marker
            if line_has_content and line_region:
                if line_region == 'header':
                    if prev_header_line_y1 is not None and prev_region == 'header':
                        vertical_gap = line_y0 - prev_header_line_y1
                        if vertical_gap > PARAGRAPH_BREAK_THRESHOLD:
                            header_spans.append(("\n\n", "", 0, 0, 0))
                        else:
                            # Always add at least single line break between lines
                            header_spans.append(("\n", "", 0, 0, 0))
                    prev_header_line_y1 = line_y1
                
                elif line_region == 'body':
                    if prev_body_line_y1 is not None and prev_region == 'body':
                        # Only check gap if we're staying in body region (transition already handled)
                        vertical_gap = line_y0 - prev_body_line_y1
                        if vertical_gap > PARAGRAPH_BREAK_THRESHOLD:
                            body_spans.append(("\n\n", "", 0, 0, 0))
                        else:
                            # Always add at least single line break between lines
                            body_spans.append(("\n", "", 0, 0, 0))
                    prev_body_line_y1 = line_y1
                
                elif line_region == 'footer':
                    if prev_footer_line_y1 is not None and prev_region == 'footer':
                        # Only check gap if we're staying in footer region (transition already handled)
                        vertical_gap = line_y0 - prev_footer_line_y1
                        if vertical_gap > PARAGRAPH_BREAK_THRESHOLD:
                            footer_spans.append(("\n\n", "", 0, 0, 0))
                        else:
                            # Always add at least single line break between lines
                            footer_spans.append(("\n", "", 0, 0, 0))
                    prev_footer_line_y1 = line_y1
                
                # Update previous region
                prev_region = line_region
    
    # Compose TextBlock
    if all_x0 and all_y0 and all_x1 and all_y1:
        bbox = (min(all_x0), min(all_y0), max(all_x1), max(all_y1))
    else:
        bbox = (0, 0, 0, 0)
    
    # Build text from spans (skip line breaks for clean text searching)
    def spans_to_text(spans):
        """Convert spans to text, skipping line break markers, joining text spans with spaces."""
        if not spans:
            return ""
        text_parts = []
        for span_text, font_name, font_size, char_count, flags in spans:
            # Skip line break markers - they're only in font_spans for structure
            if span_text not in ("\n", "\n\n"):
                text_parts.append(span_text)
        return " ".join(text_parts)
    
    header_text = spans_to_text(header_spans)
    body_text = spans_to_text(body_spans)
    footer_text = spans_to_text(footer_spans)
    
    # Combine all text in reading order: header, body, footer
    full_text_parts = []
    if header_text:
        full_text_parts.append(header_text)
    if body_text:
        full_text_parts.append(body_text)
    if footer_text:
        full_text_parts.append(footer_text)
    full_text = " ".join(full_text_parts)
    
    page_num = page.number if hasattr(page, "number") else 0
    # Combine all spans in reading order: header, body, footer
    all_spans = []
    if header_spans:
        all_spans.extend(header_spans)
    if body_spans:
        all_spans.extend(body_spans)
    if footer_spans:
        all_spans.extend(footer_spans)
    return TextBlock(
        bbox=bbox, 
        page=page_num, 
        text=full_text,
        font_spans=all_spans
    )


def _point_in_any_bbox(x, y, bboxes):
    """Check if a point (x, y) is inside any of the bounding boxes."""
    for bbox in bboxes:
        x0, y0, x1, y1 = bbox
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False
