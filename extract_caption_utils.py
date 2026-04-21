"""
Caption Extraction Utilities

Shared utilities for extracting and cleaning caption text from PDF pages
for both tables and figures. Captions are typically found immediately above
or below the content element.
"""

import fitz
from typing import Tuple


def extract_caption_zone(page: fitz.Page, element_bbox: Tuple[float, float, float, float], 
                        position: str = 'pre', search_distance: int = 60) -> str:
    """
    Extract text from the zone above ('pre') or below ('post') an element's bounding box.
    
    Args:
        page: PyMuPDF page object
        element_bbox: Element bounding box (x0, y0, x1, y1) - could be table or figure
        position: 'pre' for text above element, 'post' for text below element
        search_distance: Distance in points to search for captions (default: 60)
    
    Returns:
        Extracted text from the caption zone (max 200 characters, cleaned)
    """
    x0, y0, x1, y1 = element_bbox
    page_rect = page.rect
    
    # Calculate the zone above or below the element
    if position == 'pre':
        zone_x0 = x0
        zone_x1 = x1
        zone_y0 = max(page_rect.y0, y0 - search_distance)
        zone_y1 = y0
    else:  # 'post'
        zone_x0 = x0
        zone_x1 = x1
        zone_y0 = y1
        zone_y1 = min(page_rect.y1, y1 + search_distance)
    
    # Create clip rectangle for the caption zone
    clip_rect = fitz.Rect(zone_x0, zone_y0, zone_x1, zone_y1)
    
    # Extract text from the zone
    try:
        caption_text = page.get_text("text", clip=clip_rect).strip()
        # Limit to 200 characters and clean up
        if len(caption_text) > 200:
            caption_text = caption_text[:200].strip()
        # Clean and normalize the caption text
        caption_text = clean_caption_text(caption_text)
        return caption_text
    except Exception:
        return ""


def clean_caption_text(text: str) -> str:
    """
    Clean and normalize caption text extracted from PDF.
    Removes artifacts, extra whitespace, and common noise patterns.
    
    Args:
        text: Raw caption text extracted from PDF
    
    Returns:
        Cleaned and normalized caption text
    """
    if not text:
        return ""
    
    # Replace multiple whitespace with single space
    import re
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common artifacts
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    
    # Strip and return
    return text.strip()


def extract_caption(page: fitz.Page, element_bbox: Tuple[float, float, float, float], 
                   search_distance: int = 60) -> str:
    """
    Extract complete caption by combining text from above and below an element.
    
    Args:
        page: PyMuPDF page object
        element_bbox: Element bounding box (x0, y0, x1, y1)
        search_distance: Distance in points to search for captions (default: 60)
    
    Returns:
        Combined caption text from pre and post zones
    """
    caption_pre = extract_caption_zone(page, element_bbox, position='pre', search_distance=search_distance)
    caption_post = extract_caption_zone(page, element_bbox, position='post', search_distance=search_distance)
    
    # Combine captions
    caption = (caption_pre or "") + (" " + caption_post if caption_post else "")
    
    return caption.strip()
