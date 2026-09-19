from typing import Any, Dict, List, Optional

from .strategy import (
    build_interview_strategy,
    build_question_context,
    select_next_category,
)
from .conversation_state import ConversationState
from .question_generator import generate_next_question
from .answer_analyzer import analyze_answer
from .decision_engine import process_answer as process_answer_decision
from .question_validator import QuestionValidator
from .category_scheduler import AdaptiveCategoryScheduler


class InterviewOrchestrator:
    """
    Main controller for the adaptive mock interview.

    Responsibilities:
    - Manage candidate and job profiles
    - Manage interview strategy
    - Maintain conversation state
    - Generate questions
    - Analyze candidate answers
    - Integrate optional LLM evaluation
    - Make adaptive interview decisions
    - Progress through interview categories
    """

    def __init__(
        self,
        candidate_profile: Any = None,
        job_profile: Any = None,
        match_report: Optional[Dict[str, Any]] = None,
        strategy: Optional[Dict[str, Any]] = None,
        use_llm: bool = False,
        llm_adapter: Any = None,
        candidate: Any = None,
        job: Any = None,
        max_questions: int = 15,
    ):
        """
        Initialize the interview orchestrator.

        Supports:

            candidate_profile
            job_profile
            match_report
            strategy
            use_llm
            llm_adapter

        Also supports backward-compatible:

            candidate
            job
        """

        # =========================================================
        # PROFILE ALIASES
        # =========================================================

        if candidate_profile is None:
            candidate_profile = candidate

        if job_profile is None:
            job_profile = job

        self.candidate_profile = candidate_profile
        self.job_profile = job_profile

        # Backward-compatible names
        self.candidate = candidate_profile
        self.job = job_profile

        self.match_report = match_report or {}

        self.use_llm = use_llm
        self.llm_adapter = llm_adapter

        # =========================================================
        # CONVERT PROFILES TO DICTIONARIES
        # =========================================================

        candidate_dict = self._to_dict(
            candidate_profile
        )

        job_dict = self._to_dict(
            job_profile
        )

        # =========================================================
        # STRATEGY
        # =========================================================

        if strategy is not None:
            self.strategy = strategy
        else:
            self.strategy = build_interview_strategy(
                candidate=candidate_dict,
                job=job_dict,
                match_report=self.match_report,
            )

        # =========================================================
        # CANDIDATE NAME
        # =========================================================

        candidate_name = self._get_value(
            candidate_profile,
            "name",
            candidate_dict.get(
                "name",
                "Candidate",
            ),
        )

        # =========================================================
        # JOB ROLE
        # =========================================================

        role = self._get_value(
            job_profile,
            "title",
            job_dict.get(
                "title",
                "Interview",
            ),
        )

        if not role or role == "Interview":
            role = self._get_value(
                job_profile,
                "role",
                role,
            )

        # =========================================================
        # CONVERSATION STATE & SCHEDULER
        # =========================================================

        self.max_questions = max(5, int(max_questions))

        self.state = ConversationState(
            candidate_name=candidate_name,
            role=role,
            max_questions=self.max_questions,
            max_consecutive_followups=1,
        )

        self.scheduler = AdaptiveCategoryScheduler(
            strategy=self.strategy,
            candidate=candidate_dict,
            job=job_dict,
            match_report=self.match_report,
            max_questions=self.max_questions,
            max_consecutive_followups=1,
        )

        # =========================================================
        # QUESTION VALIDATOR (CENTRALIZED DEDUPLICATION)
        # =========================================================

        self.validator = QuestionValidator()
        self._register_validator_entities(candidate_dict, job_dict)

        # =========================================================
        # LLM INITIALIZATION
        # =========================================================

        if (
            self.use_llm
            and self.llm_adapter is None
        ):
            self._initialize_llm()

    def _register_validator_entities(
        self,
        candidate_dict: Dict[str, Any],
        job_dict: Dict[str, Any],
    ):
        """Register known candidate projects, skills, and tools into validator."""
        projects = []
        for p in candidate_dict.get("projects", []):
            if isinstance(p, dict):
                p_name = p.get("title") or p.get("name") or ""
                if p_name:
                    projects.append(p_name)
            elif isinstance(p, str):
                projects.append(p)

        skills = []
        raw_skills = candidate_dict.get("skills", [])
        if isinstance(raw_skills, dict):
            for s_list in raw_skills.values():
                if isinstance(s_list, list):
                    skills.extend([str(s) for s in s_list])
        elif isinstance(raw_skills, list):
            skills.extend([str(s) for s in raw_skills])

        job_req = job_dict.get("required_skills", [])
        if isinstance(job_req, list):
            skills.extend([str(s) for s in job_req])

        self.validator.register_entities(projects=projects, skills=skills)

    # =============================================================
    # LLM INITIALIZATION
    # =============================================================

    def _initialize_llm(self):
        """
        Initialize the existing InterviewLLMAdapter.
        """

        try:

            from ..llm.interview_adapter import (
                InterviewLLMAdapter
            )

            self.llm_adapter = InterviewLLMAdapter()

            print(
                "LLM adapter initialized successfully."
            )

        except Exception as exc:

            print(
                f"LLM adapter initialization failed: {exc}"
            )

            self.llm_adapter = None

    # =============================================================
    # UTILITY METHODS
    # =============================================================

    @staticmethod
    def _to_dict(
        value: Any,
    ) -> Dict[str, Any]:
        """
        Convert a dictionary, Pydantic model, or normal Python
        object into a dictionary.
        """

        if value is None:
            return {}

        if isinstance(value, dict):
            return value

        # Pydantic v2
        if hasattr(value, "model_dump"):
            try:
                return value.model_dump()
            except Exception:
                pass

        # Pydantic v1
        if hasattr(value, "dict"):
            try:
                return value.dict()
            except Exception:
                pass

        # Normal Python object
        if hasattr(value, "__dict__"):
            try:
                return vars(value)
            except Exception:
                pass

        return {}

    @staticmethod
    def _get_value(
        obj: Any,
        key: str,
        default: Any = None,
    ) -> Any:
        """
        Safely retrieve an attribute from a dictionary
        or normal object.
        """

        if obj is None:
            return default

        if isinstance(obj, dict):
            return obj.get(
                key,
                default,
            )

        return getattr(
            obj,
            key,
            default,
        )

    # =============================================================
    # STATE GETTERS
    # =============================================================

    def get_current_question(self) -> str:
        """
        Return the current interview question.
        """

        return self.state.current_question

    def get_current_category(self) -> str:
        """
        Return the current interview category.
        """

        return self.state.current_category

    def get_active_category(self) -> str:
        """
        Return the active interview category.

        During a follow-up, this remains the original category.
        """

        return self.state.active_category

    def is_active(self) -> bool:
        """
        Return whether the interview is active.
        """

        return self.state.is_active

    # =============================================================
    # QUESTION CONTEXT
    # =============================================================

    def _build_question_context(
        self,
        category: str,
    ) -> Dict[str, Any]:
        """
        Build complete context for question generation.
        """

        context = build_question_context(
            self.strategy,
            category,
        )

        # =========================================================
        # CONVERSATION STATE
        # =========================================================

        context["candidate_name"] = (
            self.state.candidate_name
        )

        context["role"] = (
            self.state.role
        )

        context["current_category"] = (
            self.state.current_category
        )

        context["active_category"] = (
            self.state.active_category
        )

        context["current_difficulty"] = (
            self.state.current_difficulty
        )

        context["question_number"] = (
            self.state.question_number
        )

        context["questions_asked"] = list(
            self.state.questions_asked
        )

        context["skipped_questions"] = list(
            getattr(self.state, "skipped_questions", [])
        )

        context["answers_received"] = list(
            self.state.answers_received
        )

        context["conversation_history"] = list(
            self.state.conversation_history
        )

        context["completed_categories"] = list(
            self.state.completed_categories
        )

        context["topics_covered"] = list(
            self.state.topics_covered
        )

        context["topics_remaining"] = list(
            self.state.topics_remaining
        )

        context["followups_asked"] = (
            self.state.followups_asked
        )

        context["max_followups_per_topic"] = (
            self.state.max_followups_per_topic
        )

        context["last_answer_assessment"] = (
            self.state.last_answer_assessment
        )

        # =========================================================
        # PROFILE INFORMATION
        # =========================================================

        context["candidate"] = self._to_dict(
            self.candidate_profile
        )

        context["job"] = self._to_dict(
            self.job_profile
        )

        context["match_report"] = (
            self.match_report
        )

        # Grounding: Inject specific target (matched skill, skill gap, project, responsibility)
        if hasattr(self, "scheduler"):
            target_info = self.scheduler.get_target_for_category(category)
            for k, v in target_info.items():
                if v:
                    context[k] = v

        return context

    # =============================================================
    # QUESTION GENERATION
    # =============================================================

    def generate_question(
        self,
        category: Optional[str] = None,
        previous_question: str = "",
        previous_answer: str = "",
        action: str = "new_topic",
    ) -> Dict[str, Any]:
        """
        Generate the next interview question.

        Enforces centralized question deduplication via QuestionValidator:
        1. LLM generation is attempted first when enabled.
        2. If LLM question is duplicate/empty, fallback to template generation.
        3. If template question is duplicate/exhausted, advance to next category.
        4. Valid questions are recorded in QuestionValidator and ConversationState.
        """

        if category is None:
            category = (
                self.state.current_category
            )

        # Budget exhaustion check
        if not self.state.is_active or self.state.question_number >= self.max_questions:
            self.state.end_session()
            return {
                "question": "",
                "category": "closing",
                "generation_method": "completed",
                "action": "complete",
                "exhausted": True,
            }

        # Closing reservation: if only 1 question remains in budget, force closing
        if hasattr(self, "scheduler") and self.scheduler.remaining_budget() <= 1:
            category = "closing"

        current_cat = category
        max_category_hops = 10
        hops = 0

        while hops < max_category_hops:
            hops += 1
            context = self._build_question_context(current_cat)
            eff_action = "follow_up" if current_cat == "follow_up" else action

            # =========================================================
            # LLM QUESTION GENERATION
            # =========================================================

            if (
                self.use_llm
                and self.llm_adapter is not None
            ):
                try:
                    result = (
                        self.llm_adapter.generate_question(
                            context=context,
                            category=current_cat,
                            previous_question=previous_question,
                            previous_answer=previous_answer,
                        )
                    )

                    if (
                        isinstance(result, dict)
                        and result.get("question")
                    ):
                        candidate_q = result.get("question", "").strip()
                        if candidate_q and not self.validator.is_duplicate(candidate_q, category=current_cat):
                            generated_category = (
                                result.get(
                                    "category",
                                    current_cat,
                                )
                            )
                            difficulty = self.state.current_difficulty

                            self.validator.record_question(candidate_q, category=generated_category)
                            self.state.set_question(
                                question=candidate_q,
                                category=generated_category,
                                difficulty=difficulty,
                            )
                            if hasattr(self, "scheduler"):
                                self.scheduler.record_question(
                                    generated_category,
                                    is_followup=(generated_category == "follow_up" or eff_action == "follow_up"),
                                )

                            result.setdefault(
                                "category",
                                generated_category,
                            )
                            result["difficulty"] = difficulty
                            result.setdefault(
                                "generation_method",
                                "llm",
                            )
                            return result
                        else:
                            print(
                                f"[Orchestrator] LLM question rejected by validator (duplicate/empty): '{candidate_q}'. Trying template fallback."
                            )

                except Exception as exc:
                    print(
                        f"LLM question generation failed: {exc}"
                    )
                    print(
                        "Falling back to template generation."
                    )

            # =========================================================
            # TEMPLATE GENERATION
            # =========================================================

            decision = {
                "action": eff_action,
                "target": None,
            }

            try:
                result = generate_next_question(
                    context=context,
                    decision=decision,
                    previous_question=previous_question,
                    previous_answer=previous_answer,
                )
            except TypeError:
                result = generate_next_question(
                    context,
                    decision,
                    previous_question,
                    previous_answer,
                )

            if not isinstance(result, dict):
                result = {
                    "question": str(result),
                    "category": current_cat,
                    "action": eff_action,
                    "generation_method": "template",
                }

            candidate_q = result.get("question", "").strip()
            is_exhausted = result.get("exhausted", False) or not candidate_q

            if not is_exhausted and not self.validator.is_duplicate(candidate_q, category=current_cat):
                generated_category = (
                    result.get(
                        "category",
                        current_cat,
                    )
                )
                difficulty = (
                    result.get(
                        "difficulty",
                        self.state.current_difficulty,
                    )
                )

                self.validator.record_question(candidate_q, category=generated_category)
                self.state.set_question(
                    question=candidate_q,
                    category=generated_category,
                    difficulty=difficulty,
                )
                if hasattr(self, "scheduler"):
                    self.scheduler.record_question(
                        generated_category,
                        is_followup=(generated_category == "follow_up" or eff_action == "follow_up"),
                    )

                result.setdefault(
                    "category",
                    generated_category,
                )
                result.setdefault(
                    "difficulty",
                    difficulty,
                )
                result.setdefault(
                    "generation_method",
                    "template",
                )
                return result

            # =========================================================
            # CATEGORY EXHAUSTED OR DUPLICATE -> ADVANCE CATEGORY
            # =========================================================

            print(
                f"[Orchestrator] Category '{current_cat}' exhausted or duplicate. Advancing to next category."
            )
            self.state.complete_current_category()

            if hasattr(self, "scheduler"):
                next_cat = self.scheduler.select_next_category(
                    current_category=current_cat,
                    pending_action="continue",
                    current_difficulty=self.state.current_difficulty,
                )
            else:
                next_cat = select_next_category(
                    self.strategy,
                    self.state.completed_categories,
                )

            if (
                next_cat == "closing"
                and "closing" in self.state.completed_categories
            ):
                self.state.end_session()
                return {
                    "question": "",
                    "category": "closing",
                    "generation_method": "completed",
                    "action": "complete",
                    "exhausted": True,
                }

            current_cat = next_cat
            action = "new_topic"

        # End session if max category transitions exceeded
        self.state.end_session()
        return {
            "question": "",
            "category": "closing",
            "generation_method": "completed",
            "action": "complete",
            "exhausted": True,
        }

    # =============================================================
    # SKIP QUESTION
    # =============================================================

    def skip_question(self) -> Dict[str, Any]:
        """
        Handle candidate skipping the current question.

        1. Records the skipped question in state.skipped_questions and validator.
        2. Consumes exactly 1 question slot in ConversationState and Scheduler.
        3. Penalizes difficulty (-1 level if above Level 1).
        4. Terminates immediately if question budget is reached.
        5. Advances category via AdaptiveCategoryScheduler.
        """

        if not self.state.is_active or self.state.is_budget_exhausted():
            self.state.end_session()
            return {
                "success": False,
                "skipped": False,
                "message": "Interview is no longer active.",
                "interview_active": False,
                "interview_complete": True,
                "question": "",
                "next_question": "",
            }

        skipped_q = self.state.current_question
        skipped_cat = self.state.current_category

        if skipped_q:
            self.validator.record_question(skipped_q, category=skipped_cat)

        # Decrease difficulty on skip if above Level 1
        if self.state.current_difficulty > 1:
            self.state.decrease_difficulty()

        self.state.record_skip()
        if hasattr(self, "scheduler"):
            self.scheduler.record_question(skipped_cat, is_skipped=True)

        # Check if question budget has been exhausted
        if self.state.is_budget_exhausted() or (hasattr(self, "scheduler") and self.scheduler.is_budget_exhausted()):
            self.state.end_session()
            return {
                "success": True,
                "skipped": True,
                "skipped_question": skipped_q,
                "category": skipped_cat,
                "next_question": "",
                "next_category": "closing",
                "current_category": self.state.current_category,
                "active_category": self.state.active_category,
                "current_difficulty": self.state.current_difficulty,
                "interview_active": False,
                "interview_complete": True,
                "message": "Interview completed (question budget reached).",
                "assessment": {
                    "quality": "skipped",
                    "score": None,
                    "clarity_level": "skipped",
                    "technical_depth_level": "skipped",
                },
                "decision": {
                    "action": "skip",
                    "complete_category": True,
                    "trigger_followup": False,
                    "next_category": "closing",
                },
                "completed_categories": list(self.state.completed_categories),
                "questions_completed": len(self.state.answers_received),
            }

        # Select next category via scheduler
        if hasattr(self, "scheduler"):
            next_cat = self.scheduler.select_next_category(
                current_category=skipped_cat,
                pending_action="continue",
                current_difficulty=self.state.current_difficulty,
            )
        else:
            next_cat = self.state.current_category

        next_result = self.generate_question(
            category=next_cat,
            previous_question=skipped_q,
            previous_answer=":skip",
            action="new_topic",
        )

        next_q = next_result.get("question", "")
        next_cat_res = next_result.get("category", next_cat)
        is_complete = not next_q or self.state.is_budget_exhausted()
        if is_complete:
            self.state.end_session()

        return {
            "success": True,
            "skipped": True,
            "skipped_question": skipped_q,
            "category": skipped_cat,
            "next_question": next_q,
            "next_category": next_cat_res,
            "next_active_category": self.state.active_category,
            "current_category": self.state.current_category,
            "active_category": self.state.active_category,
            "current_difficulty": self.state.current_difficulty,
            "interview_active": self.state.is_active,
            "interview_complete": not self.state.is_active,
            "message": "Question skipped. Moving to next question." if not is_complete else "Interview completed.",
            "assessment": {
                "quality": "skipped",
                "score": None,
                "clarity_level": "skipped",
                "technical_depth_level": "skipped",
            },
            "decision": {
                "action": "skip",
                "complete_category": True,
                "trigger_followup": False,
                "next_category": next_cat_res,
            },
            "completed_categories": list(self.state.completed_categories),
            "questions_completed": len(self.state.answers_received),
        }

    # =============================================================
    # START INTERVIEW
    # =============================================================

    def start_interview(
        self,
    ) -> Dict[str, Any]:
        """
        Start the interview and generate the first question.
        """

        if not self.state.is_active or self.state.is_budget_exhausted():
            return {
                "success": False,
                "message": (
                    "Interview has already ended."
                ),
                "interview_active": False,
                "interview_complete": True,
                "question": "",
                "category": (
                    self.state.current_category
                ),
            }

        if hasattr(self, "scheduler"):
            category = self.scheduler.select_next_category(current_category="introduction")
        else:
            category = select_next_category(
                self.strategy,
                self.state.completed_categories,
            )

        result = self.generate_question(
            category=category
        )

        return {
            "success": True,

            "question": result.get(
                "question",
                self.state.current_question,
            ),

            "category": result.get(
                "category",
                self.state.current_category,
            ),

            "active_category": (
                self.state.active_category
            ),

            "difficulty": result.get(
                "difficulty",
                self.state.current_difficulty,
            ),

            "generation_method": (
                result.get(
                    "generation_method",
                    "template",
                )
            ),
        }

    # =============================================================
    # START ALIAS
    # =============================================================

    def start(
        self,
    ) -> Dict[str, Any]:
        """
        Compatibility alias.

        The test suite calls:

            orchestrator.start()
        """

        return self.start_interview()

    # =============================================================
    # RULE-BASED ANSWER ANALYSIS
    # =============================================================

    def _analyze_answer_rule_based(
        self,
        question: str,
        answer: str,
    ) -> Dict[str, Any]:
        """
        Perform rule-based answer analysis.

        IMPORTANT:
        analyze_answer() currently accepts only:
            question
            answer

        Therefore context is NOT passed.
        """

        return analyze_answer(
            question=question,
            answer=answer,
        )

    # =============================================================
    # LLM ANSWER ANALYSIS
    # =============================================================

    def _analyze_answer_llm(
        self,
        question: str,
        answer: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Perform LLM-based answer analysis.
        """

        if (
            not self.use_llm
            or self.llm_adapter is None
        ):
            return None

        try:

            context = self._build_question_context(
                self.state.active_category
            )

            result = (
                self.llm_adapter.analyze_answer(
                    question=question,
                    answer=answer,
                    context=context,
                )
            )

            if not isinstance(
                result,
                dict,
            ):
                return None

            if isinstance(
                result.get("llm_based"),
                dict,
            ):

                return result[
                    "llm_based"
                ]

            return result

        except Exception as exc:

            print(
                f"LLM answer analysis failed: {exc}"
            )

            return None

    # =============================================================
    # SCORE CONVERSION
    # =============================================================

    @staticmethod
    def _score_from_level(
        value: Any,
    ) -> Optional[float]:
        """
        Convert qualitative LLM evaluation levels
        into numerical values.
        """

        if value is None:
            return None

        value = str(
            value
        ).strip().lower()

        mapping = {
            "very_low": 0.20,
            "low": 0.35,
            "medium": 0.60,
            "moderate": 0.60,
            "good": 0.75,
            "high": 0.85,
            "very_high": 0.95,
            "excellent": 0.95,
        }

        return mapping.get(
            value
        )

    # =============================================================
    # COMBINE ASSESSMENTS
    # =============================================================

    def _combine_assessments(
        self,
        rule_based: Dict[str, Any],
        llm_based: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Combine rule-based and LLM assessments.

        Rule-based = 40%
        LLM        = 60%
        """

        if not llm_based:

            combined = dict(
                rule_based
            )

            combined[
                "assessment_method"
            ] = "rule_based"

            return combined

        # =========================================================
        # RULE SCORE
        # =========================================================

        rule_score = rule_based.get(
            "score",
            0,
        )

        try:

            rule_score = float(
                rule_score
            )

        except (
            TypeError,
            ValueError,
        ):

            rule_score = 0.0

        # =========================================================
        # LLM DIMENSIONS
        # =========================================================

        llm_dimensions = [

            self._score_from_level(
                llm_based.get(
                    "relevance"
                )
            ),

            self._score_from_level(
                llm_based.get(
                    "completeness"
                )
            ),

            self._score_from_level(
                llm_based.get(
                    "technical_depth"
                )
            ),

            self._score_from_level(
                llm_based.get(
                    "clarity"
                )
            ),
        ]

        valid_dimensions = [
            score
            for score in llm_dimensions
            if score is not None
        ]

        llm_score = None

        if valid_dimensions:

            llm_score = (
                sum(valid_dimensions)
                / len(valid_dimensions)
            ) * 100.0

        # =========================================================
        # FINAL SCORE
        # =========================================================

        if llm_score is not None:

            final_score = (
                rule_score * 0.40
                + llm_score * 0.60
            )

            assessment_method = "hybrid"

        else:

            final_score = rule_score

            assessment_method = (
                "rule_based_fallback"
            )

        # =========================================================
        # QUALITY
        # =========================================================

        if final_score >= 75:

            quality = "strong"

        elif final_score >= 50:

            quality = "moderate"

        else:

            quality = "weak"

        combined = dict(
            rule_based
        )

        combined.update(
            {
                "score": round(
                    final_score,
                    2,
                ),

                "quality": quality,

                "assessment_method": (
                    assessment_method
                ),

                "rule_based_score": round(
                    rule_score,
                    2,
                ),

                "llm_score": (
                    round(
                        llm_score,
                        2,
                    )
                    if llm_score is not None
                    else None
                ),

                "llm_analysis": (
                    llm_based
                ),
            }
        )

        if "overall_quality" in combined and isinstance(combined["overall_quality"], dict):
            combined["overall_quality"] = dict(combined["overall_quality"])
            combined["overall_quality"]["level"] = quality
            combined["overall_quality"]["percentage"] = round(final_score, 2)

        # =========================================================
        # LLM FOLLOW-UP INFORMATION
        # =========================================================

        if (
            llm_based.get(
                "needs_follow_up"
            )
            is not None
        ):

            combined[
                "llm_needs_follow_up"
            ] = llm_based.get(
                "needs_follow_up"
            )

        if llm_based.get(
            "suggested_action"
        ):

            combined[
                "llm_suggested_action"
            ] = llm_based.get(
                "suggested_action"
            )

        if llm_based.get(
            "reason"
        ):

            combined[
                "llm_reason"
            ] = llm_based.get(
                "reason"
            )

        return combined

    # =============================================================
    # PROCESS ANSWER
    # =============================================================

    def process_answer(
        self,
        answer: str,
    ) -> Dict[str, Any]:
        """
        Process one candidate answer and generate the next
        interview question.
        """

        if not self.state.is_active:

            return {
                "success": False,
                "message": (
                    "Interview is no longer active."
                ),
                "interview_active": False,
                "question": "",
            }

        question = (
            self.state.current_question
        )

        if not question:

            return {
                "success": False,
                "message": (
                    "There is no active question."
                ),
                "interview_active": (
                    self.state.is_active
                ),
                "question": "",
            }

        # Check for explicit skip command
        if str(answer).strip().lower() in (":skip", "skip", "/skip"):
            return self.skip_question()

        # =========================================================
        # RECORD ANSWER
        # =========================================================

        self.state.record_answer(
            answer
        )

        # =========================================================
        # RULE-BASED ANALYSIS
        # =========================================================

        rule_based_assessment = (
            self._analyze_answer_rule_based(
                question=question,
                answer=answer,
            )
        )

        # =========================================================
        # LLM ANALYSIS
        # =========================================================

        llm_based_assessment = (
            self._analyze_answer_llm(
                question=question,
                answer=answer,
            )
        )

        # =========================================================
        # COMBINE ASSESSMENTS
        # =========================================================

        assessment = (
            self._combine_assessments(
                rule_based=rule_based_assessment,
                llm_based=llm_based_assessment,
            )
        )

        # =========================================================
        # STORE ASSESSMENT
        # =========================================================

        self.state.set_answer_assessment(
            assessment
        )

        # =========================================================
        # DECISION ENGINE
        # =========================================================

        decision = process_answer_decision(
            assessment=assessment,
            state=self.state,
        )

        if self.state.conversation_history:
            self.state.conversation_history[-1]["assessment"] = assessment
            self.state.conversation_history[-1]["decision"] = decision

        action = decision.get(
            "action",
            "new_topic",
        )


        # =========================================================
        # CHECK BUDGET EXHAUSTION
        # =========================================================

        if self.state.is_budget_exhausted() or (hasattr(self, "scheduler") and self.scheduler.is_budget_exhausted()):
            self.state.end_session()
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "category": self.state.current_category,
                "active_category": self.state.active_category,
                "assessment": assessment,
                "rule_based_assessment": rule_based_assessment,
                "llm_assessment": llm_based_assessment,
                "decision": decision,
                "action": action,
                "interview_active": False,
                "interview_complete": True,
                "next_question": "",
                "message": "Interview completed (question budget reached).",
            }

        # =========================================================
        # FIND NEXT CATEGORY VIA SCHEDULER
        # =========================================================

        if hasattr(self, "scheduler"):
            next_category = self.scheduler.select_next_category(
                current_category=self.state.current_category,
                pending_action=action,
                last_assessment=assessment,
                current_difficulty=self.state.current_difficulty,
                completed_categories=self.state.completed_categories,
            )
        else:
            if action in ("follow_up", "clarify"):
                next_category = "follow_up"
            else:
                next_category = select_next_category(
                    self.strategy,
                    self.state.completed_categories,
                )

        # =========================================================
        # CHECK INTERVIEW COMPLETION
        # =========================================================

        if (
            (
                next_category == "closing"
                and "closing" in self.state.completed_categories
            )
            or not self.state.is_active
        ):
            self.state.end_session()
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "category": "closing",
                "active_category": (
                    self.state.active_category
                ),
                "assessment": assessment,
                "rule_based_assessment": (
                    rule_based_assessment
                ),
                "llm_assessment": (
                    llm_based_assessment
                ),
                "decision": decision,
                "action": action,
                "interview_active": False,
                "interview_complete": True,
                "next_question": "",
                "message": (
                    "Interview completed."
                ),
            }

        # =========================================================
        # GENERATE NEXT QUESTION
        # =========================================================

        next_question_result = (
            self.generate_question(
                category=next_category,
                previous_question=question,
                previous_answer=answer,
                action=action,
            )
        )

        next_question = (
            next_question_result.get(
                "question",
                "",
            )
        )

        next_category = (
            next_question_result.get(
                "category",
                next_category,
            )
        )

        is_complete = not next_question or self.state.is_budget_exhausted()
        if is_complete:
            self.state.end_session()

        # =========================================================
        # RETURN RESULT
        # =========================================================

        return {
            "success": True,
            "question": question,
            "answer": answer,
            "assessment": assessment,
            "rule_based_assessment": rule_based_assessment,
            "llm_assessment": llm_based_assessment,
            "decision": decision,
            "action": action,
            "next_question": next_question,
            "next_category": next_category,
            "next_active_category": self.state.active_category,
            "next_difficulty": self.state.current_difficulty,
            "generation_method": next_question_result.get("generation_method", "template"),
            "current_category": self.state.current_category,
            "active_category": self.state.active_category,
            "question_number": self.state.question_number,
            "interview_active": self.state.is_active,
            "interview_complete": not self.state.is_active,
            "completed_categories": list(self.state.completed_categories),
            "topics_covered": list(self.state.topics_covered),
        }

    # =============================================================
    # ANSWER ALIAS
    # =============================================================

    def answer(
        self,
        answer: str,
    ) -> Dict[str, Any]:
        """
        Convenience alias for process_answer().
        """

        return self.process_answer(
            answer
        )

    # =============================================================
    # END INTERVIEW
    # =============================================================

    def end_interview(
        self,
    ) -> Dict[str, Any]:
        """
        Manually end the interview.
        """

        self.state.end_session()

        return {
            "success": True,
            "message": "Interview ended.",
            "interview_active": False,
            "state": self.state.to_dict(),
        }

    # =============================================================
    # GET STATE
    # =============================================================

    def get_state(
        self,
    ) -> Dict[str, Any]:
        """
        Return serialized interview state.
        """

        return self.state.to_dict()

    # =============================================================
    # GET STRATEGY
    # =============================================================

    def get_strategy(
        self,
    ) -> Dict[str, Any]:
        """
        Return interview strategy.
        """

        return self.strategy