from typing import Dict, Optional

from mock_interview.llm.provider import (
    get_llm_provider,
)

from mock_interview.interview.answer_analyzer import (
    analyze_answer as rule_based_analyze_answer,
)


# =========================================================
# INTERVIEW LLM ADAPTER
# =========================================================

class InterviewLLMAdapter:
    """
    Bridge between the interview system and the LLM layer.

    The interview system communicates only with this adapter.

    The adapter handles:

    - Question generation
    - Follow-up question generation
    - Answer analysis
    - Rule-based + LLM analysis
    """

    def __init__(
        self,
        provider: Optional[str] = None,
    ):
        """
        Create the LLM adapter.

        If provider is not explicitly supplied,
        the provider configured in .env is used.
        """

        if provider:

            self.llm = get_llm_provider(
                provider
            )

        else:

            self.llm = get_llm_provider()

    # =====================================================
    # QUESTION GENERATION
    # =====================================================

    def generate_question(
        self,
        context: Dict,
        category: Optional[str] = None,
        previous_question: str = "",
        previous_answer: str = "",
    ) -> Dict:
        """
        Generate one interview question.

        Supports both:

            generate_question(context)

        and:

            generate_question(
                context=context,
                category=...,
                previous_question=...,
                previous_answer=...,
            )

        This keeps compatibility with the existing
        orchestrator and older tests.
        """

        # -------------------------------------------------
        # Copy context so the original is not modified
        # -------------------------------------------------

        llm_context = {
            **context
        }

        # -------------------------------------------------
        # Explicit category
        # -------------------------------------------------

        if category:

            llm_context["category"] = (
                category
            )

        # -------------------------------------------------
        # Previous question
        # -------------------------------------------------

        if previous_question:

            llm_context["previous_question"] = (
                previous_question
            )

        # -------------------------------------------------
        # Previous answer
        # -------------------------------------------------

        if previous_answer:

            llm_context["previous_answer"] = (
                previous_answer
            )

        # -------------------------------------------------
        # Generate through provider
        # -------------------------------------------------

        result = self.llm.generate_question(
            llm_context
        )

        # -------------------------------------------------
        # Safety
        # -------------------------------------------------

        if not isinstance(
            result,
            dict,
        ):

            return {
                "question": str(result),

                "category": (
                    category
                    or context.get(
                        "category",
                        "",
                    )
                ),

                "difficulty": (
                    context.get(
                        "difficulty",
                        1,
                    )
                ),

                "method": "llm",
            }

        # -------------------------------------------------
        # Return normalized structure
        # -------------------------------------------------

        return {
            "question": result.get(
                "question",
                "",
            ),

            "category": result.get(
                "category",
                category
                or context.get(
                    "category",
                    "",
                ),
            ),

            "difficulty": result.get(
                "difficulty",
                context.get(
                    "difficulty",
                    1,
                ),
            ),

            "method": "llm",
        }

    # =====================================================
    # ANSWER ANALYSIS
    # =====================================================

    def analyze_answer(
        self,
        question: str,
        answer: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        """
        Analyze a candidate answer using:

        1. Rule-based analyzer
        2. LLM analyzer

        Both results are preserved.
        """

        if context is None:

            context = {}

        # -------------------------------------------------
        # Rule-based analysis
        # -------------------------------------------------

        rule_analysis = (
            rule_based_analyze_answer(
                question=question,
                answer=answer,
            )
        )

        # -------------------------------------------------
        # LLM context
        # -------------------------------------------------

        llm_context = {
            **context,

            "question": question,

            "answer": answer,
        }

        # -------------------------------------------------
        # LLM analysis
        # -------------------------------------------------

        llm_analysis = (
            self.llm.analyze_answer(
                llm_context
            )
        )

        # -------------------------------------------------
        # Combined result
        # -------------------------------------------------

        return {
            "question": question,

            "answer": answer,

            "rule_based": rule_analysis,

            "llm_based": llm_analysis,
        }

    # =====================================================
    # FOLLOW-UP QUESTION
    # =====================================================

    def generate_followup(
        self,
        context: Dict,
        previous_question: str,
        previous_answer: str,
    ) -> Dict:
        """
        Generate a contextual follow-up question.

        This uses the same underlying provider but explicitly
        tells the provider that the question is a follow-up.
        """

        followup_context = {
            **context,

            "category": "follow_up",

            "previous_question": (
                previous_question
            ),

            "previous_answer": (
                previous_answer
            ),
        }

        result = self.llm.generate_question(
            followup_context
        )

        # -------------------------------------------------
        # Safety
        # -------------------------------------------------

        if not isinstance(
            result,
            dict,
        ):

            return {
                "question": str(result),

                "category": "follow_up",

                "difficulty": context.get(
                    "difficulty",
                    1,
                ),

                "method": "llm",

                "action": "follow_up",
            }

        # -------------------------------------------------
        # Normalized result
        # -------------------------------------------------

        return {
            "question": result.get(
                "question",
                "",
            ),

            "category": result.get(
                "category",
                "follow_up",
            ),

            "difficulty": result.get(
                "difficulty",
                context.get(
                    "difficulty",
                    1,
                ),
            ),

            "method": "llm",

            "action": "follow_up",
        }


# =========================================================
# ADAPTER FACTORY
# =========================================================

def create_interview_llm(
    provider: Optional[str] = None,
) -> InterviewLLMAdapter:
    """
    Create the interview LLM adapter.

    If provider is None, the provider configured
    in .env is used.
    """

    return InterviewLLMAdapter(
        provider=provider
    )