"""
Test script to verify font collection analysis on real data.
This validates that the FontCollection properly identifies body text and headings.
"""

from _classes import FontCollection, FontSpan

def test_user_example():
    """Test with the actual font data from user's LogicalDocument example."""
    
    print("=" * 70)
    print("Testing Font Analysis on Real Data")
    print("=" * 70)
    print()
    
    # User's font collection data (from the example provided)
    user_fonts = {
        "Helvetica-10.0": 5192,
        "Arial-BoldMT-Bold-12.0": 639,
        "ArialMT-12.0": 57,
        "ArialMT-11.2": 163027,  # Should be <p> (88.1%)
        "Arial-BoldMT-Bold-11.2": 5407,  # Should be heading
        "SymbolMT-11.2": 121,
        "ArialMT-6.8": 273,
        "Arial-ItalicMT-Italic-11.2": 3792,
        "Arial-ItalicMT-Italic-6.8": 10,
        "Arial-BoldMT-Bold-9.0": 145,
        "SymbolMT-9.0": 1,
        "ArialMT-9.0": 284,
        "Arial-BoldItalicMT-Bold-Italic-11.2": 174,
        "TimesNewRomanPSMT-8.2": 1,
        "Arial-ItalicMT-Italic-8.2": 223,
        "ArialMT-8.2": 2545,
        "ArialMT-5.2": 27,
        "ArialMT-9.8": 284,
        "CourierNewPSMT-11.2": 3,
        "Times-Roman-9.1": 142,
        "Calibri-12.0": 2758,
        "Calibri-7.9": 6,
    }
    
    # Total chars
    total_chars = sum(user_fonts.values())
    
    # Build FontCollection manually (simulating extract_font_collection_rich)
    collection = FontCollection()
    
    for font_key, char_count in user_fonts.items():
        # Parse font_key to extract name and size
        parts = font_key.rsplit('-', 1)
        if len(parts) == 2:
            font_name = parts[0]
            try:
                font_size = float(parts[1])
            except ValueError:
                continue
        else:
            continue
        
        # Create a FontSpan and add to collection
        # We'll use a dummy span for this test
        span = FontSpan(
            text="",
            font_name=font_name,
            font_size=font_size,
            char_count=char_count
        )
        
        # Parse font properties
        name_lower = font_name.lower()
        span.font_family = font_name.split('-')[0] if '-' in font_name else font_name
        span.font_weight = "bold" if "bold" in name_lower else "normal"
        span.font_style = "italic" if "italic" in name_lower else "normal"
        span.is_monospace = "courier" in name_lower or "consolas" in name_lower
        span.is_symbol = "symbol" in name_lower
        
        collection.add_span(span)
    
    print(f"Font Collection: {len(collection.fonts)} fonts, {collection.total_chars:,} chars")
    print()
    
    # Analyze
    print("Running analysis...")
    collection.analyze()
    print()
    
    print(f"Analysis Results:")
    print(f"  Primary body font: {collection.primary_body_font}")
    print(f"  Heading fonts: {collection.heading_fonts}")
    print(f"  Size hierarchy: {collection.size_hierarchy}")
    print()
    
    # Show fonts sorted by usage
    print("Font Details (sorted by usage):")
    print("-" * 70)
    print(f"{'Font Key':<35} {'Role':<6} {'Usage':<8} {'Chars':<8} {'Spans'}")
    print("-" * 70)
    
    sorted_fonts = sorted(
        collection.fonts.items(), 
        key=lambda x: -x[1].char_count
    )
    
    for font_key, info in sorted_fonts:
        usage_pct = f"{info.usage_percentage:.1f}%"
        role_str = info.inferred_role
        
        # Highlight key fonts
        marker = ""
        if info.inferred_role == "<p>":
            marker = " ← BODY TEXT"
        elif info.inferred_role.startswith("<h"):
            marker = " ← HEADING"
        
        print(f"{font_key:<35} {role_str:<6} {usage_pct:<8} {info.char_count:<8} "
              f"{info.occurrence_count}{marker}")
    
    print()
    
    # Verify expectations
    print("=" * 70)
    print("Validation:")
    print("=" * 70)
    
    # Check ArialMT-11.2 is body text
    body_font_key = "ArialMT-11.2"
    if body_font_key in collection.fonts:
        body_role = collection.fonts[body_font_key].inferred_role
        if body_role == "<p>":
            print(f"✓ {body_font_key} correctly identified as <p> (body text)")
        else:
            print(f"✗ {body_font_key} should be <p> but got {body_role}")
    
    # Check Bold fonts are headings
    bold_12_key = "Arial-BoldMT-12.0"
    if bold_12_key in collection.fonts:
        bold_role = collection.fonts[bold_12_key].inferred_role
        if bold_role.startswith("<h"):
            print(f"✓ {bold_12_key} correctly identified as {bold_role} (heading)")
        else:
            print(f"✗ {bold_12_key} should be heading but got {bold_role}")
    
    print()
    
    # Convert to legacy dict for downstream use
    legacy_dict = collection.to_legacy_dict()
    print("Legacy Dict Format (for downstream processing):")
    print("-" * 70)
    for font_key, (tag, count) in list(legacy_dict.items())[:5]:
        print(f"  {font_key}: ('{tag}', {count})")
    print(f"  ... and {len(legacy_dict) - 5} more")
    print()
    
    print("=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_user_example()
