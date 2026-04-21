# Font Classes Design Document

## Overview
This document describes new font-related dataclasses to add alongside existing structures in `_classes.py`. The design maintains backward compatibility while providing richer font information.

## Design Principles
1. **Additive Only** - Keep all existing classes and fields unchanged
2. **Parallel Structures** - New classes live alongside old tuples temporarily
3. **Gradual Migration** - Code can use old or new format during transition
4. **Type Safety** - Replace tuples with structured dataclasses

---

## New Dataclasses

### 1. FontSpan (replaces tuple format)
**Current format:** `Tuple[str, str, float, int]` = (text, font_name, font_size, char_count)

**New structured format:**
```python
@dataclass
class FontSpan:
    """Structured representation of a text span with font information."""
    text: str                    # The text content
    font_name: str               # Full font name (e.g., "TimesNewRomanPS-BoldMT")
    font_size: float             # Font size in points
    char_count: int              # Number of characters in this span
    
    # Additional extracted properties
    font_family: str = ""        # Base family (e.g., "TimesNewRoman")
    font_weight: str = "normal"  # "normal", "bold", "black", etc.
    font_style: str = "normal"   # "normal", "italic", "oblique"
    is_monospace: bool = False   # Courier, Consolas, etc.
    is_symbol: bool = False      # Symbol, Wingdings, etc.
    
    @property
    def font_key(self) -> str:
        """Generate key for font collection: 'FontName-Size'"""
        return f"{self.font_name}-{self.font_size}"
    
    @classmethod
    def from_tuple(cls, span_tuple: Tuple[str, str, float, int]) -> 'FontSpan':
        """Create FontSpan from legacy tuple format."""
        text, font_name, font_size, char_count = span_tuple
        
        # Parse font properties from font_name
        font_family, font_weight, font_style = cls._parse_font_name(font_name)
        is_monospace = "courier" in font_name.lower() or "consolas" in font_name.lower()
        is_symbol = "symbol" in font_name.lower() or "wingding" in font_name.lower()
        
        return cls(
            text=text,
            font_name=font_name,
            font_size=font_size,
            char_count=char_count,
            font_family=font_family,
            font_weight=font_weight,
            font_style=font_style,
            is_monospace=is_monospace,
            is_symbol=is_symbol
        )
    
    def to_tuple(self) -> Tuple[str, str, float, int]:
        """Convert back to legacy tuple format for compatibility."""
        return (self.text, self.font_name, self.font_size, self.char_count)
    
    @staticmethod
    def _parse_font_name(font_name: str) -> Tuple[str, str, str]:
        """Parse font name into family, weight, style.
        
        Examples:
            "TimesNewRomanPS-BoldMT" → ("TimesNewRoman", "bold", "normal")
            "Arial-ItalicMT" → ("Arial", "normal", "italic")
            "Helvetica-BoldOblique" → ("Helvetica", "bold", "oblique")
        """
        # Implementation will parse font naming conventions
        # This is a placeholder for the parsing logic
        family = font_name.split('-')[0] if '-' in font_name else font_name
        
        name_lower = font_name.lower()
        weight = "bold" if "bold" in name_lower else "normal"
        style = "italic" if "italic" in name_lower or "oblique" in name_lower else "normal"
        
        return family, weight, style
```

### 2. FontInfo (font usage statistics)
```python
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
```

### 3. FontCollection (replaces dict format)
**Current format:** `dict[str, tuple[str, int]]` = {"font-size": (tag, char_count)}

**New structured format:**
```python
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
        
        # Sort by size (descending) then by usage
        sorted_fonts = sorted(
            text_fonts,
            key=lambda f: (-f.font_size, -f.char_count)
        )
        
        # Find most common font as body text
        if sorted_fonts:
            body_candidate = max(text_fonts, key=lambda f: f.char_count)
            if body_candidate.usage_percentage > 30:  # Threshold for body text
                body_candidate.inferred_role = "<p>"
                self.primary_body_font = body_candidate.font_key
        
        # Assign heading levels to larger fonts
        heading_level = 1
        for font in sorted_fonts:
            if font.inferred_role == "<p>":  # Skip body text
                continue
            if font.font_size > 0 and font != body_candidate:
                # Check if significantly larger than body or has distinctive weight
                if heading_level <= 6:
                    font.inferred_role = f"<h{heading_level}>"
                    self.heading_fonts.append(font.font_key)
                    heading_level += 1
    
    def to_legacy_dict(self) -> dict[str, tuple[str, int]]:
        """Convert to legacy dict format for backward compatibility."""
        return {
            key: (info.inferred_role, info.char_count)
            for key, info in self.fonts.items()
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
```

---

## Integration Strategy

### Phase 1: Add New Classes to _classes.py
Add new classes at the bottom of the file with clear section header:
```python
## ----------------------- Font Information Classes (New) ----------------------
```

### Phase 2: Update TextBlock (Additive)
```python
@dataclass
class TextBlock(RawDataBlock):
    text: str
    font_spans: List[Tuple[str, str, float, int]]  # KEEP EXISTING
    
    # NEW: Rich font information (optional during transition)
    font_spans_rich: List[FontSpan] = field(default_factory=list)
    
    def populate_rich_spans(self) -> None:
        """Populate font_spans_rich from font_spans."""
        self.font_spans_rich = [FontSpan.from_tuple(t) for t in self.font_spans]
```

### Phase 3: Update RawDataFile & LogicalDocument (Additive)
```python
@dataclass
class RawDataFile:
    font_collection: dict[str, tuple[str, int]]  # KEEP EXISTING
    content: List[RawDataBlock]
    
    # NEW: Rich font collection (optional during transition)
    font_collection_rich: Optional[FontCollection] = None

@dataclass
class LogicalDocument:
    title: str
    type: str
    page_range: Tuple[int, int]
    font_collection: dict[str, tuple[str, int]]  # KEEP EXISTING
    content: List[RawDataBlock]
    
    # NEW: Rich font collection (optional during transition)
    font_collection_rich: Optional[FontCollection] = None
```

### Phase 4: Update font_collection.py
Add new function alongside existing:
```python
def extract_font_collection_rich(blocks: List[RawDataBlock]) -> FontCollection:
    """Build a rich FontCollection from extracted blocks."""
    collection = FontCollection()
    
    for block in blocks:
        if hasattr(block, 'font_spans'):
            for span_tuple in block.font_spans:
                span = FontSpan.from_tuple(span_tuple)
                collection.add_span(span)
    
    collection.analyze()  # Infer roles
    return collection
```

---

## Migration Checklist

- [ ] Add new classes to _classes.py
- [ ] Add optional new fields to TextBlock, RawDataFile, LogicalDocument
- [ ] Create extract_font_collection_rich() in font_collection.py
- [ ] Update _extract_raw_data.py to populate both formats
- [ ] Update _split_logical_docs.py to populate both formats
- [ ] Test with existing PDFs - verify backward compatibility
- [ ] Gradually update consuming code to use rich format
- [ ] Remove legacy fields once fully migrated

---

## Benefits

1. **Type Safety** - No more tuple unpacking errors
2. **Rich Metadata** - Font family, weight, style parsed automatically
3. **Better Analysis** - Smart role inference in FontCollection
4. **Backward Compatible** - Can convert to/from legacy format
5. **Gradual Migration** - No big bang required
6. **Self-Documenting** - Clear field names vs. positional tuple access

---

## Example Usage (Post-Migration)

```python
# Extract text with both formats
text_block = extract_text_blocks(page, table_bboxes, header_threshold, footer_threshold)

# Populate rich format
text_block.populate_rich_spans()

# Work with rich format
for span in text_block.font_spans_rich:
    if span.font_weight == "bold" and span.font_size > 14:
        print(f"Likely heading: {span.text}")
    if span.is_monospace:
        print(f"Code/data: {span.text}")

# Build rich collection
collection = extract_font_collection_rich(text_blocks)
print(f"Primary body font: {collection.primary_body_font}")
print(f"Heading fonts: {collection.heading_fonts}")

# Still works with legacy code
legacy_dict = collection.to_legacy_dict()
```
