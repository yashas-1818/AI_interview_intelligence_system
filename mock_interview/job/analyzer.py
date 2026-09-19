import re
from typing import List

from mock_interview.job.profile import JobProfile


# =========================================================
# LINE NORMALIZATION
# =========================================================

def normalize_line(
    line: str
) -> str:
    """
    Clean a single job-description line.
    """

    return (
        line
        .strip()
        .lstrip("•- ")
        .strip()
    )


# =========================================================
# BULLET EXTRACTION
# =========================================================

def extract_bullets(
    lines: List[str]
) -> List[str]:
    """
    Extract clean bullet-point items.
    """

    items = []

    for line in lines:

        cleaned = normalize_line(line)

        if cleaned:

            items.append(cleaned)

    return items


# =========================================================
# SECTION EXTRACTION
# =========================================================

def find_section(
    lines: List[str],
    headers: List[str]
) -> List[str]:
    """
    Find content belonging to a specific
    job-description section.
    """

    start_index = None

    normalized_headers = [
        header.lower().rstrip(":")
        for header in headers
    ]

    # Find section
    for index, line in enumerate(lines):

        lower = line.lower().strip()

        if lower.rstrip(":") in normalized_headers:

            start_index = index + 1

            break

    if start_index is None:

        return []

    section_lines = []

    # Common section headers
    all_section_headers = [
        "requirements",
        "required skills",
        "required qualifications",
        "must have",
        "responsibilities",
        "key responsibilities",
        "what you'll do",
        "what you will do",
        "qualifications",
        "basic qualifications",
        "preferred",
        "preferred skills",
        "preferred qualifications",
        "nice to have",
        "education",
        "educational qualifications",
        "experience",
        "experience required",
    ]

    for line in lines[start_index:]:

        lower = line.lower().strip()

        if (
            lower.rstrip(":")
            in all_section_headers
        ):

            break

        section_lines.append(line)

    return extract_bullets(
        section_lines
    )


# =========================================================
# ROLE TITLE
# =========================================================

def extract_role_title(
    lines: List[str]
) -> str:
    """
    Assume the first meaningful line
    is the job title.
    """

    if not lines:

        return ""

    return normalize_line(
        lines[0]
    )


# =========================================================
# EXPERIENCE
# =========================================================

def extract_experience(
    text: str
) -> str:
    """
    Extract experience requirement.

    Examples:
        0-2 years
        2+ years
        3 years
    """

    match = re.search(
        r"(\d+\s*[-–]\s*\d+\s*years?"
        r"|\d+\+?\s*years?)",
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(1)

    return ""


# =========================================================
# BUILD JOB PROFILE
# =========================================================

def analyze_job_description(
    text: str
) -> JobProfile:
    """
    Convert raw job-description text
    into a structured JobProfile.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    full_text = "\n".join(lines)

    # -----------------------------------------------------
    # Role
    # -----------------------------------------------------

    role_title = extract_role_title(
        lines
    )

    # -----------------------------------------------------
    # Responsibilities
    # -----------------------------------------------------

    responsibilities = find_section(
        lines,
        [
            "responsibilities",
            "key responsibilities",
            "what you'll do",
            "what you will do",
        ]
    )

    # -----------------------------------------------------
    # Required skills
    # -----------------------------------------------------

    required_skills = find_section(
        lines,
        [
            "requirements",
            "required skills",
            "required qualifications",
            "must have",
        ]
    )

    # -----------------------------------------------------
    # Preferred skills
    # -----------------------------------------------------

    preferred_skills = find_section(
        lines,
        [
            "preferred",
            "preferred skills",
            "preferred qualifications",
            "nice to have",
        ]
    )

    # -----------------------------------------------------
    # Education
    # -----------------------------------------------------

    education = find_section(
        lines,
        [
            "education",
            "educational qualifications",
        ]
    )

    # -----------------------------------------------------
    # Qualifications
    # -----------------------------------------------------

    qualifications = find_section(
        lines,
        [
            "qualifications",
            "basic qualifications",
        ]
    )

    # -----------------------------------------------------
    # Experience
    # -----------------------------------------------------

    experience_required = extract_experience(
        full_text
    )

    # -----------------------------------------------------
    # Create JobProfile
    # -----------------------------------------------------

    return JobProfile(
        role_title=role_title,

        company="",

        summary=full_text,

        required_skills=required_skills,

        preferred_skills=preferred_skills,

        responsibilities=responsibilities,

        qualifications=qualifications,

        experience_required=experience_required,

        education_required=education,

        tools_and_technologies=[],

        keywords=[],
    )


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    print(
        "Job analyzer module loaded successfully."
    )