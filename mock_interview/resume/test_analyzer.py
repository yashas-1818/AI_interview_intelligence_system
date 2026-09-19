from pathlib import Path

try:
    from mock_interview.resume.parser import extract_text_from_pdf
    from mock_interview.resume.analyzer import extract_sections
except ImportError:
    from parser import extract_text_from_pdf
    from analyzer import extract_sections


pdf_path = Path(__file__).resolve().parent / "test_data" / "resume.pdf"

text = extract_text_from_pdf(pdf_path)

sections = extract_sections(text)


print("=" * 70)
print("RESUME SECTION ANALYSIS")
print("=" * 70)


for section, content in sections.items():

    print(f"\n[{section.upper()}]")
    print("-" * 70)
    print(content)


print("=" * 70)
print("SECTION ANALYSIS COMPLETED")
print("=" * 70)