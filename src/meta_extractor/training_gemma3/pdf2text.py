import os
import argparse
import logging
from pathlib import Path

from meta_extractor.pdf_text_extractor import ExtractTextConfig, extract_text


logging.basicConfig(level=logging.INFO)


def main(input_directory: str, output_directory: str, short: bool = False):
    """
    Get text from pdf files in the given input directory

    :param input_directory: path to input files
    :param output_directory: path to output files
    :return:
    """
    input_directory = Path(input_directory)
    output_directory = Path(output_directory)
    if not output_directory.exists():
        output_directory.mkdir(parents=True, exist_ok=True)

    if short:
        # only read the first 3 pages, and the last two
        config = ExtractTextConfig(pages=[0, 1, 2, -2, -1])
    else:
        # read the first 13 pages, and the last two
        config = ExtractTextConfig(pages=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, -2, -1])

    pdf_errors = []
    simple_progress_counter = 0
    print(f"Processing status for every 100th file:")
    for filename in os.listdir(input_directory):
        if filename.endswith(".pdf"):
            if simple_progress_counter % 100 == 0:
                print(f"Processing file {simple_progress_counter + 1}: {filename}")
            simple_progress_counter += 1
            filepath = input_directory / filename
            pid = filename.split(".")[0]

            try:
                text = extract_text(str(filepath), config)
                output_filepath = output_directory / f"{pid}.txt"
                with open(output_filepath, "w") as f:
                    f.write(text)
            except Exception as e:
                pdf_errors.append(pid)
                print(f"Error with {pid}: {e}")
    print(f"Number of PDF files with errors: {len(pdf_errors)}")

def cli():
    """Command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-directory", required=True, help="path to directory where pdfs are stored.")
    parser.add_argument(
        "-o", "--output-directory", required=True, help="path to directory where output text files will be stored."
    )
    parser.add_argument(
        "-s", "--short", action='store_true', default=False,
        help="only look at the first 3 pages instead of the first 13 pages of the pdf"
    )
    args = parser.parse_args()
    main(args.input_directory, args.output_directory, args.short)
