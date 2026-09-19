from mock_interview.interview.conversation_state import (
    ConversationState
)

from mock_interview.interview.answer_analyzer import (
    analyze_answer
)


# =========================================================
# CREATE INTERVIEW SESSION
# =========================================================

state = ConversationState(
    candidate_name="H S YASHAS GOWDA",
    role="AI/ML Engineer",
)


print("=" * 70)
print("CONVERSATION STATE + ANSWER ANALYZER TEST")
print("=" * 70)


# =========================================================
# SESSION INFORMATION
# =========================================================

print()
print("SESSION ID:")
print(state.session_id)

print()
print("CANDIDATE:")
print(state.candidate_name)

print()
print("ROLE:")
print(state.role)


# =========================================================
# ADD INTERVIEW TOPICS
# =========================================================

state.add_topic("Python")
state.add_topic("NLP")
state.add_topic("Skylark")
state.add_topic("PyTorch")


print()
print("TOPICS REMAINING:")
print(state.topics_remaining)


# =========================================================
# SET FIRST QUESTION
# =========================================================

question = (
    "Could you walk me through your "
    "Skylark project?"
)

state.set_question(
    question=question,
    category="project",
)


print()
print("CURRENT QUESTION:")
print(state.current_question)

print()
print("QUESTION CATEGORY:")
print(state.current_category)

print()
print("QUESTION NUMBER:")
print(state.question_number)


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


print()
print("CANDIDATE ANSWER:")
print(answer)


# =========================================================
# RECORD ANSWER
# =========================================================

state.record_answer(
    answer
)


print()
print("LAST ANSWER STORED:")
print(state.get_last_answer())


# =========================================================
# ANALYZE ANSWER
# =========================================================

assessment = analyze_answer(
    question=state.current_question,
    answer=state.get_last_answer(),
)


# Store analysis inside conversation state
state.set_answer_assessment(
    assessment
)


# =========================================================
# DISPLAY ANSWER ANALYSIS
# =========================================================

print()
print("=" * 70)
print("ANSWER ANALYSIS")
print("=" * 70)


print()
print("ANSWER LENGTH")
print("-" * 70)

print(
    "Word Count:",
    assessment["answer_length"]["word_count"]
)

print(
    "Length Level:",
    assessment["answer_length"]["length_level"]
)


print()
print("RELEVANCE")
print("-" * 70)

print(
    "Score:",
    assessment["relevance"]["score"]
)

print(
    "Level:",
    assessment["relevance"]["level"]
)

print(
    "Matched Keywords:",
    assessment["relevance"]["matched_keywords"]
)


print()
print("TECHNICAL DEPTH")
print("-" * 70)

print(
    "Level:",
    assessment["technical_depth"]["level"]
)

print(
    "Technical Indicators:",
    assessment["technical_depth"]["indicators"]
)


print()
print("COMPLETENESS")
print("-" * 70)

print(
    "Level:",
    assessment["completeness"]["level"]
)

print(
    "Completeness Indicators:",
    assessment["completeness"]["indicators"]
)


print()
print("CLARITY")
print("-" * 70)

print(
    "Level:",
    assessment["clarity"]["level"]
)

print(
    "Filler Count:",
    assessment["clarity"]["filler_count"]
)

print(
    "Filler Ratio:",
    assessment["clarity"]["filler_ratio"]
)


print()
print("VAGUENESS")
print("-" * 70)

print(
    "Level:",
    assessment["vagueness"]["level"]
)

print(
    "Vague Phrases:",
    assessment["vagueness"]["phrases"]
)


# =========================================================
# FOLLOW-UP DECISION
# =========================================================

print()
print("FOLLOW-UP DECISION")
print("-" * 70)

print(
    "Needs Follow-Up:",
    assessment["follow_up"]["needs_follow_up"]
)

print(
    "Suggested Action:",
    assessment["follow_up"]["action"]
)

print(
    "Reasons:",
    assessment["follow_up"]["reasons"]
)


# =========================================================
# OVERALL QUALITY
# =========================================================

print()
print("OVERALL ANSWER QUALITY")
print("-" * 70)

print(
    "Score:",
    assessment["overall_quality"]["score"],
    "/ 16"
)

print(
    "Percentage:",
    assessment["overall_quality"]["percentage"],
    "%"
)

print(
    "Level:",
    assessment["overall_quality"]["level"]
)


# =========================================================
# MARK TOPIC AS COVERED
# =========================================================

state.mark_topic_covered(
    "Skylark"
)


print()
print("=" * 70)
print("TOPIC PROGRESS")
print("=" * 70)

print()
print("TOPICS COVERED:")
print(state.topics_covered)

print()
print("TOPICS REMAINING:")
print(state.topics_remaining)


# =========================================================
# DIFFICULTY UPDATE
# =========================================================

print()
print("=" * 70)
print("DIFFICULTY")
print("=" * 70)

print()
print("Current Difficulty:")
print(state.current_difficulty)


# Increase difficulty if answer is strong
if assessment["overall_quality"]["level"] in [
    "strong",
    "good",
]:

    state.increase_difficulty()

    print()
    print(
        "Answer quality is good."
    )

    print(
        "Difficulty increased."
    )

else:

    print()
    print(
        "Difficulty remains unchanged."
    )


print()
print(
    "Updated Difficulty:",
    state.current_difficulty
)


# =========================================================
# FOLLOW-UP STATUS
# =========================================================

print()
print("=" * 70)
print("FOLLOW-UP STATUS")
print("=" * 70)

print()
print(
    "Can Ask Follow-Up:",
    state.can_ask_followup()
)


# =========================================================
# CONVERSATION HISTORY
# =========================================================

print()
print("=" * 70)
print("RECENT CONVERSATION HISTORY")
print("=" * 70)


for item in state.get_recent_history():

    print()
    print(
        "Question Number:",
        item["question_number"]
    )

    print(
        "Category:",
        item["category"]
    )

    print(
        "Question:",
        item["question"]
    )

    print(
        "Answer:",
        item["answer"]
    )


# =========================================================
# COMPLETE STATE
# =========================================================

print()
print("=" * 70)
print("FINAL CONVERSATION STATE")
print("=" * 70)

final_state = state.to_dict()

print(
    final_state
)


# =========================================================
# TEST COMPLETED
# =========================================================

print()
print("=" * 70)
print("CONVERSATION + ANSWER ANALYZER TEST COMPLETED")
print("=" * 70)