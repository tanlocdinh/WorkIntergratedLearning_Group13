# Test Adapter Refactoring Guide

## Problem Statement

Currently, production modules (`_extract_raw_data.py` and `_split_logical_docs.py`) return test-only data for test harness display purposes:

- `extract_raw_data()` returns `font_collection_tags` (empty placeholder dict for display)
- `split_logical_docs()` returns `font_collection_tags` and `page_headers` (used internally, returned for display)

These test-only returns contaminate the production pipeline.

## Solution: Test Adapter Functions

Create adapter functions in the test harness that call production code and extract additional display data as needed.

---

## Implementation Steps

### Step 1: Clean Production Returns

**In `_extract_raw_data.py`:**
```python
# Remove lines marked with # TEST-ONLY comments:
def extract_raw_data(file_path: str) -> RawDataFile:
    # ... existing code ...
    
    # Extract the font collection (total pages)
    font_collection, _ = extract_font_collection(text_block_list)  # Discard tags
    
    raw_data_file = RawDataFile(
        font_collection=font_collection,
        content=all_blocks
    )
    
    return raw_data_file  # Clean production return
```

**In `_split_logical_docs.py`:**
```python
# Remove lines marked with # TEST-ONLY comments:
def split_logical_docs(raw_data_file: RawDataFile) -> List[LogicalDocument]:
    # ... existing code ...
    
    # page_headers used internally to create LogicalDocuments
    page_headers = split_doc_headers(raw_data_file)
    
    for page_header in page_headers:
        # ... create logical_documents ...
    
    return logical_documents  # Clean production return (page_headers not returned)
```

---

### Step 2: Create Test Adapter Functions

**In `_test_harness.py` (or new `test_adapters.py`):**

```python
from font_collection import extract_font_collection
from split_doc_headers import split_doc_headers

def extract_raw_data_with_display_tags(pdf_path: str):
    """Test adapter: Extract raw data + display tags for test harness."""
    raw_data_file = extract_raw_data(pdf_path)  # Production call
    
    # Extract display tags for test harness
    text_blocks = [b for b in raw_data_file.content if hasattr(b, 'font_spans')]
    _, font_collection_tags = extract_font_collection(text_blocks)
    
    return raw_data_file, font_collection_tags


def split_logical_docs_with_display_data(raw_data_file):
    """Test adapter: Split logical docs + extract display data for test harness."""
    logical_documents = split_logical_docs(raw_data_file)  # Production call
    
    # Extract display data for test harness
    page_headers = split_doc_headers(raw_data_file)
    text_blocks = [b for b in raw_data_file.content if hasattr(b, 'font_spans')]
    _, font_collection_tags = extract_font_collection(text_blocks)
    
    return logical_documents, font_collection_tags, page_headers
```

---

### Step 3: Update Test Harness Calls

**In `_test_harness.py`:**

```python
# BEFORE (using contaminated production returns):
raw_data_file, font_collection_tags = extract_raw_data(pdf_path)
logical_docs, font_collection_tags_logical, page_headers = split_logical_docs(raw_data_file)

# AFTER (using test adapters):
raw_data_file, font_collection_tags = extract_raw_data_with_display_tags(pdf_path)
logical_docs, font_collection_tags_logical, page_headers = split_logical_docs_with_display_data(raw_data_file)

# Production code in comments remains clean:
# Production pipeline (4 lines):
#   raw_data_file = extract_raw_data(pdf_path)
#   logical_docs = split_logical_docs(raw_data_file)
#   normalized_docs = normalize(logical_docs)
#   chunks = chunk(normalized_docs)
```

---

## Benefits

✅ **Clean Production Code**: No test-only processing or returns  
✅ **Separation of Concerns**: Test harness owns display logic  
✅ **Clear Production Pipeline**: 4-line pipeline with single returns  
✅ **Maintainability**: Test adapters in one place, easy to modify  
✅ **No Duplication**: Production functions called once, adapters add display data  

---

## Files to Modify

1. `_extract_raw_data.py` - Remove TEST-ONLY lines, clean return
2. `_split_logical_docs.py` - Remove TEST-ONLY lines, clean return  
3. `_test_harness.py` - Add test adapter functions, update calls
4. Update production pipeline comments to show clean signatures

---

## Search Query for Later

To find all TEST-ONLY markers when ready to refactor:
```
grep -n "TEST-ONLY" _extract_raw_data.py _split_logical_docs.py
```

Or in VS Code: Search for `# TEST-ONLY` across workspace.
