from typing import List
from _classes import RawDataFile, LogicalDocument, FontCollection
#dataclass RawDataFile
#  font_collection: dict[str, str]
#  content: List[RawDataBlock]

#dataclass LogicalDocument:
# page_range: Tuple[int, int]
# font_collection: dict[str, str]
# content: List[RawDataBlock]

from split_doc_headers import split_doc_headers
from font_collection import extract_font_collection, extract_font_collection_rich

def split_logical_docs(raw_data_file: RawDataFile, test_mode: bool = False) -> List[LogicalDocument]:
  """
  Splits the raw content blocks extracted from the PDF into logical documents based on their properties (e.g., bounding boxes, page numbers).
  
  The goal of this function is to group content blocks into logical documents that may span multiple pages in the PDF. This can be done by analyzing the page numbers and spatial relationships of the blocks to determine which blocks belong together as part of the same logical document. For example, blocks that are close together on the same page or across consecutive pages may be grouped into the same logical document, while blocks that are separated by larger gaps or page breaks may be split into different logical documents.
  
  Args:
    raw_data_file: The RawDataFile object containing extracted content blocks
    test_mode: If True, enables test harness diagnostics with interactive prompts
  """
  # Progress header
  print()
  print()
  print("logical_docs, font_tags, page_headers = split_logical_docs(raw_data_file)")
  print("=========================================================================\n")

  # Split into logical document boundaries
  page_headers = split_doc_headers(raw_data_file)
  
  # Build global font collection for analysis and test display
  # This provides context across all logical documents
  all_text_blocks = [block for block in raw_data_file.content if hasattr(block, 'font_spans')]
  _, font_tags = extract_font_collection(all_text_blocks)
  
  print("Page Headers:")
  for page_header in page_headers:
        print(f"  {page_header}")

  # Create LogicalDocument objects from page_headers and raw_data_file
  logical_documents = []
  
  for page_header in page_headers:
    start_page = page_header['start_page']
    end_page = page_header['end_page']
    
    # Filter content blocks that fall within the page range (1-based)
    # Note: RawDataBlock.page is 0-based, so we need to convert
    logical_content = [
      block for block in raw_data_file.content
      if start_page <= block.page + 1 <= end_page
    ]
    
    # Build font collection for this logical document using extract_font_collection
    # Extract only TextBlocks for font analysis
    text_blocks = [block for block in logical_content if hasattr(block, 'font_spans')]
    
    # Build ANALYZED font collection (with role inference)
    font_collection_rich = extract_font_collection_rich(text_blocks)
    
    # Convert analyzed FontCollection back to legacy dict format
    # Include ALL fonts (even unclassified <?>) so normalization can look up any font
    font_collection = font_collection_rich.to_legacy_dict(include_unclassified=True)
    
    # Infer document type from title
    header_lower = page_header['header'].lower()
    if "information" in header_lower or "brochure" in header_lower:
      doc_type = "Information_Brochure"
    elif "consent" in header_lower:
      doc_type = "Consent_Form"
    elif "synopsis" in header_lower or "summary" in header_lower:
      doc_type = "Synopsis"
    elif "amendment" in header_lower:
      doc_type = "Amendment"
    else:
      doc_type = "Protocol"
    
    # Create LogicalDocument with analyzed font collection
    logical_doc = LogicalDocument(
      title=page_header['header'],
      type=doc_type,
      page_range=(start_page, end_page),
      font_collection=font_collection,  # Analyzed legacy dict (with <h1>, <h2>, <p>, etc.)
      font_collection_rich=font_collection_rich,  # Rich FontCollection object
      content=logical_content
    )
    
    logical_documents.append(logical_doc)
  
  print(f"\nCreated {len(logical_documents)} LogicalDocument(s):")
  for i, doc in enumerate(logical_documents):
    print(f"  Document {i+1}: Pages {doc.page_range[0]}-{doc.page_range[1]}, {len(doc.content)} blocks, {len(doc.font_collection)} fonts")
  
  # Show unique fonts across all logical documents
  all_unique_fonts = set()
  for doc in logical_documents:
    all_unique_fonts.update(doc.font_collection.keys())
  print(f"\nTotal unique font tags across all LogicalDocuments: {len(all_unique_fonts)}")
  
  # -----------------------------------------------------------------------------------
  # TEST MODE: Display diagnostics if enabled
  # -----------------------------------------------------------------------------------
  if test_mode:
    from test_harness.test_harness_utils import run_logical_docs_diagnostics
    run_logical_docs_diagnostics(logical_documents, font_tags, page_headers, prefix="Extracted")
  # -----------------------------------------------------------------------------------
  
  # Return logical documents along with font_tags and page_headers
  # These are needed downstream for normalization and test harness display
  return logical_documents, font_tags, page_headers
      
