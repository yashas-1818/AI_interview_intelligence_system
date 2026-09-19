from typing import Dict


# =========================================================
# DECISION TYPES
# =========================================================

FOLLOW_UP = "follow_up"
NEW_TOPIC = "new_topic"
INCREASE_DIFFICULTY = "increase_difficulty"
DECREASE_DIFFICULTY = "decrease_difficulty"
CLARIFY = "clarify"
CONTINUE = "continue"
END_INTERVIEW = "end_interview"


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def _get_answer_topics(assessment: Dict) -> Dict:
    """
    Safely retrieve topics detected in the candidate's answer.
    """

    return assessment.get(
        "answer_topics",
        {}
    )


def _get_primary_target(assessment: Dict) -> str:
    """
    Get the most important topic detected in the answer.
    """

    follow_up_targets = assessment.get(
        "follow_up_targets",
        {}
    )

    return follow_up_targets.get(
        "primary_target",
        ""
    )


def _mark_answer_topics_covered(
    assessment: Dict,
    state,
) -> None:
    """
    Move topics mentioned in the candidate's answer
    from remaining topics to covered topics.

    This prevents the same topic from repeatedly appearing
    as an unexplored topic.
    """

    answer_topics = _get_answer_topics(assessment)

    topics = answer_topics.get(
        "topics",
        []
    )

    if not topics:
        return

    for topic in topics:
        state.mark_topic_covered(topic)


def _should_complete_category(
    assessment: Dict,
    state,
) -> bool:
    """
    Determine whether the current interview category
    has been sufficiently explored.

    A category can be completed when:
    - the answer is strong, or
    - the answer is good and no follow-up is required, or
    - the maximum follow-ups have already been used.
    """

    follow_up = assessment.get(
        "follow_up",
        {}
    )

    overall = assessment.get(
        "overall_quality",
        {}
    )

    answer_quality = assessment.get(
        "quality",
        overall.get("level", "moderate"),
    )

    needs_follow_up = (
        assessment["needs_followup"]
        if "needs_followup" in assessment
        else follow_up.get("needs_follow_up", False)
    )

    # Follow-up turns always complete the active category so the interview progresses
    if getattr(state, "current_category", "") == "follow_up":
        return True

    # Strong answer = category can normally progress
    if answer_quality == "strong":
        return True

    # Good answer without another required follow-up
    if (
        answer_quality == "good"
        and not needs_follow_up
    ):
        return True

    # Maximum follow-ups reached
    if not state.can_ask_followup():
        return True

    return False


# =========================================================
# DECISION ENGINE
# =========================================================

def decide_next_action(
    assessment: Dict,
    state,
) -> Dict:
    """
    Decide what the interviewer should do after
    receiving and analyzing a candidate's answer.

    This version uses:
    - answer quality
    - follow-up requirements
    - detected answer topics
    - follow-up targets
    - follow-up limits
    - category progression
    """

    follow_up = assessment.get(
        "follow_up",
        {}
    )

    overall = assessment.get(
        "overall_quality",
        {}
    )

    answer_quality = assessment.get(
        "quality",
        overall.get("level", "moderate"),
    )

    needs_follow_up = (
        assessment["needs_followup"]
        if "needs_followup" in assessment
        else follow_up.get("needs_follow_up", False)
    )

    suggested_action = (
        assessment.get("followup_action")
        or follow_up.get("action", "continue")
    )

    primary_target = _get_primary_target(
        assessment
    )

    # -----------------------------------------------------
    # 1. Empty / unclear answer
    # -----------------------------------------------------

    if suggested_action == "clarify":
        if state.can_ask_followup():
            return {
                "action": CLARIFY,
                "reason": (
                    "The candidate's answer was "
                    "empty or not sufficiently relevant."
                ),
                "difficulty_change": 0,
                "target": primary_target,
                "complete_category": False,
            }
        else:
            return {
                "action": DECREASE_DIFFICULTY,
                "reason": (
                    "Clarification already attempted. "
                    "Reducing difficulty and moving forward."
                ),
                "difficulty_change": -1,
                "target": primary_target,
                "complete_category": True,
            }

    # -----------------------------------------------------
    # 2. Mark detected topics as covered
    # -----------------------------------------------------

    _mark_answer_topics_covered(
        assessment,
        state,
    )

    # -----------------------------------------------------
    # 3. Follow-up required
    # -----------------------------------------------------

    # Only follow up if not already in a follow-up and state allows it
    if (
        needs_follow_up
        and state.current_category != "follow_up"
        and state.can_ask_followup()
    ):

        return {
            "action": FOLLOW_UP,
            "reason": (
                "The answer requires deeper "
                "explanation before moving on."
            ),
            "difficulty_change": 0,
            "target": primary_target,
            "complete_category": False,
        }

    # -----------------------------------------------------
    # 4. Strong answer
    # -----------------------------------------------------

    if answer_quality == "strong":

        return {
            "action": INCREASE_DIFFICULTY,
            "reason": (
                "The candidate provided a strong "
                "and sufficiently detailed answer."
            ),
            "difficulty_change": 1,
            "target": primary_target,
            "complete_category": True,
        }

    # -----------------------------------------------------
    # 5. Good answer
    # -----------------------------------------------------

    if answer_quality == "good":

        return {
            "action": NEW_TOPIC,
            "reason": (
                "The candidate provided a good answer. "
                "Move to the next interview topic."
            ),
            "difficulty_change": 0,
            "target": primary_target,
            "complete_category": True,
        }

    # -----------------------------------------------------
    # 6. Weak answer
    # -----------------------------------------------------

    if answer_quality == "weak":
        # If this was already a follow-up or no further follow-up allowed, complete category
        complete = (state.current_category == "follow_up") or not state.can_ask_followup()
        return {
            "action": DECREASE_DIFFICULTY,
            "reason": (
                "The candidate's answer was weak. "
                "Reduce difficulty and move to the next topic."
            ),
            "difficulty_change": -1,
            "target": primary_target,
            "complete_category": complete,
        }

    # -----------------------------------------------------
    # 7. Moderate answer
    # -----------------------------------------------------

    if _should_complete_category(
        assessment,
        state,
    ):

        return {
            "action": NEW_TOPIC,
            "reason": (
                "The current topic has been sufficiently "
                "explored. Move to a new topic."
            ),
            "difficulty_change": 0,
            "target": primary_target,
            "complete_category": True,
        }

    return {
        "action": CONTINUE,
        "reason": (
            "The answer was acceptable. "
            "Continue with the interview."
        ),
        "difficulty_change": 0,
        "target": primary_target,
        "complete_category": False,
    }


# =========================================================
# APPLY DECISION TO STATE
# =========================================================

def apply_decision(
    decision: Dict,
    state,
) -> None:
    """
    Apply the decision to ConversationState.
    """

    action = decision.get(
        "action"
    )

    complete_category = decision.get(
        "complete_category",
        False,
    )

    # -----------------------------------------------------
    # Complete current category
    # -----------------------------------------------------

    if complete_category:

        state.complete_current_category()

    # -----------------------------------------------------
    # Follow-up
    # -----------------------------------------------------

    if action == FOLLOW_UP:

        state.record_followup()

        return

    # -----------------------------------------------------
    # Increase difficulty
    # -----------------------------------------------------

    if action == INCREASE_DIFFICULTY:

        state.increase_difficulty()

        state.reset_followups()

        return

    # -----------------------------------------------------
    # Decrease difficulty
    # -----------------------------------------------------

    if action == DECREASE_DIFFICULTY:

        state.decrease_difficulty()

        state.reset_followups()

        return

    # -----------------------------------------------------
    # New topic
    # -----------------------------------------------------

    if action == NEW_TOPIC:

        state.reset_followups()

        return

    # -----------------------------------------------------
    # Clarification
    # -----------------------------------------------------

    if action == CLARIFY:

        state.record_followup()

        return

    # -----------------------------------------------------
    # End interview
    # -----------------------------------------------------

    if action == END_INTERVIEW:

        state.end_session()

        return


# =========================================================
# HIGH-LEVEL PROCESSOR
# =========================================================

def process_answer(
    assessment: Dict,
    state,
) -> Dict:
    """
    Process the answer assessment and update interview state.
    """

    decision = decide_next_action(
        assessment=assessment,
        state=state,
    )

    apply_decision(
        decision=decision,
        state=state,
    )

    return decision