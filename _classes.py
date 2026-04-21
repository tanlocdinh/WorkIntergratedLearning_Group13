from dataclasses import dataclass, field
from typing import List, Tuple, Optional

## ----------------------- Phase 1 - Raw Data Extract ----------------------

@dataclass
class RawDataBlock:
  """
  Base class for different types of content blocks extracted from the PDF. Each block has a bounding box and page number for context.
  """
  bbox: Tuple[int, int, int, int]  # (x0, y0, x1, y1)
  page: int

  def __str__(self) -> str:
    return f"Page: {self.page} BBox: {self.bbox}"

@dataclass
class TextBlock(RawDataBlock):
  """
  Represents a block of text content extracted from the PDF, along with its bounding box and page number.
  """
  text: str  # Text content of the block 
  font_spans: List[Tuple[str, str, float, int, int]] # Font spans: (span_text, font_name, font_size, char_count, flags) before normalization, or List[str] of '<tag>text</tag>' after normalization
  
  # NEW: Rich font information (optional during transition)
  font_spans_rich: List['FontSpan'] = field(default_factory=list)

  def populate_rich_spans(self) -> None:
    """Populate font_spans_rich from font_spans."""
    self.font_spans_rich = [FontSpan.from_tuple(t) for t in self.font_spans]

  def __str__(self) -> str:
    return f"TextBlock: {super().__str__()} Text: {self.text[:30]}..."


@dataclass
class TableBlock(RawDataBlock):
  """
  Represents a table extracted from the PDF, including its caption (if available), headers, rows, bounding box, and page number.
  """
  data: List[List[str]]  # 2D list representing the table data - row[cell(row,col) value...]
  caption: str # Text that appears before/after the table and may be part of the caption
  cols: int
  rows: int
  first_data_row: int
  stub_header: str
  col_headers: List[str]
  row_headers: List[str]
  not_table_words: List[str]  # Words that are in the table block but not true table content

  def __str__(self) -> str:
    return f"TableBlock: {super().__str__()} Headers: {self.col_headers} Rows: {len(self.data)}"

@dataclass
class FigureBlock(RawDataBlock):
  """
  Represents a figure extracted from the PDF, including its caption (if available), bounding box, page number, and image data.
  """
  caption: str  # Text that appears before/after the figure and may be part of the caption
  image_data: bytes  # Raw image data extracted from the PDF
  image_type: str = "unknown"  # Image format (e.g., "png", "jpeg") or "unknown" if extraction failed
  width: float = 0.0  # Width in points
  height: float = 0.0  # Height in points

  def __str__(self) -> str:
    return f"FigureBlock: {super().__str__()} Type: {self.image_type} Size: {self.width:.0f}x{self.height:.0f} Caption: {self.caption[:30]}..."

@dataclass
class RawDataFile:
  """
  Represents the entire PDF document that has been processed to extract raw content blocks (text, tables, figures) along with their properties for downstream processing.
  """

  # A font collection that maps font properties to (tag, char_count) tuples for the entire document.
  # The tag is a string version of the font properties (e.g., "Times-18-Bold-Underlined" or "<?>"). The char_count tracks total characters using that font.
  # We can optionally map this to preliminary inferred roles across the document with a later step refining this mapping at a document or section level.
  font_collection: dict[str, tuple[str, int]]

  # A sorted list of all the raw content blocks (text, tables, figures) extracted from the PDF, along with their properties (e.g., bounding boxes, page numbers) for downstream processing.
  # the blocks are sorted in reading order based on their page numbers and bounding box positions to facilitate downstream processing such as sectioning and entity extraction.
  content: List[RawDataBlock]
  
  # NEW: Rich font collection (optional during transition)
  font_collection_rich: Optional['FontCollection'] = None
  
  def __str__(self) -> str:
    return f"RawDataFile: FontCollection: {list(self.font_collection.keys())[:5]}... Content Blocks: {len(self.content)}"

## ----------------------- Phase 1a Split File into Logical Documents ----------------------

@dataclass
class LogicalDocument:
  """
  Represents a logical document that may span multiple pages in the PDF, containing a collection of content blocks (text, tables, figures) that are associated with this logical document based on their properties (e.g., bounding boxes, page numbers).
  """

  # The page header giving rise to this document being identified as a logical document.
  title: str

  # The type of logical document (protocol, information brochure, etc).
  type: str

  # The page range in the original PDF that this logical document spans, which can be used to filter content blocks that belong to this document based on their page numbers.
  page_range: Tuple[int, int]

  # A font collection that maps font properties to (tag, char_count) tuples for this logical document only, which can be used to classify text blocks into heading levels and body text based on their font properties.
  font_collection: dict[str, tuple[str, int]]

  # A sorted list of all the raw content blocks (text, tables, figures) that belong to this logical document based on their page numbers and bounding box positions, along with their properties for downstream processing.
  content: List[RawDataBlock]
  
  # NEW: Rich font collection (optional during transition)
  font_collection_rich: Optional['FontCollection'] = None

  def __str__(self) -> str:
    return f"LogicalDocument: PageRange: {self.page_range} FontCollection: {list(self.font_collection.keys())[:5]}... Content Blocks: {len(self.content)}"


## ----------------------- Phase 2 Cleaning / Sectionizing ----------------------

@dataclass
class NormalizedSection:
  """
  Represents a section within a logical document.
  """

  # [document]_[start_page]_[index] - unique identifier for the section based on the document name, starting page number and index of the section on that page. This can be used to reference this section in downstream processing and to maintain the hierarchical structure of sections and subsections within the document.
  id: str

  # The original page number from the PDF document
  start_page: int

  # List of previous section titles that lead to this section,
  # which can be used to maintain the hierarchical structure of
  # sections and subsections within the document and to provide
  # context for entity extraction.
  previous_titles: List[str]

  # The identified title for this section.
  title: str

  # Content has been normalized to just text (so tables and
  # figures have been converted to text with captions) and
  # cleaned up (e.g., removing irrelevant content,
  # combining/splitting blocks as needed) to facilitate
  # downstream entity extraction.
  # If there 
  content: str

  def __str__(self) -> str:
    return f"normalizedSection: ID: {self.id} StartPage: {self.start_page} Title: {self.title[:30]}..."


@dataclass
class NormalizedDocument:
  """
  Represents a logical document that has been processed to identify sections based on the properties of the content blocks (e.g., font properties, bounding boxes) and organized into a hierarchical structure of sections and subsections.
  """
  sections: List[NormalizedSection]  # List of top-level sections in the document
  
  def __str__(self) -> str:
    return f"NormalizedDocument: Sections: {len(self.sections)}"


## ----------------------- Font Information Classes (New) ----------------------

@dataclass
class FontSpan:
  """Structured representation of a text span with font information."""
  text: str                    # The text content
  font_name: str               # Full font name (e.g., "TimesNewRomanPS-BoldMT")
  font_size: float             # Font size in points (rounded to 1 decimal)
  char_count: int              # Number of characters in this span
  flags: int = 0               # PyMuPDF font flags (bold=16, italic=2, serif=4, mono=8, superscript=1)
  
  # Properties derived from flags (more reliable than font name parsing)
  font_family: str = ""        # Base family (e.g., "TimesNewRoman")
  font_weight: str = "normal"  # "normal", "bold" (from flags)
  font_style: str = "normal"   # "normal", "italic" (from flags)
  is_monospace: bool = False   # From flags bit 3
  is_serif: bool = False       # From flags bit 2
  is_superscript: bool = False # From flags bit 0
  is_symbol: bool = False      # Symbol/Wingdings fonts
  
  @property
  def font_key(self) -> str:
    """Generate key for font collection: 'FontName-Size'"""
    return f"{self.font_name}-{self.font_size}"
  
  @classmethod
  def from_tuple(cls, span_tuple: Tuple) -> 'FontSpan':
    """Create FontSpan from tuple format (4-tuple legacy or 5-tuple with flags)."""
    # Handle both old 4-tuple and new 5-tuple formats
    if len(span_tuple) == 5:
      text, font_name, font_size, char_count, flags = span_tuple
    elif len(span_tuple) == 4:
      text, font_name, font_size, char_count = span_tuple
      flags = 0  # No flags available in legacy format
    else:
      raise ValueError(f"Invalid span tuple length: {len(span_tuple)}")
    
    # Extract properties from flags (more reliable than font name)
    is_bold = (flags & 16) != 0      # Bit 4
    is_italic = (flags & 2) != 0     # Bit 1
    is_monospace = (flags & 8) != 0  # Bit 3
    is_serif = (flags & 4) != 0      # Bit 2
    is_superscript = (flags & 1) != 0 # Bit 0
    
    # Detect symbol fonts from name
    name_lower = font_name.lower()
    is_symbol = "symbol" in name_lower or "wingding" in name_lower or "zapf" in name_lower
    
    # Fallback to font name parsing if flags not available
    if flags == 0:
      font_family, font_weight, font_style = cls._parse_font_name(font_name)
      if not is_monospace:
        is_monospace = "courier" in name_lower or "consolas" in name_lower
    else:
      # Use flags for weight and style
      font_family = font_name.split('-')[0] if '-' in font_name else font_name
      font_family = font_family.replace('PS', '').replace('MT', '')
      font_weight = "bold" if is_bold else "normal"
      font_style = "italic" if is_italic else "normal"
    
    return cls(
      text=text,
      font_name=font_name,
      font_size=font_size,
      char_count=char_count,
      flags=flags,
      font_family=font_family,
      font_weight=font_weight,
      font_style=font_style,
      is_monospace=is_monospace,
      is_serif=is_serif,
      is_superscript=is_superscript,
      is_symbol=is_symbol
    )
  
  def to_tuple(self) -> Tuple[str, str, float, int, int]:
    """Convert to tuple format with flags."""
    return (self.text, self.font_name, self.font_size, self.char_count, self.flags)
  
  @staticmethod
  def _parse_font_name(font_name: str) -> Tuple[str, str, str]:
    """Parse font name into family, weight, style.
    
    Examples:
      "TimesNewRomanPS-BoldMT" → ("TimesNewRoman", "bold", "normal")
      "Arial-ItalicMT" → ("Arial", "normal", "italic")
      "Helvetica-BoldOblique" → ("Helvetica", "bold", "oblique")
    """
    # Extract base font family (before first hyphen or MT suffix)
    family = font_name
    if '-' in font_name:
      family = font_name.split('-')[0]
    # Remove common suffixes
    family = family.replace('PS', '').replace('MT', '')
    
    name_lower = font_name.lower()
    weight = "bold" if "bold" in name_lower else "normal"
    style = "italic" if "italic" in name_lower or "oblique" in name_lower else "normal"
    
    return family, weight, style


@dataclass
class FontInfo:
  """Statistics and properties for a specific font."""
  font_name: str               # Full font name
  font_size: float             # Font size in points
  char_count: int              # Total characters using this font
  occurrence_count: int = 0    # Number of spans using this font
  
  # Derived properties (computed from font_name)
  font_family: str = ""
  font_weight: str = "normal"
  font_style: str = "normal"
  is_monospace: bool = False
  is_symbol: bool = False
  
  # Analysis fields (set by FontCollection)
  inferred_role: str = "<?>"   # "<h1>", "<h2>", "<p>", "<?>" etc.
  usage_percentage: float = 0.0  # Percentage of total text
  
  @property
  def font_key(self) -> str:
    """Generate key: 'FontName-Size'"""
    return f"{self.font_name}-{self.font_size}"
  
  @property
  def display_name(self) -> str:
    """Human-readable font description."""
    style_parts = []
    if self.font_weight != "normal":
      style_parts.append(self.font_weight)
    if self.font_style != "normal":
      style_parts.append(self.font_style)
    
    style_str = "-".join(style_parts) if style_parts else ""
    size_str = f"{self.font_size:.0f}pt"
    
    if style_str:
      return f"{self.font_family} {style_str} {size_str}"
    return f"{self.font_family} {size_str}"


@dataclass
class FontCollection:
  """Structured font collection with analysis capabilities."""
  
  fonts: dict[str, FontInfo] = field(default_factory=dict)  # font_key → FontInfo
  total_chars: int = 0
  
  # Analysis results (computed by analyze())
  primary_body_font: str = ""        # Most common body text font
  heading_fonts: List[str] = field(default_factory=list)  # Fonts identified as headings
  size_hierarchy: List[float] = field(default_factory=list)  # Sizes sorted largest to smallest
  
  def add_span(self, span: FontSpan) -> None:
    """Add a font span to the collection."""
    key = span.font_key
    
    if key not in self.fonts:
      self.fonts[key] = FontInfo(
        font_name=span.font_name,
        font_size=span.font_size,
        char_count=0,
        font_family=span.font_family,
        font_weight=span.font_weight,
        font_style=span.font_style,
        is_monospace=span.is_monospace,
        is_symbol=span.is_symbol
      )
    
    # Update counts
    self.fonts[key].char_count += span.char_count
    self.fonts[key].occurrence_count += 1
    self.total_chars += span.char_count
  
  def analyze(self) -> None:
    """Analyze font collection to infer roles and hierarchy."""
    if not self.fonts:
      return
    
    # Calculate usage percentages
    for font in self.fonts.values():
      font.usage_percentage = (font.char_count / self.total_chars * 100) if self.total_chars > 0 else 0
    
    # Build size hierarchy (largest to smallest)
    self.size_hierarchy = sorted(
      set(f.font_size for f in self.fonts.values()),
      reverse=True
    )
    
    # Infer roles based on size, usage, and properties
    self._infer_font_roles()
  
  def _infer_font_roles(self) -> None:
    """Infer semantic roles (heading levels, body text) for fonts."""
    # Filter out symbol/monospace fonts from heading analysis
    text_fonts = [f for f in self.fonts.values() if not f.is_symbol]
    
    if not text_fonts:
      return
    
    # Find most common font as body text candidate
    body_candidate = max(text_fonts, key=lambda f: f.char_count)
    if body_candidate.usage_percentage > 30:  # Threshold for body text
      body_candidate.inferred_role = "<p>"
      self.primary_body_font = body_candidate.font_key
    
    # Sort by size (descending) then by usage
    sorted_fonts = sorted(
      text_fonts,
      key=lambda f: (-f.font_size, -f.char_count)
    )
    
    # Assign heading levels to larger fonts
    heading_level = 1
    for font in sorted_fonts:
      if font.inferred_role == "<p>":  # Skip body text
        continue
      # Check if significantly larger than body or has distinctive weight
      if font.font_size > body_candidate.font_size or font.font_weight == "bold":
        if heading_level <= 6:
          font.inferred_role = f"<h{heading_level}>"
          self.heading_fonts.append(font.font_key)
          heading_level += 1
    
    # Classify remaining small fonts (likely annotations, footnotes, captions)
    # Don't classify symbols - they remain as <?>
    for font in text_fonts:
      if font.inferred_role == "<?>" and not font.is_symbol:
        # Small fonts (< body text size) or very small (< 9pt)
        if font.font_size < body_candidate.font_size or font.font_size < 9.0:
          font.inferred_role = "<p>"
  
  def to_legacy_dict(self, include_unclassified: bool = False) -> dict[str, tuple[str, int]]:
    """Convert to legacy dict format for backward compatibility.
    
    Args:
        include_unclassified: If False (default), exclude fonts tagged as "<?>"
                            If True, include all fonts regardless of tag
    
    Returns:
        dict mapping font_key to (tag, char_count) for classified fonts only
    """
    return {
      key: (info.inferred_role, info.char_count)
      for key, info in self.fonts.items()
      if include_unclassified or info.inferred_role != "<?>"
    }
  
  @classmethod
  def from_legacy_dict(cls, legacy_dict: dict[str, tuple[str, int]]) -> 'FontCollection':
    """Create FontCollection from legacy dict format."""
    collection = cls()
    
    for font_key, (tag, char_count) in legacy_dict.items():
      # Parse font_key: "FontName-Size"
      parts = font_key.rsplit('-', 1)
      if len(parts) == 2:
        font_name = parts[0]
        try:
          font_size = float(parts[1])
        except ValueError:
          font_size = 12.0
      else:
        font_name = font_key
        font_size = 12.0
      
      # Create FontInfo
      font_family, font_weight, font_style = FontSpan._parse_font_name(font_name)
      
      collection.fonts[font_key] = FontInfo(
        font_name=font_name,
        font_size=font_size,
        char_count=char_count,
        font_family=font_family,
        font_weight=font_weight,
        font_style=font_style,
        inferred_role=tag
      )
      collection.total_chars += char_count
    
    return collection
  
  def __str__(self) -> str:
    return f"FontCollection: {len(self.fonts)} fonts, {self.total_chars} chars"
  

