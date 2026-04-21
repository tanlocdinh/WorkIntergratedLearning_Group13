"""
Test to verify RawDataFile shows unanalyzed fonts vs LogicalDocument analyzed fonts.
"""

from _classes import FontCollection, FontSpan

def test_unanalyzed_vs_analyzed():
    """Compare unanalyzed (RawDataFile) vs analyzed (LogicalDocument) font collections."""
    
    print("=" * 70)
    print("Testing Unanalyzed vs Analyzed Font Collections")
    print("=" * 70)
    print()
    
    # Simulate user's font data
    sample_fonts = [
        ("Body text " * 100, "ArialMT", 11.2, 1100),
        ("Heading", "Arial-BoldMT", 12.0, 7),
        ("Subheading", "Arial-BoldMT", 11.2, 10),
        ("Symbol: •", "SymbolMT", 11.2, 2),
        ("Footer", "Helvetica", 10.0, 6),
    ]
    
    # 1. UNANALYZED (RawDataFile state)
    print("1. UNANALYZED (RawDataFile) - All fonts tagged <?>")
    print("-" * 70)
    
    unanalyzed_dict = {}
    total_chars_unanalyzed = 0
    
    for text, font_name, font_size, char_count in sample_fonts:
        key = f"{font_name}-{font_size}"
        unanalyzed_dict[key] = ("<?>", char_count)
        total_chars_unanalyzed += char_count
    
    for idx, (font_key, (tag, count)) in enumerate(unanalyzed_dict.items(), 1):
        pct = (count / total_chars_unanalyzed * 100)
        print(f"  {idx}. {font_key}: {count} ({pct:.1f}%) {tag}")
    
    print()
    
    # 2. ANALYZED (LogicalDocument state)
    print("2. ANALYZED (LogicalDocument) - Fonts classified")
    print("-" * 70)
    
    collection = FontCollection()
    for text, font_name, font_size, char_count in sample_fonts:
        span = FontSpan.from_tuple((text, font_name, font_size, char_count, 0))
        collection.add_span(span)
    
    collection.analyze()
    
    # Show ALL fonts (including <?>)
    print("All fonts in FontCollection.fonts (including <?>):")
    for idx, (font_key, info) in enumerate(collection.fonts.items(), 1):
        pct = info.usage_percentage
        print(f"  {idx}. {font_key}: {info.char_count} ({pct:.1f}%) {info.inferred_role}")
    
    print()
    
    # 3. LEGACY DICT (for downstream processing)
    print("3. LEGACY DICT (for downstream) - <?> tags EXCLUDED")
    print("-" * 70)
    
    legacy_dict = collection.to_legacy_dict(include_unclassified=False)
    
    for idx, (font_key, (tag, count)) in enumerate(legacy_dict.items(), 1):
        total_chars = collection.total_chars
        pct = (count / total_chars * 100) if total_chars > 0 else 0
        print(f"  {idx}. {font_key}: {count} ({pct:.1f}%) {tag}")
    
    print()
    print(f"Fonts in legacy dict: {len(legacy_dict)} (excluded {len(collection.fonts) - len(legacy_dict)} unclassified)")
    
    print()
    
    # 4. OPTIONAL: Include unclassified
    print("4. OPTIONAL: Legacy dict WITH <?> tags (include_unclassified=True)")
    print("-" * 70)
    
    legacy_dict_all = collection.to_legacy_dict(include_unclassified=True)
    
    for idx, (font_key, (tag, count)) in enumerate(legacy_dict_all.items(), 1):
        total_chars = collection.total_chars
        pct = (count / total_chars * 100) if total_chars > 0 else 0
        marker = " ← Would be ignored downstream" if tag == "<?>" else ""
        print(f"  {idx}. {font_key}: {count} ({pct:.1f}%) {tag}{marker}")
    
    print()
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    print("✓ RawDataFile: Shows all fonts with <?> (unanalyzed)")
    print("✓ LogicalDocument: Shows analyzed fonts with semantic tags")
    print("✓ Legacy dict (default): Excludes <?> for clean downstream processing")
    print("✓ FontCollection.fonts: Retains ALL fonts for debugging")
    print()


if __name__ == "__main__":
    test_unanalyzed_vs_analyzed()
