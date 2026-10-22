from datetime import datetime
from typing import Dict, List, Optional


class ConversationState:
    """
    Maintains the complete state of an adaptive interview session.

    Important:
    - Interview categories represent the actual interview flow.
    - "follow_up" is a temporary question mode and should NOT become
      a completed interview category.
    - active_category stores the real category being explored when
      the current question happens to be a follow-up.
    """

    def __init__(
        self,
        candidate_name: str = "",
        role: str = "",
        session_id: Optional[str] = None,
        max_questions: int = 15,
        max_consecutive_followups: int = 1,
    ):
        self.candidate_name = candidate_name
        self.role = role

        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.started_at = datetime.now().isoformat()
        self.ended_at: Optional[str] = None

        # Budget & limits
        self.max_questions = max(5, max_questions)
        self.max_consecutive_followups = max_consecutive_followups
        self.consecutive_followups = 0

        # Current question state
        self.current_category = "introduction"
        self.active_category = "introduction"
        self.current_question = ""
        self.current_difficulty = 1
        self.question_number = 0

        # Conversation history
        self.questions_asked: List[str] = []
        self.answers_received: List[str] = []
        self.conversation_history: List[Dict] = []
        self.skipped_questions: List[str] = []

        # Category tracking
        self.completed_categories: List[str] = []

        # Topic tracking
        self.topics_covered: List[str] = []
        self.topics_remaining: List[str] = []

        # Follow-up tracking
        self.followups_asked = 0
        self.max_followups_per_topic = max_consecutive_followups

        # Last answer
        self.last_answer_assessment: Optional[Dict] = None

        self.is_active = True

    # ------------------------------------------------------------------
    # QUESTION MANAGEMENT
    # ------------------------------------------------------------------

    def set_question(
        self,
        question: str,
        category: str,
        difficulty: Optional[int] = None,
    ):
        """
        Set the next interview question.

        If category == "follow_up", preserve the actual interview
        category in active_category.
        """

        if category != "follow_up":
            self.active_category = category
            self.reset_followups()

        self.current_category = category
        self.current_question = question

        if difficulty is not None:
            self.current_difficulty = difficulty

        self.question_number += 1

        self.questions_asked.append(question)

    # ------------------------------------------------------------------
    # ANSWER MANAGEMENT
    # ------------------------------------------------------------------

    def record_answer(
        self,
        answer: str,
        speech_telemetry: Optional[Dict] = None,
        speech_analytics: Optional[Dict] = None,
    ):
        """
        Record the candidate's answer against the current question.
        Optionally stores raw speech telemetry and computed speech analytics.
        """

        self.answers_received.append(answer)

        entry = {
            "question_number": self.question_number,
            "category": self.current_category,
            "active_category": self.active_category,
            "difficulty": self.current_difficulty,
            "question": self.current_question,
            "answer": answer,
        }
        if speech_telemetry is not None:
            entry["speech_telemetry"] = speech_telemetry
        if speech_analytics is not None:
            entry["speech_analytics"] = speech_analytics

        self.conversation_history.append(entry)

    def record_skip(
        self,
        question: Optional[str] = None,
        speech_analytics: Optional[Dict] = None,
    ):
        """
        Record that the current question was skipped by the candidate.
        Ensures the question is marked as consumed, added to history with
        explicit skipped assessment (score=None), and consumed from budget.
        """
        q = question or self.current_question
        if q and q not in self.skipped_questions:
            self.skipped_questions.append(q)
        if q and q not in self.questions_asked:
            self.questions_asked.append(q)

        self.answers_received.append("[Skipped]")
        skip_entry = {
            "question_number": self.question_number,
            "category": self.current_category,
            "active_category": self.active_category,
            "difficulty": self.current_difficulty,
            "question": q,
            "answer": "[Skipped]",
            "skipped": True,
            "assessment": {
                "quality": "skipped",
                "score": None,
                "technical_depth_level": "skipped",
                "clarity_level": "skipped",
                "relevance": {"level": "none", "score": 0.0},
                "completeness_level": "none",
                "vagueness_level": "none",
                "needs_followup": False,
            },
            "decision": {
                "action": "skip",
                "complete_category": True,
                "trigger_followup": False,
                "difficulty_change": 0,
            },
        }
        if speech_analytics is not None:
            skip_entry["speech_analytics"] = speech_analytics

        self.conversation_history.append(skip_entry)

    def set_speech_analytics_for_last_turn(self, speech_analytics: Dict):
        """Attach or update speech analytics on the most recent turn."""
        if self.conversation_history:
            self.conversation_history[-1]["speech_analytics"] = speech_analytics

    def has_question_been_asked(self, question: str) -> bool:
        """Check if a question has already been asked or skipped."""
        return question in self.questions_asked or question in self.skipped_questions

    # ------------------------------------------------------------------
    # CATEGORY MANAGEMENT
    # ------------------------------------------------------------------

    def mark_category_completed(self, category: str):
        """
        Mark an actual interview category as completed.

        "follow_up" is never stored as a completed category.
        """

        if not category:
            return

        if category == "follow_up":
            category = self.active_category

        if category not in self.completed_categories:
            self.completed_categories.append(category)

    def is_category_completed(self, category: str) -> bool:
        """
        Check whether an interview category is completed.
        """

        if category == "follow_up":
            category = self.active_category

        return category in self.completed_categories

    def complete_current_category(self):
        """
        Complete the actual category being explored.

        This is the important fix:
        if the current question is a follow-up, complete the
        underlying active category instead of "follow_up".
        """

        category_to_complete = self.active_category

        self.mark_category_completed(category_to_complete)

        # Follow-up state is reset after completing the category.
        self.reset_followups()

    # ------------------------------------------------------------------
    # TOPIC MANAGEMENT
    # ------------------------------------------------------------------

    def add_topic(self, topic: str):
        """
        Add a topic to the remaining-topic pool if it does not already exist.
        """

        topic = topic.strip()

        if not topic:
            return

        if topic not in self.topics_remaining:
            self.topics_remaining.append(topic)

    def mark_topic_covered(self, topic: str):
        """
        Mark a topic as covered.
        """

        topic = topic.strip()

        if not topic:
            return

        if topic not in self.topics_covered:
            self.topics_covered.append(topic)

        if topic in self.topics_remaining:
            self.topics_remaining.remove(topic)

    def mark_topics_covered(self, topics: List[str]):
        """
        Mark multiple topics as covered.
        """

        for topic in topics:
            self.mark_topic_covered(topic)

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # FOLLOW-UP MANAGEMENT
    # ------------------------------------------------------------------

    def record_followup(self):
        """
        Increment the number of follow-ups asked for the current topic.
        """
        self.consecutive_followups += 1
        self.followups_asked += 1

    def reset_followups(self):
        """
        Reset follow-up count when moving to a new actual category/topic.
        """
        self.consecutive_followups = 0
        self.followups_asked = 0

    def can_ask_followup(self) -> bool:
        """
        Return whether another follow-up can be asked.
        Enforces maximum 1 consecutive follow-up by default and reserves
        at least 1 slot for closing.
        """
        return (
            self.consecutive_followups < self.max_consecutive_followups
            and (self.max_questions - self.question_number) > 1
        )

    # ------------------------------------------------------------------
    # BUDGET MANAGEMENT
    # ------------------------------------------------------------------

    def is_budget_exhausted(self) -> bool:
        """Return whether the interview has reached the maximum question budget."""
        return len(self.answers_received) >= self.max_questions

    def remaining_budget(self) -> int:
        """Return the number of remaining question slots."""
        return max(0, self.max_questions - len(self.answers_received))

    # ------------------------------------------------------------------
    # DIFFICULTY MANAGEMENT
    # ------------------------------------------------------------------

    def increase_difficulty(self):
        """
        Increase interview difficulty up to level 5.
        """

        self.current_difficulty = min(
            self.current_difficulty + 1,
            5,
        )

    def decrease_difficulty(self):
        """
        Decrease interview difficulty down to level 1.
        """

        self.current_difficulty = max(
            self.current_difficulty - 1,
            1,
        )

    # ------------------------------------------------------------------
    # ANSWER ASSESSMENT
    # ------------------------------------------------------------------

    def set_answer_assessment(self, assessment: Dict):
        self.last_answer_assessment = assessment

    def get_last_answer(self) -> Optional[str]:
        if not self.answers_received:
            return None

        return self.answers_received[-1]

    def get_last_question(self) -> Optional[str]:
        if not self.questions_asked:
            return None

        return self.questions_asked[-1]

    # ------------------------------------------------------------------
    # HISTORY
    # ------------------------------------------------------------------

    def get_recent_history(self, limit: int = 5) -> List[Dict]:
        return self.conversation_history[-limit:]

    # ------------------------------------------------------------------
    # SESSION MANAGEMENT
    # ------------------------------------------------------------------

    def end_session(self):
        self.is_active = False
        self.ended_at = datetime.now().isoformat()

    # ------------------------------------------------------------------
    # SERIALIZATION
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict:
        return {
            "candidate_name": self.candidate_name,
            "role": self.role,
            "session_id": self.session_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,

            "max_questions": self.max_questions,
            "consecutive_followups": self.consecutive_followups,
            "max_consecutive_followups": self.max_consecutive_followups,

            "current_category": self.current_category,
            "active_category": self.active_category,
            "current_question": self.current_question,
            "current_difficulty": self.current_difficulty,
            "question_number": self.question_number,

            "questions_asked": self.questions_asked,
            "skipped_questions": list(self.skipped_questions),
            "answers_received": self.answers_received,
            "conversation_history": self.conversation_history,

            "completed_categories": self.completed_categories,

            "topics_covered": self.topics_covered,
            "topics_remaining": self.topics_remaining,

            "followups_asked": self.followups_asked,
            "max_followups_per_topic": self.max_followups_per_topic,

            "last_answer_assessment": self.last_answer_assessment,

            "is_active": self.is_active,
        }