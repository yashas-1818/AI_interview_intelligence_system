from typing import Dict, List, Optional
from .question_validator import are_questions_similar


# =========================================================
# QUESTION TEMPLATES
# =========================================================

QUESTION_TEMPLATES = {

    "introduction": [
        "Could you briefly introduce yourself and walk me through your background?",
        "To begin, what motivated you to specialize in software and AI engineering?",
        "Could you summarize your key technical focus areas and current career goals?",
    ],

    "resume": [
        "I noticed {project}. Could you walk me through your experience with it?",
        "Could you explain one of the most important experiences mentioned in your resume?",
        "Looking at your resume, what technical achievements are you most proud of?",
    ],

    "project": [
        "Could you explain the architecture of your {project} project?",
        "What was your specific contribution to {project}?",
        "What was the most challenging part of building {project}, and how did you solve it?",
        "What key technical trade-offs did you make while designing {project}?",
    ],

    "technical": [
        "Can you explain your experience with {skill}?",
        "How would you use {skill} to solve a real-world problem?",
        "What are some important concepts you would consider when working with {skill}?",
        "What best practices or common pitfalls do you encounter when developing with {skill}?",
    ],

    "role_specific": [
        "How would you approach {responsibility}?",
        "Can you explain how you would handle {responsibility} in a production environment?",
        "What metrics, logging, and error boundaries would you establish for {responsibility}?",
    ],

    "skill_gap": [
        "This role requires experience with {skill}. How familiar are you with it?",
        "How would you approach learning and using {skill} in a real project?",
        "Suppose you had to use {skill} for this role. How would you get started?",
    ],

    "behavioral": [
        "Tell me about a time you faced a difficult technical problem and how you handled it.",
        "Tell me about a situation where you had to work with other people to complete a project.",
        "Describe a time when something did not go according to plan. What did you do?",
    ],

    "situational": [
        "Suppose you are given a machine-learning project with an unclear requirement. How would you approach it?",
        "Imagine your model performs well during development but poorly in production. What would you investigate?",
        "Suppose a teammate disagrees with your technical approach. How would you handle the situation?",
    ],

    "closing": [
        "Is there anything else about your experience that you would like to highlight?",
        "Do you have any questions for the interviewer?",
    ],
}


# =========================================================
# ADAPTIVE FOLLOW-UP TEMPLATES
# =========================================================

PROJECT_FOLLOWUP_TEMPLATES = [
    (
        "You mentioned {target}. "
        "What was your specific technical contribution "
        "to this project?"
    ),
    (
        "You mentioned {target}. "
        "What was the main technical challenge you faced "
        "while working on it, and how did you solve it?"
    ),
    (
        "Could you explain the architecture or overall "
        "technical design of {target}?"
    ),
    (
        "What technical decisions did you make while "
        "working on {target}, and why did you choose "
        "that approach?"
    ),
    (
        "How did you evaluate whether {target} was "
        "working effectively?"
    ),
]


SKILL_FOLLOWUP_TEMPLATES = [
    (
        "You mentioned {target}. "
        "Can you explain how you have used {target} "
        "in a practical project?"
    ),
    (
        "You mentioned {target}. "
        "What was the most challenging part of using "
        "{target}, and how did you handle it?"
    ),
    (
        "How would you apply {target} to solve a "
        "real-world engineering problem?"
    ),
    (
        "What are the most important concepts you "
        "understand about {target}?"
    ),
    (
        "Can you compare {target} with another approach "
        "you have used and explain when you would choose "
        "each one?"
    ),
]


TECHNOLOGY_FOLLOWUP_TEMPLATES = [
    (
        "You mentioned {target}. "
        "Why did you choose {target} for that project?"
    ),
    (
        "How did you implement {target} in your project?"
    ),
    (
        "What challenges did you encounter while using "
        "{target}?"
    ),
    (
        "What alternatives to {target} did you consider, "
        "and why did you choose it?"
    ),
]


CONCEPT_FOLLOWUP_TEMPLATES = [
    (
        "You mentioned {target}. "
        "Could you explain how you understand this concept "
        "and where you would use it?"
    ),
    (
        "Can you give me a practical example of "
        "{target}?"
    ),
    (
        "What are the main challenges or trade-offs "
        "associated with {target}?"
    ),
]


GENERAL_FOLLOWUP_TEMPLATES = [
    (
        "Could you elaborate on {target} and explain "
        "your specific experience with it?"
    ),
    (
        "Could you give me a specific example related "
        "to {target}?"
    ),
    (
        "What was the most important thing you learned "
        "about {target}?"
    ),
]


# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def choose_first(
    values: List[str],
    default: str = ""
) -> str:
    """
    Safely return the first non-empty value.
    """

    for value in values:

        if value and str(value).strip():

            return str(value).strip()

    return default


def clean_text(
    text: str
) -> str:
    """
    Clean text before inserting it into a question.
    """

    return (
        str(text)
        .replace("\n", " ")
        .strip()
    )


# =========================================================
# CONTEXT EXTRACTION
# =========================================================

def get_context_value(
    context: Dict,
    key: str
) -> str:

    value = context.get(
        key,
        ""
    )

    if isinstance(value, list):

        return choose_first(
            [
                str(item)
                for item in value
            ]
        )

    return clean_text(
        str(value)
    )


# =========================================================
# TEMPLATE SELECTION
# =========================================================

def select_template(
    category: str,
    context: Dict,
) -> str:
    """
    Select an appropriate question template.
    """

    templates = QUESTION_TEMPLATES.get(
        category,
        QUESTION_TEMPLATES["technical"]
    )

    # -----------------------------------------------------
    # Project
    # -----------------------------------------------------

    if category == "project":

        project = get_context_value(
            context,
            "project"
        )

        if project:

            return templates[0]

    # -----------------------------------------------------
    # Resume
    # -----------------------------------------------------

    if category == "resume":

        project = get_context_value(
            context,
            "project"
        )

        if project:

            return templates[0]

        return templates[1]

    # -----------------------------------------------------
    # Technical
    # -----------------------------------------------------

    if category == "technical":

        skill = get_context_value(
            context,
            "skill"
        )

        if skill:

            return templates[0]

    # -----------------------------------------------------
    # Role-specific
    # -----------------------------------------------------

    if category == "role_specific":

        responsibility = get_context_value(
            context,
            "responsibility"
        )

        if responsibility:

            return templates[0]

    # -----------------------------------------------------
    # Skill-gap
    # -----------------------------------------------------

    if category == "skill_gap":

        skill = get_context_value(
            context,
            "skill"
        )

        if skill:

            return templates[0]

    return templates[0]


# =========================================================
# QUESTION GENERATION
# =========================================================

def _format_question_template(
    template: str,
    context: Dict,
    project: Optional[str] = None,
    skill: Optional[str] = None,
    responsibility: Optional[str] = None,
) -> str:
    proj = project or get_context_value(context, "project") or "your project"
    sk = skill or get_context_value(context, "skill") or "this skill"
    resp = responsibility or get_context_value(context, "responsibility") or "the responsibilities of this role"
    candidate_name = get_context_value(context, "candidate_name") or "yourself"
    role = get_context_value(context, "role") or "this role"

    return template.format(
        project=proj,
        skill=sk,
        responsibility=resp,
        candidate_name=candidate_name,
        role=role,
    ).strip()


def generate_question(
    context: Dict,
    template_index: int = 0,
) -> str:
    """
    Generate a deterministic, unique question from the strategy context,
    cycling through templates and candidate topics to avoid repetition.
    """
    category = context.get(
        "category",
        "technical"
    )

    templates = QUESTION_TEMPLATES.get(
        category,
        QUESTION_TEMPLATES["technical"]
    )

    prior_questions = (
        context.get("questions_asked", [])
        + context.get("skipped_questions", [])
    )

    projects = context.get("project_topics", [])
    skills = context.get("candidate_skills", [])
    gaps = context.get("skill_gaps", [])
    responsibilities = context.get("role_topics", [])

    candidate_questions: List[str] = []

    # Cycle through all available templates starting from template_index
    for i in range(len(templates)):
        idx = (template_index + i) % len(templates)
        tmpl = templates[idx]

        if category in ("project", "resume") and projects:
            for p in projects:
                candidate_questions.append(_format_question_template(tmpl, context, project=p))
        elif category == "technical" and skills:
            for s in skills:
                candidate_questions.append(_format_question_template(tmpl, context, skill=s))
        elif category == "skill_gap" and gaps:
            for g in gaps:
                candidate_questions.append(_format_question_template(tmpl, context, skill=g))
        elif category == "role_specific" and responsibilities:
            for r in responsibilities:
                candidate_questions.append(_format_question_template(tmpl, context, responsibility=r))
        else:
            candidate_questions.append(_format_question_template(tmpl, context))

    # Pick first candidate question that is NOT similar to any previously asked/skipped question
    for q in candidate_questions:
        is_dup = False
        for prior in prior_questions:
            dup, _ = are_questions_similar(q, prior)
            if dup:
                is_dup = True
                break
        if not is_dup:
            return q

    # If all templates are exhausted, return empty string so caller knows to transition category
    return ""


# =========================================================
# BUILD QUESTION CONTEXT
# =========================================================

def enrich_question_context(
    context: Dict
) -> Dict:
    """
    Convert general strategy context into context
    usable by the question generator.
    """

    enriched = dict(context)

    category = context.get(
        "category",
        ""
    )

    # -----------------------------------------------------
    # Project
    # -----------------------------------------------------

    projects = context.get(
        "project_topics",
        []
    )

    if (
        category in [
            "project",
            "resume",
        ]
        and projects
    ):

        enriched["project"] = projects[0]

    # -----------------------------------------------------
    # Technical skill
    # -----------------------------------------------------

    skills = context.get(
        "candidate_skills",
        []
    )

    if (
        category == "technical"
        and skills
    ):

        enriched["skill"] = skills[0]

    # -----------------------------------------------------
    # Skill gap
    # -----------------------------------------------------

    gaps = context.get(
        "skill_gaps",
        []
    )

    if (
        category == "skill_gap"
        and gaps
    ):

        enriched["skill"] = gaps[0]

    # -----------------------------------------------------
    # Role responsibility
    # -----------------------------------------------------

    responsibilities = context.get(
        "role_topics",
        []
    )

    if (
        category == "role_specific"
        and responsibilities
    ):

        enriched["responsibility"] = (
            responsibilities[0]
        )

    return enriched


# =========================================================
# PUBLIC GENERATOR
# =========================================================

def generate_question_from_context(
    context: Dict,
    template_index: int = 0,
) -> Dict:
    """
    Main question-generation entry point.

    Returns both the generated question and the
    context used to generate it.
    """

    enriched_context = (
        enrich_question_context(
            context
        )
    )

    question = generate_question(
        enriched_context,
        template_index
    )

    return {
        "question": question,
        "category": enriched_context.get(
            "category",
            ""
        ),
        "context": enriched_context,
        "generation_method": "template",
    }


# =========================================================
# ADAPTIVE TEMPLATE SELECTION
# =========================================================

def _select_adaptive_template(
    templates: List[str],
    context: Dict,
) -> str:
    """
    Select an adaptive template based on how many
    follow-ups have already been asked.

    This prevents the interviewer from repeatedly
    asking the same question.
    """

    followup_count = context.get(
        "followups_asked",
        0
    )

    if not isinstance(
        followup_count,
        int
    ):

        followup_count = 0

    index = (
        followup_count
        %
        len(templates)
    )

    return templates[index]


# =========================================================
# FOLLOW-UP QUESTION GENERATION
# =========================================================

def generate_followup_question(
    context: Dict,
    previous_question: str,
    previous_answer: str,
) -> str:
    """
    Generate a contextual follow-up question based on:

    - Previous question
    - Candidate answer
    - Detected answer topics
    - Follow-up target
    - Probe type
    """

    # -----------------------------------------------------
    # Retrieve adaptive information
    # -----------------------------------------------------

    followup_targets = context.get(
        "follow_up_targets",
        {}
    )

    if not isinstance(
        followup_targets,
        dict
    ):

        followup_targets = {}

    target = followup_targets.get(
        "primary_target",
        ""
    )

    probe_type = followup_targets.get(
        "probe_type",
        "general_follow_up"
    )

    # -----------------------------------------------------
    # Fallback target extraction
    # -----------------------------------------------------

    if not target:

        topics = context.get(
            "answer_topics",
            {}
        )

        if isinstance(
            topics,
            dict
        ):

            target = choose_first(
                topics.get(
                    "topics",
                    []
                )
            )

    # -----------------------------------------------------
    # Final fallback
    # -----------------------------------------------------

    if not target:

        target = "your previous answer"

    target = clean_text(
        target
    )

    # -----------------------------------------------------
    # Select template group
    # -----------------------------------------------------

    if probe_type == "project_deep_dive":

        templates = (
            PROJECT_FOLLOWUP_TEMPLATES
        )

    elif probe_type == "skill_deep_dive":

        templates = (
            SKILL_FOLLOWUP_TEMPLATES
        )

    elif probe_type == "technology_deep_dive":

        templates = (
            TECHNOLOGY_FOLLOWUP_TEMPLATES
        )

    elif probe_type == "concept_deep_dive":

        templates = (
            CONCEPT_FOLLOWUP_TEMPLATES
        )

    elif probe_type in [
        "ask_for_detail",
        "ask_for_example",
        "general_follow_up",
    ]:

        templates = (
            GENERAL_FOLLOWUP_TEMPLATES
        )

    else:

        templates = (
            GENERAL_FOLLOWUP_TEMPLATES
        )

    # -----------------------------------------------------
    # Select different template based on follow-up count
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Select different template based on follow-up count & avoid duplicates
    # -----------------------------------------------------

    prior_questions = (
        context.get("questions_asked", [])
        + context.get("skipped_questions", [])
    )

    followup_count = context.get("followups_asked", 0)
    if not isinstance(followup_count, int):
        followup_count = 0

    # Try cycling templates in the selected group to find a novel follow-up
    for i in range(len(templates)):
        idx = (followup_count + i) % len(templates)
        tmpl = templates[idx]
        candidate_q = tmpl.format(target=target).strip()
        is_dup = False
        for prior in prior_questions:
            dup, _ = are_questions_similar(candidate_q, prior)
            if dup:
                is_dup = True
                break
        if not is_dup:
            return candidate_q

    # Fallback to general follow-ups
    for tmpl in GENERAL_FOLLOWUP_TEMPLATES:
        candidate_q = tmpl.format(target=target).strip()
        is_dup = any(are_questions_similar(candidate_q, prior)[0] for prior in prior_questions)
        if not is_dup:
            return candidate_q

    return f"Could you elaborate more on your work with {target}?"


# =========================================================
# NEXT QUESTION GENERATION
# =========================================================

def generate_next_question(
    context: Dict,
    decision: Dict,
    previous_question: str = "",
    previous_answer: str = "",
) -> Dict:
    """
    Generate the next interview question based on
    the adaptive decision.
    """

    action = decision.get(
        "action",
        "continue"
    )

    # -----------------------------------------------------
    # FOLLOW-UP
    # -----------------------------------------------------

    if action == "follow_up":

        question = generate_followup_question(
            context=context,
            previous_question=previous_question,
            previous_answer=previous_answer,
        )

        return {
            "question": question,
            "category": context.get(
                "category",
                ""
            ),
            "action": "follow_up",
            "generation_method": "adaptive_template",
        }

    # -----------------------------------------------------
    # CLARIFICATION
    # -----------------------------------------------------

    if action == "clarify":

        topics = context.get(
            "answer_topics",
            {}
        )

        target = ""

        if isinstance(
            topics,
            dict
        ):

            target = choose_first(
                topics.get(
                    "topics",
                    []
                )
            )

        if target:

            question = (
                f"Could you clarify what you meant "
                f"by {target} and explain it in a "
                f"little more detail?"
            )

        else:

            question = (
                "Could you clarify your previous "
                "answer and explain it in a little "
                "more detail?"
            )

        return {
            "question": question,
            "category": context.get(
                "category",
                ""
            ),
            "action": "clarify",
            "generation_method": "adaptive_template",
        }

    # -----------------------------------------------------
    # INCREASE DIFFICULTY
    # -----------------------------------------------------

    if action == "increase_difficulty":

        enriched_context = (
            enrich_question_context(
                context
            )
        )

        question = generate_question(
            enriched_context
        )

        return {
            "question": question,
            "category": enriched_context.get(
                "category",
                ""
            ),
            "action": "increase_difficulty",
            "exhausted": question == "",
            "generation_method": "template",
        }

    # -----------------------------------------------------
    # DECREASE DIFFICULTY
    # -----------------------------------------------------

    if action == "decrease_difficulty":

        enriched_context = (
            enrich_question_context(
                context
            )
        )

        question = generate_question(
            enriched_context
        )

        return {
            "question": question,
            "category": enriched_context.get(
                "category",
                ""
            ),
            "action": "decrease_difficulty",
            "exhausted": question == "",
            "generation_method": "template",
        }

    # -----------------------------------------------------
    # NEW TOPIC
    # -----------------------------------------------------

    if action == "new_topic":

        enriched_context = (
            enrich_question_context(
                context
            )
        )

        question = generate_question(
            enriched_context
        )

        return {
            "question": question,
            "category": enriched_context.get(
                "category",
                ""
            ),
            "action": "new_topic",
            "exhausted": question == "",
            "generation_method": "template",
        }

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    enriched_context = (
        enrich_question_context(
            context
        )
    )

    question = generate_question(
        enriched_context
    )

    return {
        "question": question,
        "category": enriched_context.get(
            "category",
            ""
        ),
        "action": "continue",
        "exhausted": question == "",
        "generation_method": "template",
    }