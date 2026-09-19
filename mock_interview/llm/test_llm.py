from mock_interview.llm.provider import (
    get_llm_provider,
)


# =========================================================
# CREATE PROVIDER
# =========================================================

llm = get_llm_provider(
    "mock"
)


print("=" * 70)
print("LLM PROVIDER TEST")
print("=" * 70)


# =========================================================
# BASIC GENERATION
# =========================================================

response = llm.generate(
    prompt=(
        "Generate a short interview question "
        "for an AI/ML Engineer."
    )
)


print()
print("BASIC LLM RESPONSE")
print("-" * 70)
print(response)


# =========================================================
# QUESTION GENERATION
# =========================================================

question_context = {

    "role": "AI/ML Engineer",

    "category": "project",

    "project": (
        "Skylark – AI-Powered Founder "
        "Business Intelligence Agent"
    ),

    "candidate_name": "H S YASHAS GOWDA",
}


question = llm.generate_question(
    question_context
)


print()
print("GENERATED QUESTION")
print("-" * 70)
print(question)


# =========================================================
# FOLLOW-UP QUESTION
# =========================================================

followup_context = {

    "role": "AI/ML Engineer",

    "category": "project",

    "project": (
        "Skylark – AI-Powered Founder "
        "Business Intelligence Agent"
    ),

    "previous_question": (
        "Could you walk me through your Skylark project?"
    ),

    "previous_answer": (
        "I used Python, Claude API, GraphQL "
        "and Pandas to build the system."
    ),
}


followup = llm.generate_question(
    followup_context
)


print()
print("FOLLOW-UP QUESTION")
print("-" * 70)
print(followup)


# =========================================================
# ANSWER ANALYSIS
# =========================================================

answer_context = {

    "question": (
        "Could you explain your Skylark project?"
    ),

    "answer": (
        "I used Python, Claude API and Pandas "
        "to build the project."
    ),
}


assessment = llm.analyze_answer(
    answer_context
)


print()
print("ANSWER ANALYSIS")
print("-" * 70)

for key, value in assessment.items():

    print(
        f"{key}: {value}"
    )


# =========================================================
# COMPLETED
# =========================================================

print()
print("=" * 70)
print("LLM PROVIDER TEST COMPLETED")
print("=" * 70)