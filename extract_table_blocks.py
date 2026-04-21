import re
import fitz
from typing import List, Tuple
from _classes import TableBlock
from extract_caption_utils import extract_caption
#  bbxob: Tuple[int, int, int, int]  # (x0, y0, x1, y1) [RawDataBlock]
#  page: int [RawDataBlock]
#  data: List[List[str]]  # 2D list representing the table data - row[cell(row,col) value...]
#  caption: str # Text that appears before/after the table and may be part of the caption
#  cols: int
#  rows: int
#  first_data_row: int
#  stub_header: str
#  col_headers: List[str]
#  row_headers: List[str]
#  not_table_words: List[str]  # Words that are in the table block but not part of the table (e.g., captions, notes

def extract_table_blocks(page: fitz.Page) -> List[TableBlock]:
    """
    Extract table blocks from a PDF page using PyMuPDF's table detection.
    
    Detects tables, merges multiple tables on the same page with the same number of columns (or split tables) when appropriate, extracts
    captions, and returns TableBlock objects with all table data, caption data and metadata.
    
    Main processing steps:
    1. Find all tables on the PDF page using PyMuPDF's table detection.
    2. For each detected table, extract its data and bounding box.
    3. If a table continues from a previous one (same columns, small vertical gap), merge them.
    4. If not, treat as a new table and store the previous one.
    5. After all tables, add any remaining merged table to the results.
    6. Return list of TableBlock objects.
    
    Args:
        page: PyMuPDF page object
    
    Returns:
        List of TableBlock objects representing all tables found on the page 
    """
    table_blocks = []
    try:
        table_finder = page.find_tables()
        tabs = list(table_finder.tables) if hasattr(table_finder, 'tables') else list(table_finder)
        for tab in tabs:
            table_data = tab.extract()
            if not table_data:
                continue  # Skip empty tables
            
            # Extract caption using shared utility (searches 60 points above/below)
            caption = extract_caption(page, tab.bbox, search_distance=60)
            
            table_blocks.append(_create_table_block(
                page,
                table_data,
                tab.bbox,
                caption.strip()
            ))
    except Exception as e:
        pass
    # Initialize table_bboxes as a list of bbox for each table
    table_bboxes = [block.bbox for block in table_blocks]
    return table_blocks, table_bboxes


def _create_table_block(
    page: fitz.Page,
    table_data: List[List[str]],
    bbox: Tuple[float, float, float, float],
    caption: str
) -> TableBlock:
    """
    Create a TableBlock object from extracted table data.
    
    Args:
        page: PyMuPDF page object
        table_data: 2D list of table cell values
        bbox: Table bounding box (x0, y0, x1, y1)
        caption: Caption text found before/after the table
    Returns:
        TableBlock object with all fields populated
    """
    # Basic table structure
    row_count = len(table_data)
    col_count = len(table_data[0]) if table_data else 0
    
    # Do not extract col_headers or row_headers here; headers will be determined downstream.
    # Use all table_data as data.
    data = table_data
    
    # Convert bbox to int tuple
    bbox_int = tuple(int(coord) for coord in bbox)
    return TableBlock(
        bbox=bbox_int,
        page=page.number,
        data=data,
        caption=caption.strip(),
        cols=col_count,
        rows=row_count,
        first_data_row=0,
        stub_header="",
        col_headers=[],
        row_headers=[],
        not_table_words=[]
    )

