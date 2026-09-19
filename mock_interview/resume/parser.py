import pymupdf
import re


def normalize_pdf_text(text: str) -> str:
    """
    Clean common PDF extraction problems such as
    words split across lines with hyphens.
    """

    # Fix words broken across lines:
    # natural-\nlanguage -> natural-language
    text = re.sub(r"-\s*\n\s*", "-", text)

    # Normalize multiple spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract and normalize text from a PDF resume.
    """

    document = pymupdf.open(pdf_path)

    pages = []

    for page in document:
        pages.append(page.get_text())

    document.close()

    text = "\n".join(pages)

    return normalize_pdf_text(text)


if __name__ == "__main__":
    print("Resume parser module loaded successfully.")