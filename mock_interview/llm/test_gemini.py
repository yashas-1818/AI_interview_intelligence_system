from mock_interview.llm.gemini_provider import GeminiLLM


print("=" * 70)
print("GEMINI CONNECTION TEST")
print("=" * 70)


# =========================================================
# CREATE GEMINI PROVIDER
# =========================================================

try:

    llm = GeminiLLM()

    print()
    print("Provider:")
    print("Gemini")

    print()
    print("Model:")
    print(llm.model)

except Exception as error:

    print()
    print("FAILED TO INITIALIZE GEMINI")
    print()
    print(type(error).__name__)
    print(error)

    raise SystemExit(1)


# =========================================================
# BASIC GENERATION TEST
# =========================================================

print()
print("=" * 70)
print("BASIC GEMINI RESPONSE")
print("=" * 70)

try:

    response = llm.generate(
        prompt=(
            "You are an AI/ML technical interviewer. "
            "Ask exactly one short technical interview "
            "question for a candidate applying for an "
            "AI/ML Engineer position."
        )
    )

    print()
    print(response)

except Exception as error:

    print()
    print("GEMINI GENERATION FAILED")
    print()
    print(type(error).__name__)
    print(error)

    raise SystemExit(1)


# =========================================================
# STRUCTURED QUESTION TEST
# =========================================================

print()
print("=" * 70)
print("STRUCTURED QUESTION GENERATION")
print("=" * 70)

question_context = {

    "role": "AI/ML Engineer",

    "candidate_name": "H S YASHAS GOWDA",

    "category": "project",

    "project": (
        "Skylark – AI-Powered Founder "
        "Business Intelligence Agent"
    ),

    "candidate_skills": [
        "Python",
        "Claude API",
        "GraphQL",
        "Pandas",
        "NLP",
    ],

    "skill_gaps": [
        "PyTorch",
        "TensorFlow",
        "Docker",
        "FastAPI",
    ],

    "difficulty": 1,

    "question_history": [],
}


try:

    question = llm.generate_question(
        question_context
    )

    print()

    print("Question:")
    print(question["question"])

    print()
    print("Category:")
    print(question["category"])

    print()
    print("Difficulty:")
    print(question["difficulty"])

except Exception as error:

    print()
    print("STRUCTURED QUESTION GENERATION FAILED")
    print()
    print(type(error).__name__)
    print(error)

    raise SystemExit(1)


# =========================================================
# ANSWER ANALYSIS TEST
# =========================================================

print()
print("=" * 70)
print("GEMINI ANSWER ANALYSIS")
print("=" * 70)


answer_context = {

    "role": "AI/ML Engineer",

    "category": "project",

    "candidate_skills": [
        "Python",
        "Claude API",
        "GraphQL",
        "Pandas",
        "NLP",
    ],

    "expected_topics": [
        "architecture",
        "Python",
        "Claude API",
        "GraphQL",
        "Pandas",
        "data processing",
    ],

    "question": (
        "Could you explain the architecture of your "
        "Skylark – AI-Powered Founder Business "
        "Intelligence Agent project?"
    ),

    "answer": (
        "Skylark is an AI-powered business intelligence "
        "agent. I used Python, Claude API, GraphQL and "
        "Pandas to convert natural language queries into "
        "actionable insights from business data. Claude "
        "was used for tool-use and Pandas handled "
        "deterministic analytics."
    ),
}


try:

    analysis = llm.analyze_answer(
        answer_context
    )

    print()

    for key, value in analysis.items():

        print(
            f"{key}: {value}"
        )

except Exception as error:

    print()
    print("ANSWER ANALYSIS FAILED")
    print()
    print(type(error).__name__)
    print(error)

    raise SystemExit(1)


# =========================================================
# COMPLETED
# =========================================================

print()
print("=" * 70)
print("GEMINI CONNECTION TEST COMPLETED")
print("=" * 70)