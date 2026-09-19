from mock_interview.job.parser import extract_job_text
from mock_interview.job.analyzer import analyze_job_description


# =========================================================
# TEST JOB DESCRIPTION
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
# PARSE JOB DESCRIPTION
# =========================================================

clean_text = extract_job_text(
    job_description
)


# =========================================================
# ANALYZE JOB
# =========================================================

job_profile = analyze_job_description(
    clean_text
)


# =========================================================
# DISPLAY RESULT
# =========================================================

print("=" * 70)
print("PARSED JOB PROFILE")
print("=" * 70)

print(
    job_profile.model_dump_json(
        indent=2
    )
)

print("=" * 70)
print("JOB ANALYSIS COMPLETED")
print("=" * 70)