"""
Test that unclassified fonts (<?>) are excluded from legacy dict by default.
"""

from _classes import FontCollection, FontSpan

def test_exclude_unclassified():
    """Test that <?> fonts are excluded by default."""
    
    print("=" * 70)
    print("Testing Exclusion of Unclassified Fonts")
    print("=" * 70)
    print()
    
    # Create sample font data
    fonts_data = [
        ("Body text " * 50, "ArialMT", 11.2, 400),  # Should be <p>
        ("Heading", "Arial-BoldMT", 12.0, 12),      # Should be heading
        ("Symbol •", "SymbolMT", 11.2, 10),         # Should be <?>
        ("Footer", "Helvetica", 10.0, 50),          # Should be <?>
        ("Caption", "ArialMT", 8.0, 40),            # Should be <?>
    ]
    
    collection = FontCollection()
    
    for text, font_name, font_size, char_count in fonts_data:
        span = FontSpan.from_tuple((text, font_name, font_size, char_count, 0))
        collection.add_span(span)
    
    # Analyze
    collection.analyze()
    
    print(f"Total fonts in rich collection: {len(collection.fonts)}")
    print()
    
    # Show all fonts with their roles
    print("All fonts in FontCollection (rich):")
    print("-" * 70)
    for key, info in collection.fonts.items():
        print(f"  {key:30s} → {info.inferred_role:5s} ({info.char_count} chars)")
    print()
    
    # Get legacy dict WITHOUT unclassified (default)
    legacy_clean = collection.to_legacy_dict()
    
    print(f"Legacy dict (exclude_unclassified=False, DEFAULT):")
    print("-" * 70)
    print(f"  Total fonts: {len(legacy_clean)}")
    for key, (tag, count) in legacy_clean.items():
        print(f"  {key:30s} → {tag:5s} ({count} chars)")
    print()
    
    # Get legacy dict WITH unclassified
    legacy_full = collection.to_legacy_dict(include_unclassified=True)
    
    print(f"Legacy dict (include_unclassified=True):")
    print("-" * 70)
    print(f"  Total fonts: {len(legacy_full)}")
    for key, (tag, count) in legacy_full.items():
        print(f"  {key:30s} → {tag:5s} ({count} chars)")
    print()
    
    # Verify expectations
    print("=" * 70)
    print("Validation:")
    print("=" * 70)
    
    # Check that clean dict excludes <?>
    has_unknown = any(tag == "<?>" for tag, _ in legacy_clean.values())
    if not has_unknown:
        print("✓ Default legacy dict excludes all <?> tags")
    else:
        print("✗ Default legacy dict still has <?> tags")
    
    # Check that full dict includes <?>
    has_unknown_full = any(tag == "<?>" for tag, _ in legacy_full.values())
    if has_unknown_full:
        print("✓ Full legacy dict includes <?> tags when requested")
    else:
        print("✗ Full legacy dict missing <?> tags")
    
    # Check that classified fonts are in both
    classified_count = sum(1 for info in collection.fonts.values() if info.inferred_role != "<?>")
    if len(legacy_clean) == classified_count:
        print(f"✓ Clean dict has exactly {classified_count} classified fonts")
    else:
        print(f"✗ Clean dict has {len(legacy_clean)} fonts, expected {classified_count}")
    
    print()
    
    # Demonstrate downstream usage
    print("=" * 70)
    print("Downstream Usage Example:")
    print("=" * 70)
    print()
    
    # Simulate processing font spans
    from font_collection import tag_font_spans
    
    sample_spans = [
        ("Heading Text", "Arial-BoldMT", 12.0, 12, 0),
        ("Body paragraph text here.", "ArialMT", 11.2, 26, 0),
        ("•", "SymbolMT", 11.2, 1, 0),  # Symbol - not in clean dict
        ("Page 5", "Helvetica", 10.0, 6, 0),  # Header - not in clean dict
    ]
    
    tagged = tag_font_spans(sample_spans, legacy_clean)
    
    print("Tagged spans using clean dict:")
    for text, tag in tagged:
        status = "PROCESSED" if tag != "<?>" else "IGNORED"
        print(f"  '{text[:30]}' → {tag:5s} [{status}]")
    
    print()
    print("=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_exclude_unclassified()
