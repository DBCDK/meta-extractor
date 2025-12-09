# %%
from dataclasses import dataclass
from typing import List, Optional, Sequence, Union
import fitz  # PyMuPDF
import regex as re


@dataclass(frozen=True)
class ExtractTextConfig:
    """
    Configuration for PDF text extraction.

    pages: pages to analyze (0-based). Negative indices are allowed (like Python indexing).
           Use None to process all pages.
    threshold: paragraphs shorter than this length are always kept.
    long_paragraph_pages: on these pages we allow a number of long paragraphs.
    long_paragraph_max: maximum number of long paragraphs per page from long_paragraph_pages.
    keep_toc: if False, try to skip Table of Contents-like lines (those with dot leaders).
    include_metadata: if True, include selected PDF metadata fields at the top.
    pdf_metadata_skip: metadata keys to skip if include_metadata is True.
    split_pattern: regex pattern used to split a page into paragraphs.
                   Default splits on one-or-more newlines preceding an uppercase letter.
    """
    pages: Optional[Sequence[int]] = None
    threshold: int = 100
    long_paragraph_pages: Sequence[int] = (0, 1, 2)
    long_paragraph_max: int = 4
    keep_toc: bool = False
    include_metadata: bool = True
    pdf_metadata_skip: frozenset[str] = frozenset({"format", "creator", "producer"})
    split_pattern: str = r"\n+(?=\p{Lu})"


class PDFTextExtractor:
    """
    Reusable extractor. Create once with a config (or defaults), call .extract() on any document.
    """

    def __init__(self, config: Optional[ExtractTextConfig] = None) -> None:
        self.config = config or ExtractTextConfig()
        # Precompile the paragraph split regex for speed.
        self._split_re = re.compile(self.config.split_pattern, flags=re.UNICODE)

    def extract(self, pdf: Union[str, fitz.Document]) -> str:
        """
        Extract text from a PDF (path or fitz.Document) according to the config.

        :param pdf: PDF to extract text from. Either path to pdf or fitz.Document.
        :return: extracted text.
        """

        should_close = False  # if we opened the pdf document, we will nicely close it again ourselves
        if isinstance(pdf, str):
            pdf = fitz.open(pdf)
            should_close = True

        try:
            cfg = self.config
            pages_to_process = self._resolve_pages(pdf, cfg.pages)
            texts: List[str] = []

            # Include metadata
            if cfg.include_metadata and pdf.metadata:
                for key, val in (pdf.metadata or {}).items():
                    if val and key not in cfg.pdf_metadata_skip:
                        texts.append(f"{key}: {val}")

            # Extract page by page
            for page in pages_to_process:
                if page < 0 or page >= len(pdf):
                    continue

                text = pdf[page].get_text(sort=True)
                # Use regular expression to split text into paragraphs
                paragraphs = self._split_re.split(text)
                long_paragraph_count = 0

                for paragraph in paragraphs:
                    paragraph = " ".join(paragraph.strip().split())
                    if not paragraph:
                        continue

                    if not cfg.keep_toc:
                        # simple Table of Contents detection (dot leaders)
                        if "....." in paragraph or ". . . . ." in paragraph:
                            continue

                    if len(paragraph) < cfg.threshold: # short paragraph, keep it
                        texts.append(paragraph)
                        continue

                    if page in cfg.long_paragraph_pages and long_paragraph_count < cfg.long_paragraph_max:
                        # allow some long paragraphs on the pages defined in long_paragraph_pages
                        long_paragraph_count += 1
                        texts.append(paragraph)
                        continue

                    # else: long paragraph not allowed, skip
            return "\n".join(texts)
        finally:
            if should_close:
                pdf.close()

    @staticmethod
    def _resolve_pages(pdf: fitz.Document, pages: Optional[Sequence[int]]) -> List[int]:
        """
        Convert a possibly-None list (meaning 'all pages') and allow negative indices.
        Filter out-of-range pages gracefully and deduplicate while preserving order.

        Example:
            for pdf with 10 pages, where last two pages are referred to both by 8, 9 and -1 and -2
            pages = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, -2, -1]
            _resolve_pages turns -2 into 8 and -1 into 9, then deduplicates.
            process each valid page exactly once

        """
        n = len(pdf)
        if pages is None:
            return list(range(n))

        resolved: List[int] = []
        seen = set()
        for p in pages:
            idx = p if p >= 0 else n + p
            if 0 <= idx < n and idx not in seen:
                resolved.append(idx)
                seen.add(idx)
        return resolved


# --- Quick wrapper function for extracting

def extract_text(
        pdf: Union[str, fitz.Document],
        config: Optional[ExtractTextConfig] = None,
) -> str:
    """
    Extract text from a PDF (path or fitz.Document) according to the config.
    :param pdf: PDF to extract text from. Either path to pdf or fitz.Document.
    :param config: ExtractTextConfig instance.
    :return: extracted text.

    Examples:
    Use config defaults:
        text = extract_text("file.pdf")

    Or provide a full config with some (or all) default settings changed:
        cfg = ExtractTextConfig(pages=[0,1,2,-1], keep_toc=True, threshold=80)
        text = extract_text("file.pdf", config=cfg)
    """
    extractor = PDFTextExtractor(config)
    return extractor.extract(pdf)


# %%
#commented out example for local testing
#config = ExtractTextConfig(pages=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, -2, -1])
#print(config)
#extracted_text = extract_text(pdf="/data/meta-extractor/pdf/870970-basis:133981071.pdf", config=config)
#with open("/home/<user>/tmp/870970-basis:133981071.extracted.txt", "w") as f:
#    f.write(extracted_text)
