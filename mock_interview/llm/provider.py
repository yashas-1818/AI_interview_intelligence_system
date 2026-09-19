from typing import Dict, Optional

from mock_interview.llm.base import BaseLLM
from mock_interview.llm.config import (
    LLM_PROVIDER,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)

from mock_interview.llm.gemini_provider import (
    GeminiLLM,
)


# =========================================================
# MOCK LLM PROVIDER
# =========================================================

class MockLLM(BaseLLM):
    """
    Development/testing LLM provider.

    This provider does not make any external API calls.
    It is useful for testing the interview pipeline
    without consuming Gemini API requests.
    """

    # =====================================================
    # BASIC GENERATION
    # =====================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = LLM_TEMPERATURE,
        max_tokens: int = LLM_MAX_TOKENS,
    ) -> str:

        return (
            "This is a mock LLM response. "
            "A real LLM provider can be connected later."
        )

    # =====================================================
    # QUESTION GENERATION
    # =====================================================

    def generate_question(
        self,
        context: Dict,
    ) -> Dict:
        """
        Generate a deterministic question for testing.

        The real Gemini provider will generate
        dynamic questions.
        """

        category = context.get(
            "category",
            "technical",
        )

        role = context.get(
            "role",
            "this role",
        )

        project = context.get(
            "project",
            "",
        )

        skill = context.get(
            "skill",
            "",
        )

        responsibility = context.get(
            "responsibility",
            "",
        )

        previous_answer = context.get(
            "previous_answer",
            "",
        )

        difficulty = context.get(
            "difficulty",
            1,
        )

        # -------------------------------------------------
        # FOLLOW-UP QUESTION
        # -------------------------------------------------

        if previous_answer:

            if project:

                question = (
                    f"You mentioned your work on {project}. "
                    "Could you explain your specific technical "
                    "contribution and one challenge you faced?"
                )

            else:

                question = (
                    "Could you elaborate on your previous "
                    "answer and provide a specific example?"
                )

            return {
                "question": question,
                "category": category,
                "difficulty": difficulty,
            }

        # -------------------------------------------------
        # PROJECT QUESTION
        # -------------------------------------------------

        if (
            category == "project"
            and project
        ):

            return {
                "question": (
                    f"Could you explain the architecture "
                    f"of your {project} project?"
                ),
                "category": category,
                "difficulty": difficulty,
            }

        # -------------------------------------------------
        # TECHNICAL QUESTION
        # -------------------------------------------------

        if (
            category == "technical"
            and skill
        ):

            return {
                "question": (
                    f"Can you explain your practical "
                    f"experience with {skill}?"
                ),
                "category": category,
                "difficulty": difficulty,
            }

        # -------------------------------------------------
        # ROLE-SPECIFIC QUESTION
        # -------------------------------------------------

        if (
            category == "role_specific"
            and responsibility
        ):

            return {
                "question": (
                    f"How would you approach "
                    f"{responsibility} in a "
                    "production environment?"
                ),
                "category": category,
                "difficulty": difficulty,
            }

        # -------------------------------------------------
        # SKILL-GAP QUESTION
        # -------------------------------------------------

        if (
            category == "skill_gap"
            and skill
        ):

            return {
                "question": (
                    f"This role requires {skill}. "
                    f"How familiar are you with {skill}, "
                    "and how would you apply it?"
                ),
                "category": category,
                "difficulty": difficulty,
            }

        # -------------------------------------------------
        # DEFAULT QUESTION
        # -------------------------------------------------

        return {
            "question": (
                f"Why do you think your experience "
                f"makes you suitable for the "
                f"{role} position?"
            ),
            "category": category,
            "difficulty": difficulty,
        }

    # =====================================================
    # ANSWER ANALYSIS
    # =====================================================

    def analyze_answer(
        self,
        context: Dict,
    ) -> Dict:
        """
        Mock answer analysis.

        The real Gemini provider performs semantic
        evaluation.
        """

        return {
            "relevance": "medium",
            "completeness": "medium",
            "technical_depth": "medium",
            "clarity": "good",
            "needs_follow_up": True,
            "suggested_action": "probe_deeper",
            "reason": (
                "Mock provider response. "
                "Real semantic analysis will be "
                "performed by Gemini."
            ),
        }


# =========================================================
# LLM PROVIDER FACTORY
# =========================================================

def get_llm_provider(
    provider: Optional[str] = None,
) -> BaseLLM:
    """
    Return the configured LLM provider.

    Supported providers:

        mock
        gemini

    The provider can be explicitly passed, otherwise
    LLM_PROVIDER from .env is used.
    """

    selected_provider = (
        provider
        or LLM_PROVIDER
    ).lower().strip()

    # =====================================================
    # MOCK PROVIDER
    # =====================================================

    if selected_provider == "mock":

        return MockLLM()

    # =====================================================
    # GEMINI PROVIDER
    # =====================================================

    if selected_provider == "gemini":

        return GeminiLLM()

    # =====================================================
    # UNSUPPORTED PROVIDER
    # =====================================================

    raise ValueError(
        f"Unsupported LLM provider: "
        f"{selected_provider}. "
        f"Supported providers: mock, gemini."
    )