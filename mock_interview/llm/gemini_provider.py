import re
import time
from typing import Dict, Optional

from google import genai
from google.genai import types

from pydantic import BaseModel, Field

from mock_interview.llm.base import BaseLLM

from mock_interview.llm.config import (
    LLM_API_KEY,
    LLM_MODEL,
    LLM_FALLBACK_MODEL,
    LLM_MAX_RETRIES,
)


# =========================================================
# STRUCTURED QUESTION RESPONSE
# =========================================================

class QuestionResponse(BaseModel):

    question: str = Field(
        description="The interview question."
    )

    category: str = Field(
        description="Interview category."
    )

    difficulty: int = Field(
        description="Difficulty from 1 to 5."
    )


# =========================================================
# STRUCTURED ANSWER ANALYSIS
# =========================================================

class AnswerAnalysisResponse(BaseModel):

    relevance: str

    completeness: str

    technical_depth: str

    clarity: str

    needs_follow_up: bool

    suggested_action: str

    reason: str


# =========================================================
# GEMINI PROVIDER
# =========================================================

class GeminiLLM(BaseLLM):

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):

        self.api_key = (
            api_key or LLM_API_KEY
        )

        self.model = (
            model or LLM_MODEL
        )

        self.fallback_model = (
            LLM_FALLBACK_MODEL
        )

        self.max_retries = (
            LLM_MAX_RETRIES
        )

        if not self.api_key:

            raise ValueError(
                "Gemini API key is not configured. "
                "Check LLM_API_KEY in .env."
            )

        if not self.model:

            raise ValueError(
                "Gemini model is not configured. "
                "Check LLM_MODEL in .env."
            )

        self.client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(timeout=10000),
        )

    # =====================================================
    # BASIC CONFIG
    # =====================================================

    @staticmethod
    def _config(
        max_output_tokens: int,
        thinking_level: str = "low",
        response_schema=None,
    ):

        config_kwargs = {
            "max_output_tokens": max_output_tokens,

            "thinking_config": (
                types.ThinkingConfig(
                    thinking_level=thinking_level
                )
            ),
        }

        if response_schema is not None:

            config_kwargs[
                "response_mime_type"
            ] = "application/json"

            config_kwargs[
                "response_schema"
            ] = response_schema

        return types.GenerateContentConfig(
            **config_kwargs
        )

    # =====================================================
    # TEMPORARY ERROR DETECTION
    # =====================================================

    @staticmethod
    def _is_retryable_error(
        error: Exception,
    ) -> bool:

        message = str(error).lower()

        # 429 quota exhaustion cannot be fixed by immediate 1-2s retry
        if (
            "429" in message
            or "resource_exhausted" in message
            or "quota" in message
        ):
            return False

        retryable_patterns = [
            "503",
            "unavailable",
            "high demand",
            "temporarily unavailable",
            "internal server error",
            "timeout",
            "timed out",
        ]

        return any(
            pattern in message
            for pattern in retryable_patterns
        )

    # =====================================================
    # GEMINI REQUEST WITH RETRY
    # =====================================================

    def _generate_with_retry(
        self,
        model: str,
        contents,
        config,
    ):

        last_error = None

        for attempt in range(
            self.max_retries + 1
        ):

            try:

                return (
                    self.client
                    .models
                    .generate_content(
                        model=model,
                        contents=contents,
                        config=config,
                    )
                )

            except Exception as error:

                last_error = error

                if not self._is_retryable_error(
                    error
                ):

                    raise

                # -----------------------------------------
                # No more retries
                # -----------------------------------------

                if attempt >= self.max_retries:

                    break

                # -----------------------------------------
                # Exponential backoff
                # -----------------------------------------

                wait_time = 2 ** attempt

                print(
                    f"Gemini temporary failure "
                    f"(attempt {attempt + 1}/"
                    f"{self.max_retries + 1}). "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(
                    wait_time
                )

        raise RuntimeError(
            f"Gemini request failed after "
            f"{self.max_retries + 1} attempts: "
            f"{last_error}"
        )

    # =====================================================
    # BASIC GENERATION
    # =====================================================

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:

        if system_prompt:

            contents = (
                "SYSTEM INSTRUCTIONS:\n"
                f"{system_prompt}\n\n"
                "USER REQUEST:\n"
                f"{prompt}"
            )

        else:

            contents = prompt

        config = self._config(
            max_output_tokens=max_tokens,
            thinking_level="low",
        )

        # -------------------------------------------------
        # Primary model
        # -------------------------------------------------

        try:

            response = (
                self._generate_with_retry(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
            )

        except Exception as primary_error:

            # -------------------------------------------------
            # Fallback model
            # -------------------------------------------------

            if (
                self.fallback_model
                and self.fallback_model
                != self.model
            ):

                print(
                    "Primary Gemini model unavailable."
                )

                print(
                    "Trying fallback model: "
                    f"{self.fallback_model}"
                )

                try:

                    response = (
                        self._generate_with_retry(
                            model=self.fallback_model,
                            contents=contents,
                            config=config,
                        )
                    )

                except Exception as fallback_error:

                    raise RuntimeError(
                        "Both Gemini primary and "
                        "fallback models failed.\n\n"
                        f"Primary error: "
                        f"{primary_error}\n\n"
                        f"Fallback error: "
                        f"{fallback_error}"
                    ) from fallback_error

            else:

                raise RuntimeError(
                    "Gemini generation failed: "
                    f"{primary_error}"
                ) from primary_error

        if not response.text:

            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return response.text.strip()

    # =====================================================
    # QUESTION GENERATION
    # =====================================================

    def generate_question(
        self,
        context: Dict,
    ) -> Dict:

        prompt = (
            self._build_question_prompt(
                context
            )
        )

        config = self._config(
            max_output_tokens=1000,
            thinking_level="low",
            response_schema=QuestionResponse,
        )

        # -------------------------------------------------
        # Primary model
        # -------------------------------------------------

        try:

            response = (
                self._generate_with_retry(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
            )

        except Exception as primary_error:

            # -------------------------------------------------
            # Fallback
            # -------------------------------------------------

            if (
                self.fallback_model
                and self.fallback_model
                != self.model
            ):

                print(
                    "Primary Gemini model unavailable "
                    "for question generation."
                )

                print(
                    "Trying fallback model: "
                    f"{self.fallback_model}"
                )

                try:

                    response = (
                        self._generate_with_retry(
                            model=self.fallback_model,
                            contents=prompt,
                            config=config,
                        )
                    )

                except Exception as fallback_error:

                    raise RuntimeError(
                        "Gemini question generation "
                        "failed on both models.\n\n"
                        f"Primary error: "
                        f"{primary_error}\n\n"
                        f"Fallback error: "
                        f"{fallback_error}"
                    ) from fallback_error

            else:

                raise RuntimeError(
                    "Gemini question generation failed: "
                    f"{primary_error}"
                ) from primary_error

        if not response.text:

            raise RuntimeError(
                "Gemini returned an empty "
                "question response."
            )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\s*```$", "", raw_text)

        try:

            result = (
                QuestionResponse
                .model_validate_json(
                    raw_text
                )
            )

        except Exception as error:

            raise RuntimeError(
                "Gemini returned invalid "
                f"question JSON: {error}\n"
                f"Raw response: {response.text}"
            ) from error

        difficulty = max(
            1,
            min(
                5,
                result.difficulty,
            ),
        )

        return {
            "question": result.question.strip(),

            "category": result.category.strip(),

            "difficulty": difficulty,
        }

    # =====================================================
    # ANSWER ANALYSIS
    # =====================================================

    def analyze_answer(
        self,
        context: Dict,
    ) -> Dict:

        prompt = (
            self._build_answer_analysis_prompt(
                context
            )
        )

        config = self._config(
            max_output_tokens=1500,
            thinking_level="low",
            response_schema=(
                AnswerAnalysisResponse
            ),
        )

        # -------------------------------------------------
        # Primary model
        # -------------------------------------------------

        try:

            response = (
                self._generate_with_retry(
                    model=self.model,
                    contents=prompt,
                    config=config,
                )
            )

        except Exception as primary_error:

            if (
                self.fallback_model
                and self.fallback_model
                != self.model
            ):

                print(
                    "Primary Gemini model unavailable "
                    "for answer analysis."
                )

                print(
                    "Trying fallback model: "
                    f"{self.fallback_model}"
                )

                try:

                    response = (
                        self._generate_with_retry(
                            model=self.fallback_model,
                            contents=prompt,
                            config=config,
                        )
                    )

                except Exception as fallback_error:

                    raise RuntimeError(
                        "Gemini answer analysis "
                        "failed on both models.\n\n"
                        f"Primary error: "
                        f"{primary_error}\n\n"
                        f"Fallback error: "
                        f"{fallback_error}"
                    ) from fallback_error

            else:

                raise RuntimeError(
                    "Gemini answer analysis failed: "
                    f"{primary_error}"
                ) from primary_error

        if not response.text:

            raise RuntimeError(
                "Gemini returned an empty "
                "answer analysis."
            )

        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            raw_text = re.sub(r"\s*```$", "", raw_text)

        try:

            result = (
                AnswerAnalysisResponse
                .model_validate_json(
                    raw_text
                )
            )

        except Exception as error:

            raise RuntimeError(
                "Gemini returned invalid "
                f"answer analysis JSON: {error}\n"
                f"Raw response: {response.text}"
            ) from error

        return result.model_dump()

    # =====================================================
    # QUESTION PROMPT
    # =====================================================

    def _build_question_prompt(
        self,
        context: Dict,
    ) -> str:

        return f"""
You are an expert professional interviewer.

Generate exactly ONE interview question for
the candidate below.

Candidate:
{context.get("candidate_name", "")}

Target Role:
{context.get("role", "")}

Interview Category:
{context.get("category", "technical")}

Difficulty:
{context.get("difficulty", 1)}/5

Candidate Skills:
{context.get("candidate_skills", [])}

Skill Gaps:
{context.get("skill_gaps", [])}

Projects:
{context.get("project_topics", [])}

Role Responsibilities:
{context.get("role_topics", [])}

Previous Question:
{context.get("previous_question", "")}

Previous Answer:
{context.get("previous_answer", "")}

Questions Already Asked in This Session (NEVER REPEAT OR PARAPHRASE ANY OF THESE):
{context.get("questions_asked", context.get("question_history", []))}

Questions Skipped by Candidate:
{context.get("skipped_questions", [])}

Rules:

1. Use the candidate's actual information.

2. Do not invent experience.

3. Resume questions must reference the resume.

4. Project questions must reference an actual candidate project.

5. Technical questions must be relevant to the target role.

6. Role-specific questions must relate to the actual job responsibilities.

7. Skill-gap questions should investigate missing skills honestly.

8. Follow-up questions must probe a distinct, novel aspect.

9. NEVER repeat or paraphrase any question from "Questions Already Asked in This Session" or "Questions Skipped by Candidate".

10. If the candidate skipped the previous question, move to a completely different topic or aspect.

11. Difficulty 1 = basic understanding.
12. Difficulty 2 = practical implementation.
13. Difficulty 3 = deeper technical reasoning.
14. Difficulty 4 = design and trade-offs.
15. Difficulty 5 = advanced architecture and production-level reasoning.
16. Keep the question natural enough to be spoken during a live interview.

Return only:

{{
    "question": "...",
    "category": "...",
    "difficulty": 1
}}
"""

    # =====================================================
    # ANSWER ANALYSIS PROMPT
    # =====================================================

    def _build_answer_analysis_prompt(
        self,
        context: Dict,
    ) -> str:

        return f"""
You are an expert technical interviewer.

Evaluate the candidate answer objectively.

Target Role:
{context.get("role", "")}

Category:
{context.get("category", "")}

Question:
{context.get("question", "")}

Candidate Answer:
{context.get("answer", "")}

Candidate Skills:
{context.get("candidate_skills", [])}

Expected Topics:
{context.get("expected_topics", [])}

Known Skill Gaps:
{context.get("skill_gaps", [])}

Evaluate:

RELEVANCE
Does the answer directly address the question?

COMPLETENESS
Does the answer provide enough explanation?

TECHNICAL DEPTH
Does the candidate demonstrate actual
technical understanding?

Do not give high technical depth simply
because technology names are mentioned.

Look for implementation details, reasoning,
architecture, algorithms, decisions,
trade-offs, challenges, debugging,
performance and concrete examples.

CLARITY
Is the answer understandable and structured?

FOLLOW-UP
Should the interviewer ask another question?

Use:

probe_deeper
clarify
ask_for_example
challenge
continue

Do not reward keyword stuffing.

Do not invent information.

Return only:

{{
    "relevance": "high|medium|low|very_low",
    "completeness": "high|medium|low|very_low",
    "technical_depth": "high|medium|low|very_low",
    "clarity": "good|moderate|needs_improvement",
    "needs_follow_up": true,
    "suggested_action": "probe_deeper",
    "reason": "short explanation"
}}
"""

    # =====================================================
    # HEALTH CHECK
    # =====================================================

    def health_check(self) -> bool:

        try:

            response = (
                self._generate_with_retry(
                    model=self.model,
                    contents=(
                        "Respond with exactly: OK"
                    ),
                    config=self._config(
                        max_output_tokens=20,
                        thinking_level="low",
                    ),
                )
            )

            return bool(
                response.text
            )

        except Exception:

            return False