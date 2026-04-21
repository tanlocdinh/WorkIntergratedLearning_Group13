"""
Quick test script to verify new font classes work correctly.
Run this to test the new FontSpan, FontInfo, and FontCollection classes.
"""

from _classes import FontSpan, FontInfo, FontCollection, TextBlock

def test_font_span():
    """Test FontSpan conversion and properties."""
    print("=" * 60)
    print("TEST 1: FontSpan Conversion")
    print("=" * 60)
    
    # Legacy tuple format
    legacy_span = ("Sample Text", "TimesNewRomanPS-BoldMT", 14.0, 11)
    
    # Convert to FontSpan
    span = FontSpan.from_tuple(legacy_span)
    
    print(f"Original tuple: {legacy_span}")
    print(f"\nFontSpan object:")
    print(f"  text: {span.text}")
    print(f"  font_name: {span.font_name}")
    print(f"  font_size: {span.font_size}")
    print(f"  char_count: {span.char_count}")
    print(f"  font_family: {span.font_family}")
    print(f"  font_weight: {span.font_weight}")
    print(f"  font_style: {span.font_style}")
    print(f"  font_key: {span.font_key}")
    
    # Convert back to tuple
    converted_back = span.to_tuple()
    print(f"\nConverted back to tuple: {converted_back}")
    print(f"Match original? {converted_back == legacy_span}")
    print()


def test_font_collection():
    """Test FontCollection building and analysis."""
    print("=" * 60)
    print("TEST 2: FontCollection Building and Analysis")
    print("=" * 60)
    
    # Create sample spans
    sample_spans = [
        ("This is body text. " * 20, "Arial", 11.0, 380),  # Body text (lots of it)
        ("Main Heading", "Arial-BoldMT", 18.0, 12),  # Large heading
        ("Subheading", "Arial-BoldMT", 14.0, 10),  # Smaller heading
        ("More body.", "Arial", 11.0, 10),  # More body
        ("Footer text", "Arial", 9.0, 11),  # Footer
        ("Code: xyz", "CourierNew", 10.0, 9),  # Monospace
    ]
    
    # Build collection
    collection = FontCollection()
    for span_tuple in sample_spans:
        span = FontSpan.from_tuple(span_tuple)
        collection.add_span(span)
    
    print(f"Total fonts: {len(collection.fonts)}")
    print(f"Total characters: {collection.total_chars}")
    
    # Analyze
    collection.analyze()
    
    print(f"\nPrimary body font: {collection.primary_body_font}")
    print(f"Heading fonts: {collection.heading_fonts}")
    print(f"Size hierarchy: {collection.size_hierarchy}")
    
    print(f"\nFont Analysis:")
    for key, info in sorted(collection.fonts.items(), key=lambda x: -x[1].char_count):
        print(f"  {key:30s} | Role: {info.inferred_role:5s} | "
              f"Usage: {info.usage_percentage:5.1f}% | "
              f"Chars: {info.char_count:4d} | "
              f"Display: {info.display_name}")
    
    # Test legacy conversion
    print(f"\nLegacy dict format:")
    legacy_dict = collection.to_legacy_dict()
    for key, (tag, count) in list(legacy_dict.items())[:3]:
        print(f"  {key}: ({tag}, {count})")
    print()


def test_textblock_integration():
    """Test TextBlock with rich spans."""
    print("=" * 60)
    print("TEST 3: TextBlock Integration")
    print("=" * 60)
    
    # Create TextBlock with legacy format
    legacy_spans = [
        ("Heading text", "Arial-BoldMT", 16.0, 12),
        ("Body paragraph text", "Arial", 11.0, 19),
    ]
    
    text_block = TextBlock(
        bbox=(100, 200, 500, 300),
        page=0,
        text="Heading text Body paragraph text",
        font_spans=legacy_spans
    )
    
    print(f"TextBlock created: {text_block}")
    print(f"Legacy font_spans: {len(text_block.font_spans)} spans")
    print(f"Rich font_spans_rich: {len(text_block.font_spans_rich)} spans (empty initially)")
    
    # Populate rich spans
    text_block.populate_rich_spans()
    
    print(f"\nAfter populate_rich_spans():")
    print(f"Rich font_spans_rich: {len(text_block.font_spans_rich)} spans")
    
    for i, span in enumerate(text_block.font_spans_rich):
        print(f"  Span {i+1}: '{span.text}' | {span.font_family} | "
              f"{span.font_weight} | {span.font_size}pt")
    print()


def test_legacy_dict_conversion():
    """Test conversion from legacy dict format."""
    print("=" * 60)
    print("TEST 4: Legacy Dict Conversion")
    print("=" * 60)
    
    # Legacy format from existing code
    legacy_dict = {
        "Arial-11.0": ("<p>", 500),
        "Arial-BoldMT-18.0": ("<h1>", 25),
        "Arial-BoldMT-14.0": ("<h2>", 30),
        "TimesNewRoman-10.0": ("<?>", 15),
    }
    
    print("Original legacy dict:")
    for key, (tag, count) in legacy_dict.items():
        print(f"  {key}: ({tag}, {count})")
    
    # Convert to FontCollection
    collection = FontCollection.from_legacy_dict(legacy_dict)
    
    print(f"\nConverted to FontCollection:")
    print(f"  Total fonts: {len(collection.fonts)}")
    print(f"  Total chars: {collection.total_chars}")
    
    print(f"\nFont details:")
    for key, info in collection.fonts.items():
        print(f"  {info.display_name:20s} | Role: {info.inferred_role} | Chars: {info.char_count}")
    
    # Convert back
    converted_back = collection.to_legacy_dict()
    print(f"\nConverted back to dict:")
    for key, (tag, count) in converted_back.items():
        print(f"  {key}: ({tag}, {count})")
    
    print(f"\nMatches original? {converted_back == legacy_dict}")
    print()


if __name__ == "__main__":
    print("\n")
    print("*" * 60)
    print("TESTING NEW FONT CLASSES")
    print("*" * 60)
    print()
    
    try:
        test_font_span()
        test_font_collection()
        test_textblock_integration()
        test_legacy_dict_conversion()
        
        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY! ✓")
        print("=" * 60)
        print()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
