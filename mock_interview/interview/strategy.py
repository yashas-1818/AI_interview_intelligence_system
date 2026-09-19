from typing import Any, Dict, List

from mock_interview.resume.profile import CandidateProfile
from mock_interview.job.profile import JobProfile


# =========================================================
# QUESTION CATEGORIES
# =========================================================

QUESTION_CATEGORIES = [
    "introduction",
    "resume",
    "project",
    "technical",
    "role_specific",
    "skill_gap",
    "behavioral",
    "situational",
    "follow_up",
    "closing",
]


# =========================================================
# STRATEGY CONFIGURATION
# =========================================================

CATEGORY_DESCRIPTIONS = {
    "introduction":
        "Warm-up and candidate introduction",

    "resume":
        "Questions directly based on the candidate's resume",

    "project":
        "Deep questions about candidate projects",

    "technical":
        "Technical questions related to the candidate's skills",

    "role_specific":
        "Questions based on the target job role and responsibilities",

    "skill_gap":
        "Questions testing required or preferred skills not demonstrated by the candidate",

    "behavioral":
        "Questions about communication, teamwork, leadership, challenges and decision-making",

    "situational":
        "Hypothetical workplace and engineering situations",

    "follow_up":
        "Adaptive questions based on the candidate's previous answer",

    "closing":
        "Final interview and candidate questions",
}


# =========================================================
# BUILD CANDIDATE SKILL SET
# =========================================================

def get_candidate_skills(
    candidate: Any
) -> List[str]:
    """
    Flatten candidate skills into one list.
    Supports both CandidateProfile objects and dictionary representations.
    """

    skills = []
    if candidate is None:
        return skills

    cand_skills = (
        getattr(candidate, "skills", None)
        or (candidate.get("skills") if isinstance(candidate, dict) else None)
        or {}
    )

    if isinstance(cand_skills, dict):
        for category, skill_list in cand_skills.items():
            if isinstance(skill_list, list):
                for skill in skill_list:
                    skill = str(skill).strip()
                    if skill and skill not in skills:
                        skills.append(skill)
    elif isinstance(cand_skills, list):
        for skill in cand_skills:
            skill = str(skill).strip()
            if skill and skill not in skills:
                skills.append(skill)

    cand_projects = (
        getattr(candidate, "projects", None)
        or (candidate.get("projects") if isinstance(candidate, dict) else None)
        or []
    )

    for project in cand_projects:
        techs = (
            getattr(project, "technologies", None)
            or (project.get("technologies") if isinstance(project, dict) else None)
            or []
        )
        for technology in techs:
            technology = str(technology).strip()
            if technology and technology not in skills:
                skills.append(technology)

    return skills


# =========================================================
# BUILD PROJECT TOPICS
# =========================================================

def get_project_topics(
    candidate: Any
) -> List[str]:
    """
    Extract project names that can be used
    for project-focused questions.
    Supports both objects and dicts.
    """

    topics = []
    if candidate is None:
        return topics

    cand_projects = (
        getattr(candidate, "projects", None)
        or (candidate.get("projects") if isinstance(candidate, dict) else None)
        or []
    )

    for project in cand_projects:
        name = (
            getattr(project, "name", None)
            or getattr(project, "title", None)
            or (project.get("title") or project.get("name") if isinstance(project, dict) else str(project))
            or ""
        )
        name = str(name).strip()
        if name and name not in topics:
            topics.append(name)

    return topics


# =========================================================
# BUILD ROLE TOPICS
# =========================================================

def get_role_topics(
    job: Any
) -> List[str]:
    """
    Extract topics from job responsibilities.
    Supports both objects and dicts.
    """

    topics = []
    if job is None:
        return topics

    resps = (
        getattr(job, "responsibilities", None)
        or (job.get("responsibilities") if isinstance(job, dict) else None)
        or []
    )

    for responsibility in resps:
        responsibility = str(responsibility).strip()
        if responsibility and responsibility not in topics:
            topics.append(responsibility)

    return topics


# =========================================================
# BUILD SKILL GAP TOPICS
# =========================================================

def get_skill_gap_topics(
    match_report: Dict
) -> List[str]:
    """
    Extract missing required and preferred skills
    from the candidate-job match report.
    """

    gaps = []

    required = match_report.get(
        "required_skills",
        {}
    )

    preferred = match_report.get(
        "preferred_skills",
        {}
    )

    for skill in required.get(
        "missing",
        []
    ):

        if skill not in gaps:

            gaps.append(skill)

    for skill in preferred.get(
        "missing",
        []
    ):

        if skill not in gaps:

            gaps.append(skill)

    return gaps


# =========================================================
# BUILD INTERVIEW STRATEGY
# =========================================================

def build_interview_strategy(
    candidate: CandidateProfile,
    job: JobProfile,
    match_report: Dict,
) -> Dict:
    """
    Build a deterministic interview strategy.

    This does NOT generate actual questions.

    It decides what areas the AI interviewer
    should cover.
    """

    candidate_skills = get_candidate_skills(
        candidate
    )

    project_topics = get_project_topics(
        candidate
    )

    role_topics = get_role_topics(
        job
    )

    skill_gaps = get_skill_gap_topics(
        match_report
    )

    # -----------------------------------------------------
    # Question distribution
    # -----------------------------------------------------

    categories = []

    # Always start with introduction
    categories.append(
        "introduction"
    )

    # Candidate summary check
    has_summary = False
    if candidate is not None:
        summary = (
            getattr(candidate, "summary", None)
            or (candidate.get("summary") if isinstance(candidate, dict) else None)
        )
        has_summary = bool(summary)

    # Resume-based questions
    if has_summary:
        categories.append(
            "resume"
        )

    # Projects
    if project_topics:

        categories.append(
            "project"
        )

    # Technical
    if candidate_skills:

        categories.append(
            "technical"
        )

    # Role-specific
    if role_topics:

        categories.append(
            "role_specific"
        )

    # Skill gaps
    if skill_gaps:

        categories.append(
            "skill_gap"
        )

    # Behavioral
    categories.append(
        "behavioral"
    )

    # Situational
    categories.append(
        "situational"
    )

    # Follow-ups are available throughout
    categories.append(
        "follow_up"
    )

    # Closing
    categories.append(
        "closing"
    )

    # -----------------------------------------------------
    # Build strategy
    # -----------------------------------------------------

    # Candidate name extraction
    candidate_name = "Candidate"
    if candidate is not None:
        if hasattr(candidate, "candidate") and hasattr(candidate.candidate, "name") and candidate.candidate.name:
            candidate_name = candidate.candidate.name
        elif hasattr(candidate, "name") and candidate.name:
            candidate_name = candidate.name
        elif isinstance(candidate, dict):
            candidate_name = (
                candidate.get("name")
                or candidate.get("candidate", {}).get("name")
                or "Candidate"
            )

    # Role extraction
    role_title = "Interview"
    if job is not None:
        if hasattr(job, "role_title") and job.role_title:
            role_title = job.role_title
        elif hasattr(job, "title") and job.title:
            role_title = job.title
        elif isinstance(job, dict):
            role_title = job.get("role_title") or job.get("title") or "Interview"

    strategy = {

        "role": role_title,

        "candidate_name": candidate_name,

        "categories": categories,

        "candidate_strengths":
            match_report
            .get(
                "required_skills",
                {}
            )
            .get(
                "matched",
                []
            ),

        "skill_gaps":
            skill_gaps,

        "project_topics":
            project_topics,

        "role_topics":
            role_topics,

        "candidate_skills":
            candidate_skills,

        "question_guidance": {
            category:
                CATEGORY_DESCRIPTIONS[
                    category
                ]
            for category in categories
        },
    }

    return strategy


# =========================================================
# SELECT NEXT QUESTION CATEGORY
# =========================================================

def select_next_category(
    strategy: Dict,
    completed_categories: List[str],
) -> str:
    """
    Select the next interview category.

    Follow-up questions can be inserted dynamically,
    so they are handled separately.
    """

    categories = strategy.get(
        "categories",
        []
    )

    for category in categories:

        if category == "follow_up":

            continue

        if category not in completed_categories:

            return category

    return "closing"


# =========================================================
# GENERATE QUESTION CONTEXT
# =========================================================

def build_question_context(
    strategy: Dict,
    category: str,
) -> Dict:
    """
    Build the information that will later be
    passed to an LLM for actual question generation.
    """

    context = {

        "role":
            strategy.get(
                "role",
                ""
            ),

        "candidate_name":
            strategy.get(
                "candidate_name",
                ""
            ),

        "category":
            category,

        "category_description":
            CATEGORY_DESCRIPTIONS.get(
                category,
                ""
            ),

        "candidate_strengths":
            strategy.get(
                "candidate_strengths",
                []
            ),

        "skill_gaps":
            strategy.get(
                "skill_gaps",
                []
            ),

        "project_topics":
            strategy.get(
                "project_topics",
                []
            ),

        "role_topics":
            strategy.get(
                "role_topics",
                []
            ),

        "candidate_skills":
            strategy.get(
                "candidate_skills",
                []
            ),
    }

    return context