from pathlib import Path

try:
    from mock_interview.resume.parser import extract_text_from_pdf
except ImportError:
    from parser import extract_text_from_pdf


pdf_path = Path(__file__).resolve().parent / "test_data" / "resume.pdf"

text = extract_text_from_pdf(pdf_path)

print("=" * 60)
print("EXTRACTED RESUME TEXT")
print("=" * 60)

print(text)

print("=" * 60)
print("TEXT EXTRACTION COMPLETED")
print("=" * 60)