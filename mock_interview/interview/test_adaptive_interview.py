from mock_interview.interview.conversation_state import (
    ConversationState
)

from mock_interview.interview.answer_analyzer import (
    analyze_answer
)

from mock_interview.interview.decision_engine import (
    process_answer
)

from mock_interview.interview.question_generator import (
    generate_next_question
)


# =========================================================
# CREATE SESSION
# =========================================================

state = ConversationState(
    candidate_name="H S YASHAS GOWDA",
    role="AI/ML Engineer",
)


# =========================================================
# QUESTION CONTEXT
# =========================================================

context = {

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
    ],

    "skill_gaps": [
        "PyTorch",
        "TensorFlow",
        "Docker",
        "FastAPI",
    ],
}


# =========================================================
# FIRST QUESTION
# =========================================================

question = (
    "Could you walk me through your "
    "Skylark project?"
)

state.set_question(
    question=question,
    category="project",
)


# =========================================================
# CANDIDATE ANSWER
# =========================================================

answer = (
    "Skylark is an AI-powered business "
    "intelligence agent. I used Python, "
    "Claude API, GraphQL and Pandas to "
    "convert natural language queries into "
    "actionable insights from business data."
)


state.record_answer(
    answer
)


# =========================================================
# ANALYZE ANSWER
# =========================================================

assessment = analyze_answer(
    question=question,
    answer=answer,
)

state.set_answer_assessment(
    assessment
)


# =========================================================
# DECISION
# =========================================================

decision = process_answer(
    assessment=assessment,
    state=state,
)


# =========================================================
# GENERATE NEXT QUESTION
# =========================================================

next_question = generate_next_question(
    context=context,
    decision=decision,
    previous_question=question,
    previous_answer=answer,
)


# =========================================================
# DISPLAY
# =========================================================

print("=" * 70)
print("ADAPTIVE INTERVIEW TEST")
print("=" * 70)

print()
print("FIRST QUESTION")
print("-" * 70)
print(question)

print()
print("CANDIDATE ANSWER")
print("-" * 70)
print(answer)

print()
print("ANSWER QUALITY")
print("-" * 70)
print(
    assessment["overall_quality"]["level"]
)

print(
    assessment["overall_quality"]["percentage"],
    "%"
)

print()
print("DECISION")
print("-" * 70)
print(
    "Action:",
    decision["action"]
)

print(
    "Reason:",
    decision["reason"]
)

print()
print("NEXT QUESTION")
print("-" * 70)
print(
    next_question["question"]
)

print()
print(
    "Generation Method:",
    next_question["generation_method"]
)

print()
print("=" * 70)
print("ADAPTIVE INTERVIEW TEST COMPLETED")
print("=" * 70)