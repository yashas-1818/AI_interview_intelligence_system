from pathlib import Path

from mock_interview.resume.parser import (
    extract_text_from_pdf
)

from mock_interview.resume.analyzer import (
    build_candidate_profile
)

from mock_interview.job.parser import (
    extract_job_text
)

from mock_interview.job.analyzer import (
    analyze_job_description
)

from mock_interview.job.matcher import (
    build_match_report
)

from mock_interview.interview.strategy import (
    build_interview_strategy,
    select_next_category,
    build_question_context,
)


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]


resume_path = (
    PROJECT_ROOT
    / "mock_interview"
    / "resume"
    / "test_data"
    / "resume.pdf"
)


# =========================================================
# LOAD RESUME
# =========================================================

print("=" * 70)
print("LOADING CANDIDATE PROFILE")
print("=" * 70)

resume_text = extract_text_from_pdf(
    str(resume_path)
)

candidate = build_candidate_profile(
    resume_text
)

print(
    f"Candidate: {candidate.candidate.name}"
)


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

match_report = build_match_report(
    candidate,
    job
)


# =========================================================
# BUILD INTERVIEW STRATEGY
# =========================================================

strategy = build_interview_strategy(
    candidate,
    job,
    match_report
)


# =========================================================
# DISPLAY STRATEGY
# =========================================================

print()
print("=" * 70)
print("INTERVIEW STRATEGY")
print("=" * 70)

print()

print(
    f"Role: {strategy['role']}"
)

print(
    f"Candidate: {strategy['candidate_name']}"
)

print()

print("INTERVIEW CATEGORIES:")

for index, category in enumerate(
    strategy["categories"],
    start=1
):

    print(
        f"  {index}. {category}"
    )


print()

print("CANDIDATE STRENGTHS:")

for skill in strategy[
    "candidate_strengths"
]:

    print(
        f"  [+] {skill}"
    )


print()

print("SKILL GAPS:")

for skill in strategy[
    "skill_gaps"
]:

    print(
        f"  [!] {skill}"
    )


print()

print("PROJECT TOPICS:")

for project in strategy[
    "project_topics"
]:

    print(
        f"  - {project}"
    )


print()

print("ROLE TOPICS:")

for topic in strategy[
    "role_topics"
]:

    print(
        f"  - {topic}"
    )


# =========================================================
# TEST NEXT CATEGORY
# =========================================================

completed = [
    "introduction"
]

next_category = select_next_category(
    strategy,
    completed
)

print()

print(
    f"NEXT CATEGORY: {next_category}"
)


# =========================================================
# TEST QUESTION CONTEXT
# =========================================================

context = build_question_context(
    strategy,
    next_category
)

print()

print("QUESTION CONTEXT:")

for key, value in context.items():

    print(
        f"  {key}: {value}"
    )


print()
print("=" * 70)
print("INTERVIEW STRATEGY TEST COMPLETED")
print("=" * 70)