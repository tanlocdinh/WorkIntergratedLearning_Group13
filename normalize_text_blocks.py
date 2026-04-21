from typing import List
import re
from _classes import RawDataBlock, TextBlock
from font_collection import get_font_tag


def _merge_tagged_spans(tagged_spans: List[str]) -> List[str]:
  """
  Merge consecutive tagged spans with the same tag.
  Joins text content with spaces.
  
  Args:
    tagged_spans: List of '<tag>text</tag>' strings
    
  Returns:
    List of merged tagged strings
  """
  if not tagged_spans:
    return []
  
  merged = []
  current_texts = []
  current_tag = None
  
  for tagged_span in tagged_spans:
    # Extract tag and text from '<tag>text</tag>'
    match = re.match(r'^<(\w+)>(.+?)</\1>$', tagged_span)
    if not match:
      continue
    
    tag, text = match.groups()
    
    normalized_tag = tag
    
    if current_tag is None:
      # First span
      current_tag = normalized_tag
      current_texts.append(text)
    elif normalized_tag == current_tag:
      # Same tag: accumulate text
      current_texts.append(text)
    else:
      # Different tag: flush accumulated text
      merged_text = ' '.join(current_texts)
      merged.append(f"<{current_tag}>{merged_text}</{current_tag}>")
      
      # Start new accumulation
      current_tag = normalized_tag
      current_texts = [text]
  
  # Flush final accumulated text
  if current_texts and current_tag:
    merged_text = ' '.join(current_texts)
    merged.append(f"<{current_tag}>{merged_text}</{current_tag}>")
  
  return merged


def normalize_text_blocks(blocks: List[RawDataBlock], font_tags: dict[str, str]) -> List[RawDataBlock]:
  """
  Normalize text blocks by converting font spans to tagged strings and merging.
  
  - Filters out spans with <?> tags (symbol fonts - noise)
  - Converts each span to '<tag>text</tag>' format
  - Merges consecutive spans with same tag
  - Joins merged text content with spaces
  
  Args:
    blocks: List of RawDataBlock instances
    font_tags: Font collection dict mapping font_key to (tag, char_count)
  
  Returns:
    List of normalized blocks with merged tagged font_spans
  """
  normalized_blocks = []
  
  for block in blocks:
    # Only process TextBlock instances (they have font_spans)
    if not isinstance(block, TextBlock):
      normalized_blocks.append(block)
      continue
    
    # Convert each font span to tagged string format
    tagged_spans = []
    filtered_text_parts = []
    
    for span in block.font_spans:
      # Unpack span: (span_text, font_name, font_size, char_count, flags)
      span_text, font_name, font_size, char_count, flags = span
      
      # Lookup semantic tag
      tag = get_font_tag(font_name, font_size, font_tags)
      
      # Filter out noise (<?> = symbol fonts only)
      if tag == "<?>":
        continue
      
      # Wrap span text with tag: <tag>text</tag>
      tagged_span = f"{tag}{span_text}{tag.replace('<', '</')}"
      tagged_spans.append(tagged_span)
      filtered_text_parts.append(span_text)
    
    # If no spans remain after filtering, skip this block
    if not tagged_spans:
      continue
    
    # Merge consecutive spans with same tag
    merged_spans = _merge_tagged_spans(tagged_spans)
    
    # Reconstruct plain text
    normalized_text = ''.join(filtered_text_parts)
    
    # Create normalized block with merged tagged font_spans
    normalized_block = TextBlock(
      page=block.page,
      bbox=block.bbox,
      text=normalized_text,
      font_spans=merged_spans  # Merged list of tagged strings
    )
    
    normalized_blocks.append(normalized_block)
  
  return normalized_blocks