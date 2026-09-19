import sys
from pathlib import Path


# =========================================================
# PROJECT PATH
# =========================================================

CURRENT_FILE = Path(__file__).resolve()

MOCK_INTERVIEW_DIR = CURRENT_FILE.parents[1]

PROJECT_ROOT = CURRENT_FILE.parents[2]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

sys.path.insert(
    0,
    str(MOCK_INTERVIEW_DIR)
)


# =========================================================
# IMPORTS
# =========================================================

from resume.parser import extract_text_from_pdf
from resume.analyzer import build_candidate_profile

from job.parser import extract_job_text
from job.analyzer import analyze_job_description

from job.matcher import build_match_report


# =========================================================
# LOAD RESUME
# =========================================================

resume_path = (
    MOCK_INTERVIEW_DIR
    / "resume"
    / "test_data"
    / "resume.pdf"
)


print("=" * 70)
print("LOADING RESUME")
print("=" * 70)

print(
    f"Resume: {resume_path}"
)


resume_text = extract_text_from_pdf(
    str(resume_path)
)

candidate = build_candidate_profile(
    resume_text
)


print("Resume loaded successfully.")


# =========================================================
# JOB DESCRIPTION
# =========================================================

job_description = """
AI/ML Engineer

We are looking for an AI/ML Engineer to join our team.

Requirements:
• Strong Python programming skills
• Knowledge of Machine Learning and NLP
• Experience with PyTorch or TensorFlow
• Understanding of SQL and databases

Responsibilities:
• Develop and deploy machine learning models
• Build AI-powered applications
• Work with data pipelines
• Collaborate with software engineers

Preferred:
• Experience with LLMs
• Experience with FastAPI
• Docker knowledge

Education:
• Bachelor's degree in Computer Science, Artificial Intelligence or related field

Experience:
• 0-2 years
"""


# =========================================================
# BUILD JOB PROFILE
# =========================================================

clean_job_text = extract_job_text(
    job_description
)

job = analyze_job_description(
    clean_job_text
)


# =========================================================
# MATCH CANDIDATE WITH JOB
# =========================================================

report = build_match_report(
    candidate,
    job
)


# =========================================================
# DISPLAY RESULT
# =========================================================

print()
print("=" * 70)
print("CANDIDATE <-> JOB MATCH REPORT")
print("=" * 70)

print()

print(
    f"Role: {report['role']}"
)


# ---------------------------------------------------------
# Required Skills
# ---------------------------------------------------------

print()

print("Required Skills Matched:")

matched_required = report[
    "required_skills"
]["matched"]

if matched_required:

    for skill in matched_required:

        print(
            f"  [+] {skill}"
        )

else:

    print("  None")


print()

print("Required Skills Missing:")

missing_required = report[
    "required_skills"
]["missing"]

if missing_required:

    for skill in missing_required:

        print(
            f"  [!] {skill}"
        )

else:

    print("  None")


# ---------------------------------------------------------
# Preferred Skills
# ---------------------------------------------------------

print()

print("Preferred Skills Matched:")

matched_preferred = report[
    "preferred_skills"
]["matched"]

if matched_preferred:

    for skill in matched_preferred:

        print(
            f"  [+] {skill}"
        )

else:

    print("  None")


print()

print("Preferred Skills Missing:")

missing_preferred = report[
    "preferred_skills"
]["missing"]

if missing_preferred:

    for skill in missing_preferred:

        print(
            f"  [!] {skill}"
        )

else:

    print("  None")


# ---------------------------------------------------------
# Score
# ---------------------------------------------------------

print()

print("Required Skill Match:")

print(
    f"  {report['required_skill_match_percentage']}%"
)


print()

print("=" * 70)
print("MATCHING COMPLETED")
print("=" * 70)