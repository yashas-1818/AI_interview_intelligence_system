import re
from typing import Dict, List

from mock_interview.resume.profile import (
    CandidateProfile,
    CandidateInfo,
    Education,
    Experience,
    Project,
)


# =========================================================
# RESUME SECTION HEADERS
# =========================================================

SECTION_HEADERS = {
    "summary": [
        "summary",
        "profile",
        "objective",
    ],

    "technical_skills": [
        "technical skills",
        "skills",
        "technical expertise",
        "core skills",
    ],

    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "internship",
    ],

    "projects": [
        "projects",
        "academic projects",
        "personal projects",
        "key projects",
    ],

    "leadership": [
        "leadership",
        "leadership experience",
        "positions of responsibility",
    ],

    "certifications": [
        "certifications",
        "certificates",
    ],

    "education": [
        "education",
        "academic background",
        "educational qualifications",
    ],
}


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text: str) -> str:
    """
    Clean and normalize extracted resume text.
    """

    text = text.replace("\r", "")

    # Fix words broken across PDF lines.
    # Example:
    # natural-
    # language
    # becomes:
    # natural-language
    text = re.sub(
        r"-\s*\n\s*",
        "-",
        text
    )

    # Normalize spaces and tabs
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    # Remove excessive blank lines
    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# =========================================================
# SECTION DETECTION
# =========================================================

def detect_sections(text: str) -> Dict[str, str]:
    """
    Detect major resume sections.
    """

    text = normalize_text(text)

    lines = text.splitlines()

    sections = {
        "header": []
    }

    current_section = "header"

    normalized_headers = {}

    for section, headers in SECTION_HEADERS.items():

        for header in headers:

            normalized_headers[
                header.lower()
            ] = section

    for line in lines:

        cleaned_line = line.strip().lower()

        if cleaned_line in normalized_headers:

            current_section = normalized_headers[
                cleaned_line
            ]

            if current_section not in sections:

                sections[current_section] = []

        else:

            sections[current_section].append(
                line.strip()
            )

    for section in sections:

        sections[section] = "\n".join(
            sections[section]
        ).strip()

    return sections


# =========================================================
# CONTACT INFORMATION
# =========================================================

def extract_contact_info(
    header: str
) -> CandidateInfo:

    lines = [
        line.strip()
        for line in header.splitlines()
        if line.strip()
    ]

    name = ""
    email = ""
    phone = ""
    linkedin = ""

    if lines:

        name = lines[0]

    # Email
    email_match = re.search(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        header
    )

    if email_match:

        email = email_match.group(0)

    # Phone
    phone_match = re.search(
        r"(?:\+91[\s-]?)?[6-9]\d{9}",
        header
    )

    if phone_match:

        phone = phone_match.group(0)

    # LinkedIn
    linkedin_match = re.search(
        r"(https?://)?(www\.)?"
        r"linkedin\.com/[^\s|]+",
        header,
        re.IGNORECASE
    )

    if linkedin_match:

        linkedin = linkedin_match.group(0)

    elif "linkedin" in header.lower():

        linkedin = "LinkedIn"

    return CandidateInfo(
        name=name,
        email=email,
        phone=phone,
        linkedin=linkedin,
    )


# =========================================================
# SKILLS
# =========================================================

def extract_skills(
    skills_text: str
) -> Dict[str, List[str]]:

    skills = {}

    for line in skills_text.splitlines():

        line = line.strip()

        line = line.lstrip("•").strip()

        if ":" not in line:

            continue

        category, values = line.split(
            ":",
            1
        )

        category = category.strip().lower()

        values = values.strip()

        skill_list = [
            skill.strip()
            for skill in values.split(",")
            if skill.strip()
        ]

        if skill_list:

            skills[category] = skill_list

    return skills


# =========================================================
# EXPERIENCE
# =========================================================

def extract_experience(
    experience_text: str
) -> List[Experience]:

    if not experience_text.strip():

        return []

    lines = [
        line.strip()
        for line in experience_text.splitlines()
        if line.strip()
    ]

    experiences = []

    current_position = ""
    current_company = ""
    current_duration = ""

    for line in lines:

        # Example:
        # AI/ML Intern – WizzyBox Private Limited

        if " – " in line:

            parts = line.split(
                " – ",
                1
            )

            if len(parts) == 2:

                current_position = (
                    parts[0].strip()
                )

                current_company = (
                    parts[1].strip()
                )

                continue

        # Normal hyphen
        if " - " in line:

            parts = line.split(
                " - ",
                1
            )

            if len(parts) == 2:

                current_position = (
                    parts[0].strip()
                )

                current_company = (
                    parts[1].strip()
                )

                continue

        # Duration
        if line.lower() in [
            "present",
            "current",
        ]:

            current_duration = line

            continue

    if current_position or current_company:

        experiences.append(
            Experience(
                company=current_company,
                position=current_position,
                duration=current_duration,
                description=experience_text,
            )
        )

    return experiences


# =========================================================
# PROJECT HELPERS
# =========================================================

def looks_like_project_title(
    line: str
) -> bool:

    line = line.strip()

    if not line:

        return False

    if line.startswith("•"):

        return False

    lower = line.lower()

    description_starters = [
        "built ",
        "developed ",
        "designed ",
        "integrated ",
        "implemented ",
        "deployed ",
        "created ",
        "building ",
        "led ",
        "using ",
        "migrating ",
        "resolving ",
    ]

    if any(
        lower.startswith(prefix)
        for prefix in description_starters
    ):

        return False

    if line.endswith("."):

        return False

    known_project_patterns = [
        "skylark",
        "traders paradise",
        "ai-powered interview intelligence system",
        "event management system",
    ]

    if any(
        pattern in lower
        for pattern in known_project_patterns
    ):

        return True

    if len(line.split()) <= 10:

        return True

    return False


def parse_technologies(
    line: str
) -> List[str]:

    return [
        item.strip()
        for item in line.split(",")
        if item.strip()
    ]


# =========================================================
# PROJECT EXTRACTION
# =========================================================

def extract_projects(
    projects_text: str
) -> List[Project]:

    if not projects_text.strip():

        return []

    lines = projects_text.splitlines()

    projects = []

    current_project = None

    expecting_technology_line = False

    for raw_line in lines:

        line = raw_line.strip()

        if not line:

            continue

        # -------------------------------------------------
        # Bullet description
        # -------------------------------------------------

        if line.startswith("•"):

            if current_project:

                description = (
                    line
                    .lstrip("•")
                    .strip()
                )

                if current_project["description"]:

                    current_project[
                        "description"
                    ] += " "

                current_project[
                    "description"
                ] += description

            continue

        # -------------------------------------------------
        # Technology line
        # -------------------------------------------------

        if (
            current_project
            and expecting_technology_line
            and "," in line
        ):

            current_project[
                "technologies"
            ] = parse_technologies(line)

            expecting_technology_line = False

            continue

        # -------------------------------------------------
        # New project title
        # -------------------------------------------------

        if looks_like_project_title(line):

            if current_project:

                projects.append(
                    Project(
                        **current_project
                    )
                )

            current_project = {
                "name": line,
                "technologies": [],
                "description": "",
            }

            expecting_technology_line = True

            continue

        # -------------------------------------------------
        # Continuation of project
        # -------------------------------------------------

        if current_project:

            if current_project["description"]:

                current_project[
                    "description"
                ] += " "

            current_project[
                "description"
            ] += line

    if current_project:

        projects.append(
            Project(
                **current_project
            )
        )

    return projects


# =========================================================
# CERTIFICATIONS
# =========================================================

def extract_certifications(
    certifications_text: str
) -> List[str]:

    certifications = []

    for line in certifications_text.splitlines():

        line = line.strip()

        line = line.lstrip("•").strip()

        if line:

            certifications.append(line)

    return certifications


# =========================================================
# LEADERSHIP
# =========================================================

def extract_leadership(
    leadership_text: str
) -> List[str]:

    leadership = []

    for line in leadership_text.splitlines():

        line = line.strip()

        line = line.lstrip("•").strip()

        if line:

            leadership.append(line)

    return leadership


# =========================================================
# EDUCATION
# =========================================================

def extract_education(
    education_text: str
) -> List[Education]:

    lines = [
        line.strip()
        for line in education_text.splitlines()
        if line.strip()
    ]

    education = []

    current = None

    institution_keywords = [
        "institute",
        "college",
        "school",
    ]

    for line in lines:

        lower = line.lower()

        # -------------------------------------------------
        # Institution
        # -------------------------------------------------

        if any(
            keyword in lower
            for keyword in institution_keywords
        ):

            if current:

                education.append(
                    Education(
                        **current
                    )
                )

            current = {
                "institution": line,
                "degree": "",
                "duration": "",
                "score": "",
            }

            continue

        if current is None:

            continue

        # -------------------------------------------------
        # Duration
        # -------------------------------------------------

        duration_match = re.search(
            r"\b"
            r"(19|20)\d{2}"
            r"\s*[-–]\s*"
            r"(Present|(19|20)\d{2})"
            r"\b",
            line,
            re.IGNORECASE,
        )

        if duration_match:

            current[
                "duration"
            ] = duration_match.group(0)

            continue

        # -------------------------------------------------
        # Score
        # -------------------------------------------------

        score_match = re.search(
            r"(CGPA\s*:\s*[\d.]+)"
            r"|"
            r"([\d.]+\s*%)",
            line,
            re.IGNORECASE,
        )

        if score_match:

            if score_match.group(1):

                current[
                    "score"
                ] = score_match.group(1)

            else:

                current[
                    "score"
                ] = score_match.group(2)

        # -------------------------------------------------
        # Degree
        # -------------------------------------------------

        degree_keywords = [
            "bachelor",
            "master",
            "degree",
            "b.e",
            "b.tech",
            "m.e",
            "m.tech",
            "puc",
            "cbse",
        ]

        if any(
            keyword in lower
            for keyword in degree_keywords
        ):

            degree = line

            degree = re.sub(
                r"\s*[-–]?\s*"
                r"CGPA\s*:\s*[\d.]+",
                "",
                degree,
                flags=re.IGNORECASE,
            )

            degree = re.sub(
                r"\s*[-–]?\s*"
                r"[\d.]+\s*%",
                "",
                degree,
            )

            current[
                "degree"
            ] = degree.strip()

    if current:

        education.append(
            Education(
                **current
            )
        )

    return education


# =========================================================
# BUILD CANDIDATE PROFILE
# =========================================================

def build_candidate_profile(
    text: str
) -> CandidateProfile:

    sections = detect_sections(text)

    candidate = extract_contact_info(
        sections.get(
            "header",
            ""
        )
    )

    summary = sections.get(
        "summary",
        ""
    )

    skills = extract_skills(
        sections.get(
            "technical_skills",
            ""
        )
    )

    experience = extract_experience(
        sections.get(
            "experience",
            ""
        )
    )

    projects = extract_projects(
        sections.get(
            "projects",
            ""
        )
    )

    leadership = extract_leadership(
        sections.get(
            "leadership",
            ""
        )
    )

    certifications = extract_certifications(
        sections.get(
            "certifications",
            ""
        )
    )

    education = extract_education(
        sections.get(
            "education",
            ""
        )
    )

    return CandidateProfile(
        candidate=candidate,
        summary=summary,
        skills=skills,
        experience=experience,
        projects=projects,
        leadership=leadership,
        certifications=certifications,
        education=education,
    )


# =========================================================
# DIRECT TEST
# =========================================================

if __name__ == "__main__":

    print(
        "Resume analyzer module loaded successfully."
    )