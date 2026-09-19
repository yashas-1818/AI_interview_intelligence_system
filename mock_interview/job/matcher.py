import re


from mock_interview.job.profile import JobProfile
from mock_interview.resume.profile import CandidateProfile
from typing import List, Dict




# =========================================================
# SKILL NORMALIZATION
# =========================================================

SKILL_ALIASES = {
    "python": "python",
    "python programming": "python",

    "machine learning": "machine learning",
    "ml": "machine learning",

    "artificial intelligence": "artificial intelligence",
    "ai": "artificial intelligence",

    "natural language processing": "nlp",
    "nlp": "nlp",

    "sql": "sql",

    "mysql": "mysql",

    "mongodb": "mongodb",

    "react": "react",
    "react.js": "react",

    "node": "node.js",
    "node.js": "node.js",

    "express": "express.js",
    "express.js": "express.js",

    "typescript": "typescript",

    "javascript": "javascript",

    "pytorch": "pytorch",

    "tensorflow": "tensorflow",

    "llm": "llm",
    "llms": "llm",

    "fastapi": "fastapi",

    "docker": "docker",

    "pandas": "pandas",

    "streamlit": "streamlit",

    "graphql": "graphql",

    "computer vision": "computer vision",

    "git": "git",

    "github": "github",
}


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for skill matching.
    """

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9+#.\s-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# EXTRACT SKILLS FROM CANDIDATE PROFILE
# =========================================================

def get_candidate_skills(
    candidate: CandidateProfile
) -> List[str]:
    """
    Flatten all candidate skill categories
    into a normalized list.
    """

    skills = []

    for category, skill_list in candidate.skills.items():

        for skill in skill_list:

            normalized = normalize_text(
                skill
            )

            matched_skill = None

            for alias, canonical in SKILL_ALIASES.items():

                if alias in normalized:

                    matched_skill = canonical

                    break

            if matched_skill:

                if matched_skill not in skills:

                    skills.append(
                        matched_skill
                    )

            else:

                if normalized not in skills:

                    skills.append(
                        normalized
                    )

    # Also inspect project technologies
    for project in candidate.projects:

        for technology in project.technologies:

            normalized = normalize_text(
                technology
            )

            matched_skill = None

            for alias, canonical in SKILL_ALIASES.items():

                if alias in normalized:

                    matched_skill = canonical

                    break

            if matched_skill:

                if matched_skill not in skills:

                    skills.append(
                        matched_skill
                    )

    return skills


# =========================================================
# EXTRACT REQUIRED SKILLS FROM JOB
# =========================================================

def extract_job_skills(
    job: JobProfile
) -> List[str]:
    """
    Extract recognizable skills from
    job requirements and preferred skills.
    """

    text_parts = []

    text_parts.extend(
        job.required_skills
    )

    text_parts.extend(
        job.preferred_skills
    )

    text_parts.extend(
        job.tools_and_technologies
    )

    full_text = normalize_text(
        " ".join(text_parts)
    )

    found_skills = []

    # Check longer phrases first
    aliases = sorted(
        SKILL_ALIASES.keys(),
        key=len,
        reverse=True
    )

    for alias in aliases:

        if alias in full_text:

            canonical = SKILL_ALIASES[
                alias
            ]

            if canonical not in found_skills:

                found_skills.append(
                    canonical
                )

    return found_skills


# =========================================================
# MATCH SKILLS
# =========================================================

def match_skills(
    candidate_skills: List[str],
    job_skills: List[str]
) -> Dict[str, List[str]]:
    """
    Compare candidate skills with job skills.
    """

    candidate_set = set(
        candidate_skills
    )

    job_set = set(
        job_skills
    )

    matched = sorted(
        candidate_set.intersection(
            job_set
        )
    )

    missing = sorted(
        job_set - candidate_set
    )

    return {
        "matched": matched,
        "missing": missing,
    }


# =========================================================
# MATCH SCORE
# =========================================================

def calculate_match_score(
    matched: List[str],
    required_skills: List[str]
) -> float:
    """
    Calculate percentage of job skills
    covered by the candidate.
    """

    if not required_skills:

        return 0.0

    score = (
        len(matched)
        / len(required_skills)
    ) * 100

    return round(
        score,
        2
    )


# =========================================================
# BUILD MATCH REPORT
# =========================================================

def build_match_report(
    candidate: CandidateProfile,
    job: JobProfile
) -> Dict:

    candidate_skills = get_candidate_skills(
        candidate
    )

    job_skills = extract_job_skills(
        job
    )

    required_job_skills = []

    required_text = normalize_text(
        " ".join(
            job.required_skills
        )
    )

    aliases = sorted(
        SKILL_ALIASES.keys(),
        key=len,
        reverse=True
    )

    for alias in aliases:

        if alias in required_text:

            canonical = SKILL_ALIASES[
                alias
            ]

            if canonical not in required_job_skills:

                required_job_skills.append(
                    canonical
                )

    matched_required = sorted(
        set(candidate_skills).intersection(
            set(required_job_skills)
        )
    )

    missing_required = sorted(
        set(required_job_skills)
        - set(candidate_skills)
    )

    preferred_skills = []

    preferred_text = normalize_text(
        " ".join(
            job.preferred_skills
        )
    )

    for alias in aliases:

        if alias in preferred_text:

            canonical = SKILL_ALIASES[
                alias
            ]

            if canonical not in preferred_skills:

                preferred_skills.append(
                    canonical
                )

    matched_preferred = sorted(
        set(candidate_skills).intersection(
            set(preferred_skills)
        )
    )

    missing_preferred = sorted(
        set(preferred_skills)
        - set(candidate_skills)
    )

    required_score = calculate_match_score(
        matched_required,
        required_job_skills
    )

    return {
        "role": job.role_title,

        "required_skills": {
            "matched": matched_required,
            "missing": missing_required,
        },

        "preferred_skills": {
            "matched": matched_preferred,
            "missing": missing_preferred,
        },

        "required_skill_match_percentage":
            required_score,

        "candidate_skills":
            sorted(candidate_skills),

        "job_skills":
            sorted(job_skills),
    }