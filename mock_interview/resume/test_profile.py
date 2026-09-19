from pathlib import Path

from mock_interview.resume.parser import extract_text_from_pdf
from mock_interview.resume.analyzer import build_candidate_profile


# =========================================================
# RESUME PATH
# =========================================================

CURRENT_FILE = Path(__file__).resolve()

RESUME_DIR = CURRENT_FILE.parent

pdf_path = (
    RESUME_DIR
    / "test_data"
    / "resume.pdf"
)


# =========================================================
# CHECK FILE
# =========================================================

if not pdf_path.exists():

    raise FileNotFoundError(
        f"Resume PDF not found:\n{pdf_path}"
    )


# =========================================================
# EXTRACT TEXT
# =========================================================

text = extract_text_from_pdf(
    str(pdf_path)
)


# =========================================================
# BUILD PROFILE
# =========================================================

profile = build_candidate_profile(
    text
)


# =========================================================
# DISPLAY
# =========================================================

print("=" * 70)
print("STRUCTURED CANDIDATE PROFILE")
print("=" * 70)

print(
    profile.model_dump_json(
        indent=2
    )
)

print("=" * 70)
print("PROFILE EXTRACTION COMPLETED")
print("=" * 70)