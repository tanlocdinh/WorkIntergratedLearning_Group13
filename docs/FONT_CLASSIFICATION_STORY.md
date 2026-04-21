# Font Classification System: Architecture & Usage

## What We Built

A semantic font classification system that transforms raw PDF font metadata into structured document understanding.

### The Problem
Raw font extraction produced unstructured tuples with no semantic meaning—every font tagged `<?>` (unknown).

### The Solution
Automatic role inference that classifies fonts based on size, weight, usage patterns, and type.

---

## Architecture

### Phase 1: Raw Extraction (RawDataFile)
**Purpose**: Clean data extraction without interpretation

```python
raw_data_file.font_collection = {
    "ArialMT-11.2": ("<?>", 163027),     # 88.1% - unclassified
    "Arial-BoldMT-12.0": ("<?>", 639),   # 0.3% - unclassified
    ...all 22 fonts tagged <?>
}
```

- Extracts font spans: `(text, font_name, font_size, char_count, flags)`
- Font collection remains unanalyzed
- Total: 185,111 characters across 22 fonts

### Phase 2: Semantic Analysis (LogicalDocument)
**Purpose**: Infer document structure from font usage

```python
logical_doc.font_collection = {
    "ArialMT-11.2": ("<p>", 163027),      # Body text!
    "Arial-BoldMT-12.0": ("<h2>", 639),   # Heading!
    ...15 classified fonts, 7 excluded
}
```

**Analysis Logic**:
1. Calculate usage percentages
2. Identify body text (highest usage, typically >30%)
3. Classify larger/bold fonts as headings (`<h1>` through `<h6>`)
4. Exclude symbols, monospace, different font families
5. Filter out `<?>` tags from legacy dict by default

**Coverage**: 
- 95% of content properly tagged (`<p>`, `<h1>`-`<h6>`)
- 5% noise automatically filtered (symbols, headers, footers)

### Phase 3: Clean Export
**Purpose**: Provide clean data to downstream processors

```python
# Default: exclude unclassified
logical_doc.font_collection_rich.to_legacy_dict()
# Returns only classified fonts

# Optional: include all
logical_doc.font_collection_rich.to_legacy_dict(include_unclassified=True)
# Returns all fonts including <?>
```

---

## Classes

### FontSpan
Structured representation of a text span with parsed font properties.

**Fields**:
- Basic: `text`, `font_name`, `font_size`, `char_count`, `flags`
- Parsed: `font_family`, `font_weight`, `font_style`
- Boolean: `is_bold`, `is_italic`, `is_monospace`, `is_symbol`

**Methods**:
- `from_tuple()`: Create from legacy tuple format
- `to_tuple()`: Convert back to tuple
- `font_key`: Property returning "FontName-Size"

### FontInfo
Statistics and properties for a specific font.

**Fields**:
- Metrics: `char_count`, `occurrence_count`, `usage_percentage`
- Properties: `font_family`, `font_weight`, `font_style`
- Analysis: `inferred_role` (`<h1>`, `<p>`, `<?>`, etc.)

### FontCollection
Analysis engine with role inference capabilities.

**Fields**:
- `fonts`: Dict of font_key → FontInfo
- `total_chars`: Total character count
- `primary_body_font`: Most common body text font
- `heading_fonts`: List of identified heading fonts
- `size_hierarchy`: Font sizes sorted largest to smallest

**Methods**:
- `add_span(span)`: Add a FontSpan to collection
- `analyze()`: Infer semantic roles for all fonts
- `to_legacy_dict(include_unclassified=False)`: Export to dict format
- `from_legacy_dict(dict)`: Import from dict format

---

## Helper Functions (font_collection.py)

### extract_font_collection(blocks)
Build unanalyzed font collection from raw blocks.
```python
font_collection, font_tags = extract_font_collection(blocks)
# All fonts tagged <?>
```

### extract_font_collection_rich(blocks)
Build analyzed FontCollection with role inference.
```python
collection = extract_font_collection_rich(blocks)
# Returns FontCollection with .analyze() already called
```

### get_font_tag(font_name, font_size, font_collection)
Lookup semantic tag for a font.
```python
tag = get_font_tag("ArialMT", 11.2, doc.font_collection)
# Returns: "<p>"
```

### tag_font_spans(font_spans, font_collection)
Convert font spans to (text, tag) tuples.
```python
tagged = tag_font_spans(block.font_spans, doc.font_collection)
# Returns: [("Heading", "<h1>"), ("Body", "<p>"), ...]
```

---

## How to Use Downstream

### 1. Identify Text Block Roles (_normalize.py)

```python
from font_collection import tag_font_spans

# Tag all spans in a block
tagged_spans = tag_font_spans(block.font_spans, doc.font_collection)

# Get dominant tag
tag_counts = {}
for text, tag in tagged_spans:
    tag_counts[tag] = tag_counts.get(tag, 0) + len(text)
dominant_tag = max(tag_counts, key=tag_counts.get)

if dominant_tag == "<p>":
    # Process as body text paragraph
    merge_with_previous_paragraph(block)
elif dominant_tag.startswith("<h"):
    # This is a heading - create section break
    level = int(dominant_tag[2])
    create_new_section(block, level=level)
# Fonts not in collection are automatically ignored
```

### 2. Smart Block Merging

```python
def both_blocks_are_body_text(block1, block2, font_collection):
    """Check if both blocks are primarily body text."""
    tag1 = get_dominant_tag(block1, font_collection)
    tag2 = get_dominant_tag(block2, font_collection)
    return tag1 == "<p>" and tag2 == "<p>"

# Merge adjacent body text blocks
if both_blocks_are_body_text(block1, block2, doc.font_collection):
    merge_blocks(block1, block2)
```

### 3. Header/Footer Detection

```python
def is_header_or_footer(block, font_collection):
    """Detect if block is likely header/footer noise."""
    # If no fonts from block are in the analyzed collection
    for span in block.font_spans:
        font_name, font_size = span[1], span[2]
        font_key = f"{font_name}-{font_size}"
        if font_key in font_collection:
            return False  # Has classified fonts
    return True  # All fonts unclassified = likely noise

# Remove headers/footers
if is_header_or_footer(block, doc.font_collection):
    skip_block(block)
```

### 4. Build Section Hierarchy

```python
from font_collection import get_font_tag

sections = []
current_section = None

for block in doc.content:
    # Get dominant tag for block
    dominant_tag = get_dominant_tag(block, doc.font_collection)
    
    if dominant_tag == "<h1>":
        current_section = Section(level=1, title=block.text)
        sections.append(current_section)
    elif dominant_tag == "<h2>":
        subsection = Section(level=2, title=block.text)
        current_section.add_child(subsection)
    elif dominant_tag == "<p>":
        current_section.add_content(block.text)
    # <?> tags and fonts not in collection are ignored automatically
```

---

## Next Steps

### Immediate (_normalize.py)
1. **Tag text blocks** using `tag_font_spans()`
2. **Filter `<?>` spans** before processing
3. **Group consecutive `<p>` spans** into paragraphs
4. **Detect headings** for section boundaries
5. **Remove headers/footers** (blocks with no classified fonts)

### Soon After (section splitting)
6. **Build section tree** using heading hierarchy
7. **Merge `<p>` blocks** between same-level headings
8. **Associate tables/figures** with nearest heading based on proximity

### Future Enhancements
9. **Italic emphasis** (could tag Arial-ItalicMT-11.2 as `<em>`)
10. **List detection** (combine with indentation patterns)
11. **Caption association** (small fonts near tables/figures)
12. **Content type classification** (narrative vs data summaries)

---

## Design Principles

✓ **Progressive refinement**: Unanalyzed → Analyzed  
✓ **Automatic noise filtering**: Missing from dict = ignored  
✓ **Simple downstream logic**: Just check if font in collection  
✓ **Backward compatible**: Works with legacy tuple format  
✓ **Debugging friendly**: Rich FontCollection retains all data  
✓ **No manual configuration**: Analysis is fully automatic

---

## Test Files

- `test_font_classes.py` - Unit tests for FontSpan/FontInfo/FontCollection
- `test_font_analysis.py` - Validation with real 22-font document data
- `test_font_states.py` - Demonstrates unanalyzed → analyzed progression
- `test_exclude_unclassified.py` - Validates `<?>` filtering

---

## Example Output

**Your Document Analysis**:
```
Font Collection (15 entries) [ANALYZED]:
  1. ArialMT-11.2: 163027 (88.1%) <p>     ← Body text
  2. Calibri-12.0: 2758 (1.5%) <h1>       ← Main heading
  3. Arial-BoldMT-12.0: 639 (0.3%) <h2>   ← Subheading
  4. Arial-BoldMT-11.2: 5407 (2.9%) <h4>  ← Minor heading
  ...
  (7 fonts with <?> excluded automatically)
```

**Coverage**: 95% of meaningful content properly tagged, 5% noise filtered.

---

*Last updated: March 6, 2026*
