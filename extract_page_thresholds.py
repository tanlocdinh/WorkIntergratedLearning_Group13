"""
Header and Footer Detection Module

This module analyzes text spans across all pages of a PDF to identify consistent
header and footer regions based on their vertical positions (Y-coordinates).

The detection works by:
1. Collecting Y-coordinates of text spans in the top and bottom regions of each page
2. Finding the maximum Y for headers and minimum Y for footers across all pages
3. Returning these thresholds for use in text extraction
"""

import fitz


def extract_page_thresholds(pdf, header_percent=0.10, footer_percent=0.10):
    """
    Analyze all pages to find consistent header/footer Y-position thresholds.
    
    Args:
        pdf: PyMuPDF document object
        header_percent: Percentage of page height to consider for header detection (default 10%)
        footer_percent: Percentage of page height to consider for footer detection (default 10%)
    
    Returns:
        tuple: (header_threshold, footer_threshold) - Y-coordinates defining header/footer boundaries
               header_threshold: Maximum Y where headers end
               footer_threshold: Minimum Y where footers begin
    """
    header_y_positions = []
    footer_y_positions = []
    
    for page in pdf:
        page_height = page.rect.height
        header_region_limit = page_height * header_percent
        footer_region_start = page_height * (1 - footer_percent)
        
        # Extract text spans
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:  # Skip non-text blocks
                continue
            
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    
                    bbox = span.get("bbox", (0, 0, 0, 0))
                    y0 = bbox[1]  # Top Y coordinate
                    y1 = bbox[3]  # Bottom Y coordinate
                    
                    # Check if span is in header region (top of page)
                    if y1 <= header_region_limit:
                        header_y_positions.append(y1)
                    
                    # Check if span is in footer region (bottom of page)
                    if y0 >= footer_region_start:
                        footer_y_positions.append(y0)
    
    # Determine thresholds
    # Header threshold: the maximum Y coordinate where any header appears
    # This ensures we capture all header content across all pages
    header_threshold = max(header_y_positions) if header_y_positions else 0
    
    # Footer threshold: the minimum Y coordinate where any footer appears
    # This ensures we capture all footer content across all pages
    footer_threshold = min(footer_y_positions) if footer_y_positions else float('inf')
    
    return header_threshold, footer_threshold
