from typing import List
from _classes import RawDataFile

# dataclass RawDataFile
#  font_collection: dict[str, str]
#  content: List[RawDataBlock]

import fitz  # PyMuPDF

from extract_table_blocks import extract_table_blocks
from extract_text_blocks import extract_text_blocks
from extract_figure_blocks import extract_figure_blocks
from font_collection import extract_font_collection
from extract_page_thresholds import extract_page_thresholds


def extract_raw_data(file_path: str, test_mode: bool = False) -> RawDataFile:
    """
      Extracts content blocks (text, tables, figures) from a PDF document, along with their properties for downstream processing.

      The goal of this function is to convert the raw PDF content into a structured format that can be used for sectioning and entity extraction. This includes:
    - Extracting text blocks with their content, bounding boxes, page numbers, and inferred levels (
    e.g., heading vs body text) based on font properties and layout cues.
    - Extracting tables with their captions (if available), headers, rows, bounding boxes, and
    page numbers.
    - Extracting figures with their captions (if available), bounding boxes, page numbers, and image data.
    - Building a font collection that maps font properties to inferred roles (e.g., heading levels and body text) to assist in sectioning and content classification.

      Args:
        file_path: Path to the PDF file to extract
        test_mode: If True, enables test harness diagnostics with interactive prompts
    """
    pdf = fitz.open(file_path)

    # Progress header
    print(f"raw_data_file = extract_raw_data(pdf_path")
    print("=========================================\n")

    if not test_mode:
        print("Mode: Production")
    else:
        print("Mode: Test / Diagnostic")

    # Detect header and footer thresholds across all pages
    header_threshold, footer_threshold = extract_page_thresholds(pdf)

    all_blocks = []
    total_pages = pdf.page_count
    import os

    filename = os.path.basename(file_path)
    print(f"Processing PDF: {filename} ({total_pages} pages)\n")

    text_block_list = []
    for idx, page in enumerate(pdf, start=1):
        print(f"Page {idx} of {total_pages}", end="\r", flush=True)

        table_blocks, table_bboxes = extract_table_blocks(page)

        text_blocks = extract_text_blocks(
            page, table_bboxes, header_threshold, footer_threshold
        )

        figure_blocks = extract_figure_blocks(page)

        all_blocks.extend(table_blocks)  # Extend with table_blocks
        if isinstance(text_blocks, list):
            text_block_list.extend(text_blocks)
            all_blocks.extend(text_blocks)
        else:
            text_block_list.append(text_blocks)
            all_blocks.append(text_blocks)
        all_blocks.extend(figure_blocks)  # Extend with figure_blocks

    # Sort the blocks in reading order based on their page numbers and bounding box positions to facilitate downstream processing such as sectioning and entity extraction.
    all_blocks = sorted(
        all_blocks, key=lambda block: (block.page, block.bbox[1], block.bbox[0])
    )

    # Extract the font collection (total pages)
    font_collection, font_tags = extract_font_collection(text_block_list)

    raw_data_file = RawDataFile(font_collection=font_collection, content=all_blocks)

    # Print extraction summary
    from _classes import TextBlock, TableBlock, FigureBlock

    text_count = sum(1 for b in all_blocks if isinstance(b, TextBlock))
    table_count = sum(1 for b in all_blocks if isinstance(b, TableBlock))
    figure_count = sum(1 for b in all_blocks if isinstance(b, FigureBlock))
    print(
        f"\nExtracted {len(all_blocks)} blocks: {text_count} text, {table_count} tables, {figure_count} figures"
    )

    # -----------------------------------------------------------------------------------
    # TEST MODE: Display diagnostics if enabled
    # -----------------------------------------------------------------------------------
    if test_mode:
        from test_harness.test_harness_utils import run_raw_data_diagnostics

        run_raw_data_diagnostics(raw_data_file, font_tags)
    # -----------------------------------------------------------------------------------

    return raw_data_file
