# WorkIntergratedLearning_Group13

# Python PDF Parsing Test Harness

## Project Overview

This project provides a Python-based PDF parsing and diagnostic test harness for inspecting extracted PDF content. The tool supports raw data extraction, logical document splitting, normalization, font tag reporting, and text type diagnostics.

The test harness is designed for developers to inspect the PDF parsing workflow at different processing stages and verify whether blocks, pages, font tags, and document structures are extracted correctly.

## Main Features

- Extract raw PDF content into structured blocks.
- Display RawDataFile content by block range and page range.
- Show block distribution by page.
- Show block type index for TextBlock, TableBlock, and FigureBlock.
- Split extracted content into LogicalDocument objects.
- Display LogicalDocument summaries and block indexes.
- Normalize logical documents and inspect NormalizedDocument output.
- Display sorted font collections.
- Display tag distribution by block and by tag.
- Run Text Type Diagnostics for selected TextBlocks.
- Support flexible input formats such as `1`, `1-3`, `1,3`, and `1-3,5`.
- Support Y/N/E navigation:
  - `Y` = continue or show output
  - `N` = return to RawDataFile block/page selection
  - `E` = exit the test harness

## Requirements

- Python 3.12 or later
- PyMuPDF / fitz
- Project source code pulled from GitHub
- Test PDF files stored in the `Test_Documents` folder

## Installation

Open the terminal in the project folder and install dependencies:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available, install PyMuPDF manually:

```bash
pip install pymupdf
```

## Running the Test Harness

Open the terminal in the `Python Source Code` folder and run:

```bash
python _test_harness.py
```

A file selection window will appear. Select the PDF file that you want to test. After the file is selected, the program will extract the raw data, split the content into logical documents, and begin the interactive diagnostic workflow.

## Workflow

The diagnostic workflow includes four main inspection stages:

### 1. RawDataFile Inspection

The tool asks:

```text
Show 'RawDataFile' content? (y/n):
```

If `Y` is selected, the system displays:

- Block distribution by page
- Block type index
- Selected block content
- Font collection information

Users can select block ranges and page ranges to inspect specific parts of the extracted PDF.

### 2. Text Type Diagnostic

The tool asks:

```text
Show Text Type diagnostic for font_spans? (Y/N/E):
```

If `Y` is selected, users can select one or more TextBlocks. The system then displays each font span inside the selected block, including:

- Span number
- Extracted text
- Font name
- Font size
- Detected text type

Example detected text types include:

```text
part_sentence
line_break
bullet_or_symbol
heading
sentence
unknown
```

This helps developers verify whether the text classification logic is working correctly before later processing stages.

### 3. LogicalDocument Inspection

The tool asks:

```text
Show Extracted 'LogicalDocument(s)' content? (Y/N/E):
```

If `Y` is selected, the system displays available logical documents, including page ranges, block counts, and font counts. Users can then select a logical document and block range for detailed inspection.

The output includes:

- Logical document summary
- Page range
- Document name
- Standardized block labels
- Sorted font tags
- Tag distribution by block and by tag

### 4. NormalizedDocument Inspection

The tool asks:

```text
Show 'NormalizedDocument(s)' content? (Y/N/E):
```

If `Y` is selected, the normalization phase is executed and users can inspect normalized documents.

The output includes:

- Normalized document summary
- Normalized block content
- Standardized block labels
- Sorted font tags
- Tag distribution after normalization

This allows developers to compare LogicalDocument and NormalizedDocument output and confirm that document structure remains consistent after normalization.

## Example Input Formats

The test harness supports flexible selection formats:

```text
1       = select item 1
1-3     = select items 1 to 3
1,3     = select items 1 and 3
1-3,5   = select items 1 to 3 and item 5
Enter   = skip selection or show all, depending on the prompt
```

Reversed ranges such as `7-5` are automatically corrected to `5-7`.

## Important Notes

- This tool is intended for developer diagnostics, not as a final production user interface.
- Some PDF fonts may appear as internal names such as `CIDFont+F1` instead of readable font names.
- Text type classification is heuristic-based and may need adjustment for new PDF layouts.
- Large PDF files may produce long terminal output, so block and page filters should be used during testing.

## Troubleshooting

### PyMuPDF is missing

If the program shows an import error for `fitz`, install PyMuPDF:

```bash
pip install pymupdf
```

### File selection window does not appear

Make sure the script is being run in a desktop environment that supports Tkinter file dialogs.

### Text Type Diagnostic shows no output

Check that the selected block is a `TextBlock`. Text Type Diagnostic only works with blocks that contain font spans.

### Output is too long

Use block range and page range filters to inspect a smaller section of the document.

## Main Files

- `_test_harness.py`: Main diagnostic test harness driver.
- `_extract_raw_data.py`: Extracts raw PDF blocks and font collection data.
- `_split_logical_docs.py`: Splits raw extracted blocks into logical documents.
- `_normalize.py`: Normalizes logical document content.
- `text_type.py`: Classifies font spans into text types.
- `test_harness/options.py`: Centralises prompts, input handling, and common console messages.
- `test_harness/test_harness_utils.py`: Contains helper functions for diagnostics, range parsing, block labels, and workflow display.
- `test_harness/test_show_rawdata.py`: Displays RawDataFile content.
- `test_harness/test_show_logicaldata.py`: Displays LogicalDocument content.
- `test_harness/test_show_normdata.py`: Displays NormalizedDocument content.
- `test_harness/test_text_type.py`: Displays Text Type Diagnostic output.

## Ending the Session

The test harness can be exited at any main diagnostic prompt by entering:

```text
E
```

Otherwise, the workflow will continue through the diagnostic stages and finish after the normalized document inspection step.
