# Imports
import fitz
from typing import List, Tuple
from _classes import FigureBlock
from extract_caption_utils import extract_caption

# This module provides a function to extract figures (images) from a PDF page (using PyMuPDF),
# along with their captions (if detected). It returns a list of FigureBlock dataclass instances containing:
#   - bbox: bounding box covering the figure image
#   - page: page number
#   - caption: text appearing before/after the figure
#   - image_data: raw image data in bytes
#
# IMPORTANT LIMITATION:
# This extraction only detects embedded raster images (PNG, JPEG, etc.) and some image form XObjects.
# It does NOT detect vector graphics, flowcharts, or diagrams drawn using PDF path/shape commands.
# Vector-based figures will be captured in TextBlocks or may be misidentified as TableBlocks depending
# on their structure. Detecting and extracting vector graphics would require analyzing PDF drawing
# operators and grouping them into figure regions, which is beyond the scope of simple image extraction.

# ===================================================================================
# Main Function: extract_figure_blocks
# ===================================================================================
def extract_figure_blocks(page) -> List[FigureBlock]:
    """
    Extract figure blocks from a PDF page, including images and their associated captions.
    
    Uses page.get_image_info() for robust image detection including position information.
    
    Args:
        page: PyMuPDF page object
    
    Returns:
        List[FigureBlock]: List of extracted figures with captions and image data
    """
    figure_blocks = []
    page_num = page.number if hasattr(page, "number") else 0
    
    # Use get_image_info() which provides bbox information directly
    try:
        image_info_list = page.get_image_info()
    except Exception:
        # Fallback to empty list if method not available
        image_info_list = []
    
    if not image_info_list:
        return figure_blocks
    
    for img_index, img_dict in enumerate(image_info_list):
        try:
            # Extract bbox from image info
            bbox = img_dict.get('bbox')
            if not bbox:
                continue
            
            bbox_tuple = tuple(bbox)  # (x0, y0, x1, y1)
            
            # Calculate dimensions
            img_width = bbox[2] - bbox[0]
            img_height = bbox[3] - bbox[1]
            
            # Get xref for image extraction
            xref = img_dict.get('xref', 0)
            
            # Extract image data
            image_data = b""
            image_type = "unknown"
            
            if xref > 0:
                try:
                    base_image = page.parent.extract_image(xref)
                    if base_image:
                        image_data = base_image["image"]
                        image_type = base_image.get("ext", "unknown")
                except Exception:
                    # Image reference exists but can't extract (e.g., form XObject, inline image)
                    # Record with type="unknown" and empty data
                    pass
            
            # Extract caption using shared utility
            caption = extract_caption(page, bbox_tuple, search_distance=50)
            
            # Create FigureBlock
            figure_block = FigureBlock(
                bbox=bbox_tuple,
                page=page_num,
                caption=caption,
                image_data=image_data,
                image_type=image_type,
                width=img_width,
                height=img_height
            )
            
            figure_blocks.append(figure_block)
            
        except Exception:
            # Skip problematic images silently
            continue
    
    return figure_blocks
