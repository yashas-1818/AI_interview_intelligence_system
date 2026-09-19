from mock_interview.llm.interview_adapter import (
    InterviewLLMAdapter,
)


print("=" * 70)
print("INTERVIEW LLM ADAPTER TEST")
print("=" * 70)


# =========================================================
# CREATE ADAPTER
# =========================================================

adapter = InterviewLLMAdapter()


print()
print("LLM PROVIDER:")
print(type(adapter.llm).__name__)


# =========================================================
# QUESTION GENERATION
# =========================================================

print()
print("=" * 70)
print("QUESTION GENERATION")
print("=" * 70)


context = {

    "candidate_name":
        "H S YASHAS GOWDA",

    "role":
        "AI/ML Engineer",

    "category":
        "project",

    "difficulty":
        2,

    "project":
        "Skylark – AI-Powered Founder "
        "Business Intelligence Agent",

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

    "project_topics": [
        "Skylark – AI-Powered Founder "
        "Business Intelligence Agent",
        "Traders Paradise",
        "AI-Powered Interview Intelligence System",
        "Event Management System",
    ],

    "question_history": [],
}


try:

    result = adapter.generate_question(
        context
    )

    print()
    print("Question:")
    print(result["question"])

    print()
    print("Category:")
    print(result["category"])

    print()
    print("Difficulty:")
    print(result["difficulty"])

    print()
    print("Method:")
    print(result["method"])


except Exception as error:

    print()
    print("QUESTION GENERATION FAILED")
    print(type(error).__name__)
    print(error)

    raise SystemExit(1)


# =========================================================
# ANSWER ANALYSIS
# =========================================================

print()
print("=" * 70)
print("ANSWER ANALYSIS")
print("=" * 70)


question = result["question"]

answer = (
    "Skylark is an AI-powered business "
    "intelligence agent. I used Python, "
    "Claude API, GraphQL and Pandas to "
    "convert natural language queries into "
    "actionable insights from business data."
)


try:

    analysis = adapter.analyze_answer(
        question=question,
        answer=answer,
        context=context,
    )

    print()
    print("RULE-BASED ANALYSIS:")

    print(
        analysis["rule_based"]
    )

    print()
    print("LLM ANALYSIS:")

    print(
        analysis["llm_based"]
    )


except Exception as error:

    print()
    print("ANSWER ANALYSIS FAILED")
    print(type(error).__name__)
    print(error)

    raise SystemExit(1)


print()
print("=" * 70)
print("INTERVIEW LLM ADAPTER TEST COMPLETED")
print("=" * 70)