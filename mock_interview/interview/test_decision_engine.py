from mock_interview.interview.conversation_state import (
    ConversationState
)

from mock_interview.interview.answer_analyzer import (
    analyze_answer
)

from mock_interview.interview.decision_engine import (
    process_answer
)


# =========================================================
# CREATE SESSION
# =========================================================

state = ConversationState(
    candidate_name="H S YASHAS GOWDA",
    role="AI/ML Engineer",
)


print("=" * 70)
print("ADAPTIVE DECISION ENGINE TEST")
print("=" * 70)


# =========================================================
# SET QUESTION
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
# SIMULATE ANSWER
# =========================================================

answer = (
    "Skylark is an AI-powered business "
    "intelligence agent. I used Python, "
    "Claude API, GraphQL and Pandas to "
    "convert natural language queries into "
    "actionable insights from business data."
)


print()
print("QUESTION:")
print(question)

print()
print("ANSWER:")
print(answer)


# =========================================================
# RECORD ANSWER
# =========================================================

state.record_answer(
    answer
)


# =========================================================
# ANALYZE
# =========================================================

assessment = analyze_answer(
    question=question,
    answer=answer,
)

state.set_answer_assessment(
    assessment
)


print()
print("=" * 70)
print("ANSWER ASSESSMENT")
print("=" * 70)

print(
    "Quality:",
    assessment["overall_quality"]["level"]
)

print(
    "Score:",
    assessment["overall_quality"]["percentage"],
    "%"
)

print(
    "Technical Depth:",
    assessment["technical_depth"]["level"]
)

print(
    "Needs Follow-Up:",
    assessment["follow_up"]["needs_follow_up"]
)

print(
    "Suggested Action:",
    assessment["follow_up"]["action"]
)


# =========================================================
# DECISION
# =========================================================

decision = process_answer(
    assessment=assessment,
    state=state,
)


print()
print("=" * 70)
print("ADAPTIVE DECISION")
print("=" * 70)

print(
    "Action:",
    decision["action"]
)

print(
    "Reason:",
    decision["reason"]
)

print(
    "Difficulty Change:",
    decision["difficulty_change"]
)


# =========================================================
# UPDATED STATE
# =========================================================

print()
print("=" * 70)
print("UPDATED INTERVIEW STATE")
print("=" * 70)

print()
print(
    "Difficulty:",
    state.current_difficulty
)

print(
    "Follow-Ups Asked:",
    state.followups_asked
)

print(
    "Current Category:",
    state.current_category
)

print(
    "Question Number:",
    state.question_number
)


# =========================================================
# TEST COMPLETED
# =========================================================

print()
print("=" * 70)
print("ADAPTIVE DECISION ENGINE TEST COMPLETED")
print("=" * 70)