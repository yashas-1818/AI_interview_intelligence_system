"""
AI POWERED INTERVIEW INTELLIGENCE SYSTEM
Adaptive Category Scheduler

Responsible for:
- Enforcing a finite question budget (MAX_QUESTIONS)
- Guaranteeing coverage of required baseline interview categories
- Tracking category quotas as minimum/maximum constraints
- Probing matched candidate skills (e.g. Python, SQL) under 'technical'
- Probing required skill gaps (e.g. FastAPI, MySQL) under 'skill_gap'
- Enforcing follow-up bounding (maximum 1 consecutive follow-up)
- Reserving the final available slot for 'closing'
- Dynamically selecting next categories based on performance and remaining budget
"""

from typing import Any, Dict, List, Optional, Set


class AdaptiveCategoryScheduler:
    """
    Adaptive Category Scheduler for mock interview sessions.

    Maintains category minimum/maximum quotas, ensures all core interview
    phases are visited within the question budget, and adaptively sequences
    questions based on candidate performance.
    """

    # Baseline required categories that must be covered
    BASELINE_REQUIRED_CATEGORIES = [
        "introduction",
        "resume",
        "project",
        "technical",
        "role_specific",
        "skill_gap",
        "behavioral",
        "situational",
        "closing",
    ]

    def __init__(
        self,
        strategy: Optional[Dict[str, Any]] = None,
        candidate: Optional[Dict[str, Any]] = None,
        job: Optional[Dict[str, Any]] = None,
        match_report: Optional[Dict[str, Any]] = None,
        max_questions: int = 15,
        max_consecutive_followups: int = 1,
    ):
        self.strategy = strategy or {}
        self.candidate = candidate or {}
        self.job = job or {}
        self.match_report = match_report or {}
        self.max_questions = max(5, max_questions)
        self.max_consecutive_followups = max_consecutive_followups

        # Category quotas (min_required, max_allowed) scaled with question budget
        scale = max(1, self.max_questions // 15)
        self.category_quotas: Dict[str, Dict[str, int]] = {
            "introduction": {"min": 1, "max": max(1, 1 * scale)},
            "resume": {"min": 1, "max": max(2, 2 * scale)},
            "project": {"min": 1, "max": max(2, 2 * scale)},
            "technical": {"min": 1, "max": max(3, 4 * scale)},
            "role_specific": {"min": 1, "max": max(2, 3 * scale)},
            "skill_gap": {"min": 1, "max": max(2, 3 * scale)},
            "behavioral": {"min": 1, "max": max(2, 2 * scale)},
            "situational": {"min": 1, "max": max(2, 2 * scale)},
            "closing": {"min": 1, "max": 1},
        }

        # Tracking state
        self.category_counts: Dict[str, int] = {cat: 0 for cat in self.category_quotas}
        self.total_questions_consumed: int = 0
        self.consecutive_followups: int = 0
        self.probed_matched_skills: List[str] = []
        self.probed_skill_gaps: List[str] = []
        self.probed_projects: List[str] = []
        self.probed_responsibilities: List[str] = []

        # Extract available topics from profiles and match report
        self.matched_skills = self._extract_matched_skills()
        self.required_skill_gaps = self._extract_required_skill_gaps()
        self.preferred_skill_gaps = self._extract_preferred_skill_gaps()
        self.project_topics = self._extract_projects()
        self.role_topics = self._extract_role_topics()

    # =========================================================================
    # EXTRACTION HELPERS
    # =========================================================================

    def _extract_matched_skills(self) -> List[str]:
        req = self.match_report.get("required_skills", {})
        matched = req.get("matched", [])
        if not matched and self.strategy:
            matched = self.strategy.get("candidate_strengths", [])
        if not matched and self.candidate:
            raw = self.candidate.get("skills", [])
            if isinstance(raw, list):
                matched = [str(s).lower() for s in raw]
            elif isinstance(raw, dict):
                for v in raw.values():
                    if isinstance(v, list):
                        matched.extend([str(s).lower() for s in v])
        return [str(s).strip() for s in matched if str(s).strip()]

    def _extract_required_skill_gaps(self) -> List[str]:
        req = self.match_report.get("required_skills", {})
        missing = req.get("missing", [])
        if not missing and self.strategy:
            missing = self.strategy.get("skill_gaps", [])
        return [str(s).strip() for s in missing if str(s).strip()]

    def _extract_preferred_skill_gaps(self) -> List[str]:
        pref = self.match_report.get("preferred_skills", {})
        missing = pref.get("missing", [])
        return [str(s).strip() for s in missing if str(s).strip()]

    def _extract_projects(self) -> List[str]:
        projects = []
        raw = self.candidate.get("projects", [])
        for p in raw:
            if isinstance(p, dict):
                title = p.get("title") or p.get("name") or ""
                if title:
                    projects.append(title.strip())
            elif isinstance(p, str) and p.strip():
                projects.append(p.strip())
        if not projects and self.strategy:
            projects = self.strategy.get("project_topics", [])
        return projects

    def _extract_role_topics(self) -> List[str]:
        resps = []
        raw = self.job.get("responsibilities", [])
        for r in raw:
            if isinstance(r, str) and r.strip():
                resps.append(r.strip())
        if not resps and self.strategy:
            resps = self.strategy.get("role_topics", [])
        return resps

    # =========================================================================
    # BUDGET & FOLLOW-UP QUERIES
    # =========================================================================

    def remaining_budget(self) -> int:
        """Returns the number of remaining question slots in the budget."""
        return max(0, self.max_questions - self.total_questions_consumed)

    def is_budget_exhausted(self) -> bool:
        """Returns True if all question slots have been consumed."""
        return self.total_questions_consumed >= self.max_questions

    def can_ask_followup(self) -> bool:
        """
        Follow-up allowed ONLY if:
        1. Consecutive follow-up count is strictly less than max_consecutive_followups (default 1).
        2. Remaining budget is > 1 (closing must always have a reserved slot).
        """
        return (
            self.consecutive_followups < self.max_consecutive_followups
            and self.remaining_budget() > 1
        )

    def record_question(
        self,
        category: str,
        is_followup: bool = False,
        is_skipped: bool = False,
    ) -> None:
        """
        Record that a question was asked (or skipped).
        Every question consumes exactly one slot in the budget.
        """
        self.total_questions_consumed += 1

        if is_followup or category == "follow_up":
            self.consecutive_followups += 1
        else:
            self.consecutive_followups = 0
            if category in self.category_counts:
                self.category_counts[category] += 1

    def reset_consecutive_followups(self) -> None:
        """Reset consecutive follow-up counter."""
        self.consecutive_followups = 0

    # =========================================================================
    # ADAPTIVE CATEGORY SELECTION
    # =========================================================================

    def get_unvisited_required_categories(
        self,
        completed_categories: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Return the list of mandatory baseline categories that have not yet
        met their minimum quota constraint or have not been completed.
        """
        completed = set(completed_categories or [])
        unvisited = []
        for cat in [
            "introduction",
            "resume",
            "project",
            "technical",
            "role_specific",
            "skill_gap",
            "behavioral",
            "situational",
        ]:
            needs_probe = (cat not in completed) or (
                self.category_counts.get(cat, 0)
                < self.category_quotas.get(cat, {}).get("min", 1)
            )
            under_max = (
                self.category_counts.get(cat, 0)
                < self.category_quotas.get(cat, {}).get("max", 2)
            )
            if needs_probe and under_max:
                unvisited.append(cat)

        # Closing must be visited if not done yet
        if "closing" not in completed and self.category_counts.get("closing", 0) < 1:
            unvisited.append("closing")

        return unvisited

    def select_next_category(
        self,
        current_category: str,
        pending_action: str = "continue",
        last_assessment: Optional[Dict[str, Any]] = None,
        current_difficulty: int = 1,
        completed_categories: Optional[List[str]] = None,
    ) -> str:
        """
        Dynamically determine the next category to visit within budget.

        Rules:
        1. If budget has 1 slot left -> MUST force 'closing'.
        2. If budget exhausted -> return 'closing' or complete.
        3. If pending_action is 'follow_up' and can_ask_followup() -> return 'follow_up'.
        4. If remaining slots <= len(unvisited_required) -> strictly pick next unvisited required category.
        5. Otherwise adaptively pick based on quotas, performance, and coverage gaps.
        """
        remaining = self.remaining_budget()

        # Rule 1 & 2: Closing reservation
        if remaining <= 1:
            return "closing"

        # Rule 3: Bounded follow-up
        if pending_action in ("follow_up", "clarify") and self.can_ask_followup():
            return "follow_up"

        # If follow-up was just probed, reset consecutive follow-ups
        if current_category == "follow_up" or pending_action not in ("follow_up", "clarify"):
            self.reset_consecutive_followups()

        unvisited_required = self.get_unvisited_required_categories(
            completed_categories=completed_categories
        )
        # Exclude closing from immediate unvisited list if remaining > 1
        unvisited_non_closing = [c for c in unvisited_required if c != "closing"]

        # Rule 4: Tightly constrained budget -> must prioritize uncovered categories
        if remaining <= len(unvisited_non_closing) + 1:
            if unvisited_non_closing:
                return unvisited_non_closing[0]
            return "closing"

        # Rule 5: Standard progression through required categories first
        for cat in unvisited_non_closing:
            return cat

        # If all minimum quotas are satisfied, adaptively choose based on quotas & performance:
        # High difficulty / strong candidate: probe technical deep dive or role-specific
        if current_difficulty >= 3 and self.category_counts.get("technical", 0) < self.category_quotas["technical"]["max"]:
            return "technical"

        # Check for unprobed skill gaps
        if self.required_skill_gaps and len(self.probed_skill_gaps) < len(self.required_skill_gaps):
            if self.category_counts.get("skill_gap", 0) < self.category_quotas["skill_gap"]["max"]:
                return "skill_gap"

        # Check for unprobed matched skills
        if self.matched_skills and len(self.probed_matched_skills) < len(self.matched_skills):
            if self.category_counts.get("technical", 0) < self.category_quotas["technical"]["max"]:
                return "technical"

        # Check role specific
        if self.category_counts.get("role_specific", 0) < self.category_quotas["role_specific"]["max"]:
            return "role_specific"

        # Check situational
        if self.category_counts.get("situational", 0) < self.category_quotas["situational"]["max"]:
            return "situational"

        # Default to closing when categories are well covered
        return "closing"

    # =========================================================================
    # TARGET EXTRACTION (MANDATORY SKILL & GAP PROBING)
    # =========================================================================

    def get_target_for_category(self, category: str) -> Dict[str, Any]:
        """
        Provides specific candidate projects, matched skills, required skill gaps,
        or role responsibilities so questions are deeply grounded in profiles.
        """
        target_info: Dict[str, Any] = {}

        if category == "technical":
            # Mandatory: probe matched skills (e.g. Python, SQL, Git)
            unprobed = [s for s in self.matched_skills if s not in self.probed_matched_skills]
            selected = unprobed[0] if unprobed else (self.matched_skills[0] if self.matched_skills else "Python")
            if selected not in self.probed_matched_skills:
                self.probed_matched_skills.append(selected)
            target_info["skill"] = selected

        elif category == "skill_gap":
            # Mandatory: probe required skill gaps (e.g. FastAPI, MySQL)
            unprobed = [s for s in self.required_skill_gaps if s not in self.probed_skill_gaps]
            if unprobed:
                selected = unprobed[0]
            elif self.preferred_skill_gaps:
                unprobed_pref = [s for s in self.preferred_skill_gaps if s not in self.probed_skill_gaps]
                selected = unprobed_pref[0] if unprobed_pref else self.preferred_skill_gaps[0]
            elif self.required_skill_gaps:
                selected = self.required_skill_gaps[0]
            else:
                selected = "FastAPI"

            if selected not in self.probed_skill_gaps:
                self.probed_skill_gaps.append(selected)
            target_info["skill"] = selected

        elif category in ("project", "resume"):
            # Select key candidate project
            unprobed = [p for p in self.project_topics if p not in self.probed_projects]
            selected = unprobed[0] if unprobed else (self.project_topics[0] if self.project_topics else "your primary project")
            if selected not in self.probed_projects:
                self.probed_projects.append(selected)
            target_info["project"] = selected

        elif category == "role_specific":
            # Select job responsibility
            unprobed = [r for r in self.role_topics if r not in self.probed_responsibilities]
            selected = unprobed[0] if unprobed else (self.role_topics[0] if self.role_topics else "building scalable backend services")
            if selected not in self.probed_responsibilities:
                self.probed_responsibilities.append(selected)
            target_info["responsibility"] = selected

        return target_info
