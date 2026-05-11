import os
import tkinter as tk
from tkinter import filedialog

from _extract_raw_data import extract_raw_data
from _split_logical_docs import split_logical_docs
from _normalize import normalize


# from test_harness.test_harness_utils import set_monitor_CMD
from test_harness.test_harness_utils import (
    set_monitor_CMD,
    run_raw_data_diagnostics,
    run_logical_docs_diagnostics,
    run_normalized_docs_diagnostics,
    parse_block_range,
)  ### edit
from test_harness.test_text_type import show_text_type_for_blocks

from test_harness.options import (
    PROMPT_TEXT_TYPE,
    PROMPT_LOGICAL_DOCS,
    PROMPT_NORMALIZED_DOCS,
    ask_yes_no_exit,
    ask_text_type_blocks,
    print_paths,
    print_no_file_selected,
    print_selected_file,
    print_exit_message,
    print_return_to_raw_data,
)


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
    # print("Script dir     :", BASE_DIR)
    # print("Parent dir     :", PARENT_DIR)
    # print("Documents dir  :", DOCUMENTS_FOLDER)
    # print("Folder exists? :", os.path.exists(DOCUMENTS_FOLDER))

    ### edit
    print_paths(
        BASE_DIR,
        PARENT_DIR,
        DOCUMENTS_FOLDER,
        os.path.exists(DOCUMENTS_FOLDER),
    )

    # -----------------------------------------------------------------------------------
    # Select PDF
    # -----------------------------------------------------------------------------------
    pdf_path = filedialog.askopenfilename(
        parent=root,
        title="Select PDF file",
        initialdir=DOCUMENTS_FOLDER if os.path.exists(DOCUMENTS_FOLDER) else BASE_DIR,
        filetypes=[("PDF files", "*.pdf")],
    )

    # Destroy tkinter root immediately
    root.destroy()

    if not pdf_path:
        print_no_file_selected()
        return

    print_selected_file(pdf_path)

    # -----------------------------------------------------------------------------------
    # PDF Extract: Raw Data, Logical Documents and Normalized phases
    # -----------------------------------------------------------------------------------

    # Extract raw data blocks - text, tables, figures
    # raw_data_file = extract_raw_data(pdf_path, test_mode=True)

    # Split raw content blocks into logical documents
    # logical_docs, font_tags, page_headers = split_logical_docs(
    #     raw_data_file, test_mode=True
    # )

    # Normalize logical documents
    # normalized_docs = normalize(logical_docs, font_tags, page_headers, test_mode=True)

    ### edit
    # -----------------------------------------------------------------------------------
    # PDF Extract: Raw Data and Logical Documents
    # -----------------------------------------------------------------------------------

    raw_data_file = extract_raw_data(pdf_path, test_mode=False)

    logical_docs, font_tags, page_headers = split_logical_docs(
        raw_data_file, test_mode=False
    )

    # -----------------------------------------------------------------------------------
    # Interactive flow:
    # RawDataFile block/page -> LogicalDocument -> NormalizedDocument
    # Y = continue, N = back to RawDataFile block/page, E = exit
    # -----------------------------------------------------------------------------------

    while True:
        # Step 1: RawDataFile block range + page selection
        run_raw_data_diagnostics(raw_data_file, font_tags, ask_show=True)

        ### add & edit
        text_type_choice = ask_yes_no_exit(PROMPT_TEXT_TYPE)

        if text_type_choice == "exit":
            print_exit_message()
            return

        if text_type_choice == "back":
            print_return_to_raw_data()
            continue

        if text_type_choice == "yes":
            block_input = ask_text_type_blocks()

            selected_blocks = parse_block_range(block_input)

            show_text_type_for_blocks(raw_data_file, expand_blocks=selected_blocks)

        # Step 2: Ask LogicalDocument
        # logical_choice = ask_yes_no_exit(
        #     "\nShow Extracted 'LogicalDocument(s)' content? (Y/N/E): "
        # )

        # if logical_choice == "exit":
        #     print("\nExiting test harness.")
        #     return

        # if logical_choice == "back":
        #     print("\nReturning to RawDataFile block/page selection...\n")
        #     continue

        ### edit
        logical_choice = ask_yes_no_exit(PROMPT_LOGICAL_DOCS)

        if logical_choice == "exit":
            print_exit_message()
            return

        if logical_choice == "back":
            print_return_to_raw_data()
            continue

        run_logical_docs_diagnostics(
            logical_docs, font_tags, page_headers, prefix="Extracted", ask_show=False
        )

        # Step 3: Normalize only after LogicalDocument is accepted
        normalized_docs = normalize(
            logical_docs, font_tags, page_headers, test_mode=False
        )

        # Step 4: Ask NormalizedDocument
        # normalized_choice = ask_yes_no_exit(
        #     "\nShow 'NormalizedDocument(s)' content? (Y/N/E): "
        # )

        # if normalized_choice == "exit":
        #     print("\nExiting test harness.")
        #     return

        # if normalized_choice == "back":
        #     print("\nReturning to RawDataFile block/page selection...\n")
        #     continue

        normalized_choice = ask_yes_no_exit(PROMPT_NORMALIZED_DOCS)

        if normalized_choice == "exit":
            print_exit_message()
            return

        if normalized_choice == "back":
            print_return_to_raw_data()
            continue

        run_normalized_docs_diagnostics(
            normalized_docs, font_tags, page_headers, ask_show=False
        )

        break


# -----------------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------------
if __name__ == "__main__":
    run_driver()
