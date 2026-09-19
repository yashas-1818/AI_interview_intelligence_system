from mock_interview.llm.interview_adapter import (
    create_interview_llm,
)

from mock_interview.interview.conversation_state import (
    ConversationState,
)


# =========================================================
# CREATE SESSION
# =========================================================

state = ConversationState(
    candidate_name="H S YASHAS GOWDA",
    role="AI/ML Engineer",
)


# =========================================================
# CREATE LLM ADAPTER
# =========================================================

llm = create_interview_llm(
    provider="mock"
)


print("=" * 70)
print("LLM ↔ INTERVIEW INTEGRATION TEST")
print("=" * 70)


# =========================================================
# INTERVIEW CONTEXT
# =========================================================

context = {

    "role": "AI/ML Engineer",

    "candidate_name": (
        "H S YASHAS GOWDA"
    ),

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
}


# =========================================================
# GENERATE FIRST QUESTION
# =========================================================

question_result = (
    llm.generate_question(
        context
    )
)

question = question_result[
    "question"
]


state.set_question(
    question=question,
    category="project",
)


print()
print("=" * 70)
print("GENERATED INTERVIEW QUESTION")
print("=" * 70)

print()
print(question)

print()
print(
    "Generation Method:",
    question_result["method"]
)


# =========================================================
# SIMULATE CANDIDATE ANSWER
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


print()
print("=" * 70)
print("CANDIDATE ANSWER")
print("=" * 70)

print()
print(answer)


# =========================================================
# COMBINED ANSWER ANALYSIS
# =========================================================

assessment = llm.analyze_answer(
    question=question,
    answer=answer,
    context=context,
)


print()
print("=" * 70)
print("RULE-BASED ANALYSIS")
print("=" * 70)

rule_analysis = assessment[
    "rule_based"
]

print()
print(
    "Quality:",
    rule_analysis[
        "overall_quality"
    ]["level"]
)

print(
    "Score:",
    rule_analysis[
        "overall_quality"
    ]["percentage"],
    "%"
)

print(
    "Technical Depth:",
    rule_analysis[
        "technical_depth"
    ]["level"]
)

print(
    "Needs Follow-Up:",
    rule_analysis[
        "follow_up"
    ]["needs_follow_up"]
)


print()
print("=" * 70)
print("LLM ANALYSIS")
print("=" * 70)

llm_analysis = assessment[
    "llm_based"
]

for key, value in llm_analysis.items():

    print(
        f"{key}: {value}"
    )


# =========================================================
# GENERATE FOLLOW-UP
# =========================================================

followup = llm.generate_followup(
    context=context,
    previous_question=question,
    previous_answer=answer,
)


print()
print("=" * 70)
print("LLM FOLLOW-UP QUESTION")
print("=" * 70)

print()
print(
    followup["question"]
)

print()
print(
    "Action:",
    followup["action"]
)

print(
    "Generation Method:",
    followup["method"]
)


# =========================================================
# FINAL STATE
# =========================================================

print()
print("=" * 70)
print("INTERVIEW STATE")
print("=" * 70)

print()
print(
    "Session ID:",
    state.session_id
)

print(
    "Question Number:",
    state.question_number
)

print(
    "Current Category:",
    state.current_category
)

print(
    "Current Question:",
    state.current_question
)

print(
    "Answers Received:",
    len(
        state.answers_received
    )
)


# =========================================================
# COMPLETED
# =========================================================

print()
print("=" * 70)
print("LLM ↔ INTERVIEW INTEGRATION TEST COMPLETED")
print("=" * 70)