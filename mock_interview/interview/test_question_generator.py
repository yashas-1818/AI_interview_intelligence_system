from mock_interview.interview.question_generator import (
    generate_question_from_context
)


# =========================================================
# TEST 1: RESUME QUESTION
# =========================================================

resume_context = {

    "role": "AI/ML Engineer",

    "candidate_name": "H S YASHAS GOWDA",

    "category": "resume",

    "candidate_strengths": [
        "machine learning",
        "nlp",
        "python",
        "sql",
    ],

    "skill_gaps": [
        "pytorch",
        "tensorflow",
        "docker",
        "fastapi",
    ],

    "project_topics": [
        "Skylark – AI-Powered Founder Business Intelligence Agent",
        "Traders Paradise – Full-Stack Indian Stock Trading Platform",
        "AI-Powered Interview Intelligence System",
        "Event Management System",
    ],

    "role_topics": [
        "Develop and deploy machine learning models",
        "Build AI-powered applications",
        "Work with data pipelines",
        "Collaborate with software engineers",
    ],

    "candidate_skills": [
        "Python",
        "C",
        "JavaScript",
        "NLP",
        "Claude API",
    ],
}


# =========================================================
# TEST 2: PROJECT QUESTION
# =========================================================

project_context = dict(
    resume_context
)

project_context[
    "category"
] = "project"


# =========================================================
# TEST 3: TECHNICAL QUESTION
# =========================================================

technical_context = dict(
    resume_context
)

technical_context[
    "category"
] = "technical"


# =========================================================
# TEST 4: ROLE QUESTION
# =========================================================

role_context = dict(
    resume_context
)

role_context[
    "category"
] = "role_specific"


# =========================================================
# TEST 5: SKILL GAP QUESTION
# =========================================================

gap_context = dict(
    resume_context
)

gap_context[
    "category"
] = "skill_gap"


# =========================================================
# RUN TESTS
# =========================================================

test_cases = [
    (
        "RESUME QUESTION",
        resume_context,
    ),
    (
        "PROJECT QUESTION",
        project_context,
    ),
    (
        "TECHNICAL QUESTION",
        technical_context,
    ),
    (
        "ROLE-SPECIFIC QUESTION",
        role_context,
    ),
    (
        "SKILL-GAP QUESTION",
        gap_context,
    ),
]


print("=" * 70)
print("QUESTION GENERATOR TEST")
print("=" * 70)


for title, context in test_cases:

    result = generate_question_from_context(
        context
    )

    print()
    print(title)
    print("-" * 70)

    print(
        "Category:",
        result["category"]
    )

    print(
        "Question:",
        result["question"]
    )

    print(
        "Method:",
        result["generation_method"]
    )


print()
print("=" * 70)
print("QUESTION GENERATOR TEST COMPLETED")
print("=" * 70)