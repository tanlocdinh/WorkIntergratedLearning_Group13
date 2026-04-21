import os
import tkinter as tk
from tkinter import filedialog

from _extract_raw_data import extract_raw_data
from _split_logical_docs import split_logical_docs
from _normalize import normalize
from test_harness.test_harness_utils import set_monitor_CMD

# -----------------------------------------------------------------------------------
# Main Test Harness Driver
# -----------------------------------------------------------------------------------
def run_driver():

    # -----------------------------------------------------------------------------------
    # Setup Tkinter root for dialogs
    # NOTE: Using standard Tk root for reliability
    # -----------------------------------------------------------------------------------
    root = tk.Tk()
    root.withdraw()

    # -----------------------------------------------------------------------------------
    # Resolve USB-relative paths
    # -----------------------------------------------------------------------------------
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.dirname(BASE_DIR)
    DOCUMENTS_FOLDER = os.path.join(PARENT_DIR, "Test_Documents")

    # -----------------------------------------------------------------------------------
    # Debug (keep this while testing)
    # -----------------------------------------------------------------------------------
    print("Script dir     :", BASE_DIR)
    print("Parent dir     :", PARENT_DIR)
    print("Documents dir  :", DOCUMENTS_FOLDER)
    print("Folder exists? :", os.path.exists(DOCUMENTS_FOLDER))

    # -----------------------------------------------------------------------------------
    # Select PDF
    # -----------------------------------------------------------------------------------
    pdf_path = filedialog.askopenfilename(
        parent=root,
        title="Select PDF file",
        initialdir=DOCUMENTS_FOLDER if os.path.exists(DOCUMENTS_FOLDER) else BASE_DIR,
        filetypes=[("PDF files", "*.pdf")]
    )

    # Destroy tkinter root immediately
    root.destroy()

    if not pdf_path:
        print("No file selected. Exiting.")
        return

    print("Selected file:", pdf_path)

    # -----------------------------------------------------------------------------------
    # PDF Extract: Raw Data, Logical Documents and Normalized phases
    # -----------------------------------------------------------------------------------

    # Extract raw data blocks - text, tables, figures
    raw_data_file = extract_raw_data(pdf_path, test_mode=True)

    # Split raw content blocks into logical documents
    logical_docs, font_tags, page_headers = split_logical_docs(
        raw_data_file,
        test_mode=True
    )

    # Normalize logical documents
    normalized_docs = normalize(
        logical_docs,
        font_tags,
        page_headers,
        test_mode=True
    )


# -----------------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------------
if __name__ == "__main__":
    run_driver()