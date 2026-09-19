import re
from typing import Dict, List


# =========================================================
# STOP WORDS
# =========================================================

STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "is",
    "are",
    "was",
    "were",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "this",
    "that",
    "it",
    "i",
    "we",
    "my",
    "our",
    "they",
    "their",
    "you",
    "your",
    "have",
    "has",
    "had",
    "do",
    "did",
    "can",
    "could",
    "would",
    "should",
    "be",
    "been",
    "from",
    "as",
    "at",
    "by",
    "about",
    "how",
    "what",
    "why",
    "when",
    "where",
    "which",
}


# =========================================================
# BASIC TEXT PROCESSING
# =========================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for keyword and phrase matching.
    """

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def tokenize(text: str) -> List[str]:
    """
    Convert text into meaningful tokens.
    """

    normalized = normalize_text(text)

    words = normalized.split()

    return [
        word
        for word in words
        if word not in STOP_WORDS
    ]


# =========================================================
# ANSWER LENGTH
# =========================================================

def calculate_answer_length(
    answer: str,
) -> Dict:
    """
    Calculate basic answer-length information.
    """

    words = answer.split()

    word_count = len(words)

    if word_count == 0:
        level = "empty"

    elif word_count < 8:
        level = "very_short"

    elif word_count < 25:
        level = "short"

    elif word_count < 60:
        level = "medium"

    elif word_count < 120:
        level = "long"

    else:
        level = "very_long"

    return {
        "word_count": word_count,
        "length_level": level,
    }


# =========================================================
# QUESTION KEYWORDS
# =========================================================

def extract_question_keywords(
    question: str,
) -> List[str]:
    """
    Extract meaningful words from the question.
    """

    return list(
        dict.fromkeys(
            tokenize(question)
        )
    )


# =========================================================
# ANSWER KEYWORDS
# =========================================================

def extract_answer_keywords(
    answer: str,
) -> List[str]:
    """
    Extract meaningful words from the answer.
    """

    return list(
        dict.fromkeys(
            tokenize(answer)
        )
    )


# =========================================================
# RELEVANCE
# =========================================================

def calculate_relevance(
    question: str,
    answer: str,
) -> Dict:
    """
    Estimate answer relevance using keyword overlap.

    This is a deterministic baseline.
    Later the LLM can perform semantic relevance analysis.
    """

    question_keywords = set(
        extract_question_keywords(question)
    )

    answer_keywords = set(
        extract_answer_keywords(answer)
    )

    if not question_keywords:
        overlap = 0.0

    else:
        overlap = (
            len(
                question_keywords
                & answer_keywords
            )
            /
            len(question_keywords)
        )

    if not answer.strip():
        level = "none"

    elif overlap >= 0.40:
        level = "high"

    elif overlap >= 0.20:
        level = "medium"

    elif len(answer_keywords) >= 5:
        level = "medium"

    else:
        level = "low"

    return {
        "score": round(
            overlap * 100,
            2,
        ),
        "level": level,
        "matched_keywords": sorted(
            question_keywords
            & answer_keywords
        ),
    }


# =========================================================
# TECHNICAL DEPTH
# =========================================================

TECHNICAL_INDICATORS = {
    "because",
    "architecture",
    "algorithm",
    "api",
    "database",
    "model",
    "training",
    "testing",
    "deployment",
    "deploy",
    "pipeline",
    "performance",
    "optimization",
    "implementation",
    "implemented",
    "integration",
    "integrated",
    "framework",
    "system",
    "backend",
    "frontend",
    "data",
    "processing",
    "accuracy",
    "latency",
    "scaling",
    "security",
    "error",
    "debugging",
    "solution",
    "approach",
}


def calculate_technical_depth(
    answer: str,
) -> Dict:
    """
    Estimate technical depth using technical indicators.
    """

    keywords = set(
        tokenize(answer)
    )

    matched = sorted(
        keywords
        & TECHNICAL_INDICATORS
    )

    count = len(matched)

    if count >= 6:
        level = "high"

    elif count >= 3:
        level = "medium"

    elif count >= 1:
        level = "low"

    else:
        level = "minimal"

    return {
        "level": level,
        "indicator_count": count,
        "indicators": matched,
    }


# =========================================================
# COMPLETENESS
# =========================================================

COMPLETENESS_INDICATORS = {
    "because",
    "therefore",
    "however",
    "first",
    "second",
    "finally",
    "also",
    "then",
    "so",
    "result",
    "resulted",
    "reason",
    "approach",
    "problem",
    "solution",
    "challenge",
}


def calculate_completeness(
    answer: str,
) -> Dict:
    """
    Estimate whether the answer contains enough
    information to be considered complete.
    """

    words = answer.split()

    word_count = len(words)

    keywords = set(
        tokenize(answer)
    )

    indicators = sorted(
        keywords
        & COMPLETENESS_INDICATORS
    )

    indicator_count = len(
        indicators
    )

    if word_count == 0:
        level = "none"

    elif word_count < 8:
        level = "low"

    elif (
        word_count >= 40
        and indicator_count >= 2
    ):
        level = "high"

    elif word_count >= 20:
        level = "medium"

    else:
        level = "low"

    return {
        "level": level,
        "indicator_count": indicator_count,
        "indicators": indicators,
    }


# =========================================================
# CLARITY
# =========================================================

FILLER_WORDS = {
    "um",
    "uh",
    "like",
    "basically",
    "actually",
    "maybe",
    "probably",
    "you know",
}


def calculate_clarity(
    answer: str,
) -> Dict:
    """
    Basic clarity estimate.

    Later this can incorporate speech features
    such as pauses, filler frequency and speaking rate.
    """

    words = answer.lower().split()

    if not words:
        return {
            "level": "none",
            "filler_count": 0,
            "filler_ratio": 0.0,
        }

    filler_count = sum(
        1
        for word in words
        if word.strip(
            ".,!?;"
        ) in FILLER_WORDS
    )

    filler_ratio = (
        filler_count
        /
        len(words)
    )

    if filler_ratio <= 0.03:
        level = "good"

    elif filler_ratio <= 0.08:
        level = "moderate"

    else:
        level = "needs_improvement"

    return {
        "level": level,
        "filler_count": filler_count,
        "filler_ratio": round(
            filler_ratio,
            3,
        ),
    }


# =========================================================
# VAGUENESS
# =========================================================

VAGUE_PHRASES = [
    "something",
    "somehow",
    "stuff",
    "things",
    "etc",
    "and so on",
    "i think",
    "maybe",
    "kind of",
    "sort of",
    "not sure",
    "i don't know",
]


def detect_vagueness(
    answer: str,
) -> Dict:
    """
    Detect vague language.
    """

    normalized = answer.lower()

    matched = []

    for phrase in VAGUE_PHRASES:

        if phrase in normalized:
            matched.append(
                phrase
            )

    if not answer.strip():
        level = "none"

    elif len(matched) >= 3:
        level = "high"

    elif len(matched) >= 1:
        level = "medium"

    else:
        level = "low"

    return {
        "level": level,
        "phrases": matched,
    }


# =========================================================
# DOMAIN KNOWLEDGE
# =========================================================

KNOWN_SKILLS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "sql",
    "machine learning",
    "deep learning",
    "nlp",
    "natural language processing",
    "computer vision",
    "data science",
    "artificial intelligence",
    "ai",
    "ml",
    "pytorch",
    "tensorflow",
    "fastapi",
    "docker",
    "react",
    "node",
    "nodejs",
    "express",
    "pandas",
    "streamlit",
    "mongodb",
    "mysql",
    "git",
    "github",
    "power bi",
    "llm",
    "llms",
}


KNOWN_TECHNOLOGIES = {
    "python",
    "java",
    "javascript",
    "typescript",
    "pytorch",
    "tensorflow",
    "fastapi",
    "docker",
    "react",
    "node",
    "nodejs",
    "express",
    "pandas",
    "streamlit",
    "mongodb",
    "mysql",
    "git",
    "github",
    "power bi",
}


KNOWN_CONCEPTS = {
    "machine learning",
    "deep learning",
    "natural language processing",
    "nlp",
    "artificial intelligence",
    "ai",
    "data processing",
    "data analysis",
    "model training",
    "model deployment",
    "api",
    "database",
    "architecture",
    "backend",
    "frontend",
    "algorithm",
    "optimization",
    "testing",
    "deployment",
    "pipeline",
    "performance",
    "security",
    "scalability",
    "debugging",
}


KNOWN_PROJECTS = {
    "skylark",
    "traders paradise",
    "ai powered interview intelligence system",
    "event management system",
}


# =========================================================
# GENERIC ENTITY EXTRACTION
# =========================================================

def _find_phrases(
    text: str,
    phrases: set,
) -> List[str]:
    """
    Find known multi-word or single-word phrases
    in normalized text.
    """

    normalized = normalize_text(text)

    found = []

    for phrase in sorted(
        phrases,
        key=len,
        reverse=True,
    ):

        normalized_phrase = normalize_text(
            phrase
        )

        if not normalized_phrase:
            continue

        pattern = (
            r"\b"
            + re.escape(
                normalized_phrase
            )
            + r"\b"
        )

        if re.search(
            pattern,
            normalized,
        ):
            found.append(
                phrase
            )

    return found


# =========================================================
# MENTIONED SKILLS
# =========================================================

def extract_mentioned_skills(
    answer: str,
) -> List[str]:
    """
    Detect known skills mentioned by the candidate.
    """

    return _find_phrases(
        answer,
        KNOWN_SKILLS,
    )


# =========================================================
# MENTIONED TECHNOLOGIES
# =========================================================

def extract_mentioned_technologies(
    answer: str,
) -> List[str]:
    """
    Detect technologies mentioned by the candidate.
    """

    return _find_phrases(
        answer,
        KNOWN_TECHNOLOGIES,
    )


# =========================================================
# MENTIONED CONCEPTS
# =========================================================

def extract_mentioned_concepts(
    answer: str,
) -> List[str]:
    """
    Detect technical concepts mentioned by the candidate.
    """

    return _find_phrases(
        answer,
        KNOWN_CONCEPTS,
    )


# =========================================================
# MENTIONED PROJECTS
# =========================================================

def extract_mentioned_projects(
    answer: str,
) -> List[str]:
    """
    Detect known projects mentioned by the candidate.
    """

    return _find_phrases(
        answer,
        KNOWN_PROJECTS,
    )


# =========================================================
# DETECTED TOPICS
# =========================================================

def detect_answer_topics(
    answer: str,
) -> Dict:
    """
    Extract the main topics/entities mentioned
    in the candidate's answer.
    """

    skills = extract_mentioned_skills(
        answer
    )

    technologies = (
        extract_mentioned_technologies(
            answer
        )
    )

    concepts = extract_mentioned_concepts(
        answer
    )

    projects = extract_mentioned_projects(
        answer
    )

    topics = []

    for item in (
        projects
        + skills
        + technologies
        + concepts
    ):

        if item not in topics:
            topics.append(item)

    return {
        "skills": skills,
        "technologies": technologies,
        "concepts": concepts,
        "projects": projects,
        "topics": topics,
    }


# =========================================================
# FOLLOW-UP TARGETS
# =========================================================

def determine_followup_targets(
    answer_topics: Dict,
    technical_depth: str,
    completeness: str,
    answer_length: str,
) -> Dict:
    """
    Determine which detected topics should be explored
    in a follow-up question.
    """

    targets = []

    projects = answer_topics.get(
        "projects",
        [],
    )

    skills = answer_topics.get(
        "skills",
        [],
    )

    technologies = answer_topics.get(
        "technologies",
        [],
    )

    concepts = answer_topics.get(
        "concepts",
        [],
    )

    # -----------------------------------------------------
    # Project-first probing
    # -----------------------------------------------------

    for project in projects:

        if project not in targets:
            targets.append(
                project
            )

    # -----------------------------------------------------
    # Skill probing
    # -----------------------------------------------------

    for skill in skills:

        if skill not in targets:
            targets.append(
                skill
            )

    # -----------------------------------------------------
    # Technology probing
    # -----------------------------------------------------

    for technology in technologies:

        if technology not in targets:
            targets.append(
                technology
            )

    # -----------------------------------------------------
    # Concept probing
    # -----------------------------------------------------

    if technical_depth in [
        "minimal",
        "low",
    ]:

        for concept in concepts:

            if concept not in targets:
                targets.append(
                    concept
                )

    # -----------------------------------------------------
    # Determine probe type
    # -----------------------------------------------------

    if projects:
        probe_type = "project_deep_dive"

    elif skills:
        probe_type = "skill_deep_dive"

    elif technologies:
        probe_type = "technology_deep_dive"

    elif concepts:
        probe_type = "concept_deep_dive"

    elif completeness in [
        "low",
        "none",
    ]:

        probe_type = "ask_for_detail"

    elif answer_length in [
        "very_short",
        "short",
    ]:

        probe_type = "ask_for_example"

    else:
        probe_type = "general_follow_up"

    return {
        "targets": targets[:5],
        "primary_target": (
            targets[0]
            if targets
            else ""
        ),
        "probe_type": probe_type,
    }


# =========================================================
# FOLLOW-UP DECISION
# =========================================================

def determine_followup(
    relevance: str,
    completeness: str,
    technical_depth: str,
    vagueness: str,
    answer_length: str,
    answer_topics: Dict,
) -> Dict:
    """
    Determine whether a follow-up question should be asked.
    """

    reasons = []

    # -----------------------------------------------------
    # Empty answer
    # -----------------------------------------------------

    if answer_length == "empty":

        return {
            "needs_follow_up": True,
            "action": "clarify",
            "reason": (
                "Candidate did not provide an answer."
            ),
            "reasons": [
                "candidate did not provide an answer"
            ],
        }

    # -----------------------------------------------------
    # Very short
    # -----------------------------------------------------

    if answer_length == "very_short":

        reasons.append(
            "answer is too short"
        )

    # -----------------------------------------------------
    # Low relevance
    # -----------------------------------------------------

    if relevance in [
        "none",
        "low",
    ]:

        reasons.append(
            "answer may not address the question"
        )

    # -----------------------------------------------------
    # Low completeness
    # -----------------------------------------------------

    if completeness in [
        "none",
        "low",
    ]:

        reasons.append(
            "answer lacks sufficient detail"
        )

    # -----------------------------------------------------
    # Weak technical depth
    # -----------------------------------------------------

    if technical_depth in [
        "minimal",
        "low",
    ]:

        reasons.append(
            "technical explanation may need deeper probing"
        )

    # -----------------------------------------------------
    # Vague language
    # -----------------------------------------------------

    if vagueness in [
        "medium",
        "high",
    ]:

        reasons.append(
            "answer contains vague statements"
        )

    # -----------------------------------------------------
    # Follow-up required
    # -----------------------------------------------------

    if reasons:

        if relevance in [
            "none",
            "low",
        ]:

            action = "clarify"

        elif technical_depth in [
            "minimal",
            "low",
        ]:

            action = "probe_deeper"

        else:

            action = "ask_for_example"

        return {
            "needs_follow_up": True,
            "action": action,
            "reasons": reasons,
        }

    # -----------------------------------------------------
    # Good answer
    # -----------------------------------------------------

    return {
        "needs_follow_up": False,
        "action": "continue",
        "reasons": [],
    }


# =========================================================
# OVERALL ASSESSMENT
# =========================================================

def calculate_overall_quality(
    relevance: str,
    completeness: str,
    technical_depth: str,
    clarity: str,
    vagueness: str,
) -> Dict:
    """
    Produce a baseline overall answer-quality rating.
    """

    score = 0

    # -----------------------------------------------------
    # Relevance
    # -----------------------------------------------------

    relevance_scores = {
        "high": 4,
        "medium": 3,
        "low": 1,
        "none": 0,
    }

    score += relevance_scores.get(
        relevance,
        0,
    )

    # -----------------------------------------------------
    # Completeness
    # -----------------------------------------------------

    completeness_scores = {
        "high": 4,
        "medium": 3,
        "low": 1,
        "none": 0,
    }

    score += completeness_scores.get(
        completeness,
        0,
    )

    # -----------------------------------------------------
    # Technical depth
    # -----------------------------------------------------

    technical_scores = {
        "high": 4,
        "medium": 3,
        "low": 1,
        "minimal": 0,
    }

    score += technical_scores.get(
        technical_depth,
        0,
    )

    # -----------------------------------------------------
    # Clarity
    # -----------------------------------------------------

    clarity_scores = {
        "good": 4,
        "moderate": 2,
        "needs_improvement": 1,
        "none": 0,
    }

    score += clarity_scores.get(
        clarity,
        0,
    )

    # -----------------------------------------------------
    # Vagueness penalty
    # -----------------------------------------------------

    if vagueness == "medium":
        score -= 1

    elif vagueness == "high":
        score -= 2

    score = max(
        0,
        min(score, 16)
    )

    percentage = round(
        (score / 16) * 100,
        2,
    )

    if percentage >= 80:
        level = "strong"

    elif percentage >= 60:
        level = "good"

    elif percentage >= 40:
        level = "moderate"

    else:
        level = "weak"

    return {
        "score": score,
        "percentage": percentage,
        "level": level,
    }


# =========================================================
# MAIN ANSWER ANALYZER
# =========================================================

def analyze_answer(
    question: str,
    answer: str,
) -> Dict:
    """
    Analyze one candidate answer.

    This is a deterministic baseline with
    contextual topic extraction.

    The returned dictionary intentionally exposes
    both detailed nested analysis and convenient
    top-level fields for the decision engine.
    """

    # -----------------------------------------------------
    # Basic analysis
    # -----------------------------------------------------

    length = calculate_answer_length(
        answer
    )

    relevance = calculate_relevance(
        question,
        answer,
    )

    technical_depth = (
        calculate_technical_depth(
            answer
        )
    )

    completeness = (
        calculate_completeness(
            answer
        )
    )

    clarity = calculate_clarity(
        answer
    )

    vagueness = detect_vagueness(
        answer
    )

    # -----------------------------------------------------
    # Topic extraction
    # -----------------------------------------------------

    answer_topics = detect_answer_topics(
        answer
    )

    # -----------------------------------------------------
    # Follow-up targets
    # -----------------------------------------------------

    followup_targets = (
        determine_followup_targets(
            answer_topics=answer_topics,
            technical_depth=technical_depth[
                "level"
            ],
            completeness=completeness[
                "level"
            ],
            answer_length=length[
                "length_level"
            ],
        )
    )

    # -----------------------------------------------------
    # Follow-up decision
    # -----------------------------------------------------

    followup = determine_followup(
        relevance["level"],
        completeness["level"],
        technical_depth["level"],
        vagueness["level"],
        length["length_level"],
        answer_topics,
    )

    # -----------------------------------------------------
    # Overall quality
    # -----------------------------------------------------

    overall = calculate_overall_quality(
        relevance["level"],
        completeness["level"],
        technical_depth["level"],
        clarity["level"],
        vagueness["level"],
    )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    result = {

        # -------------------------------------------------
        # Original information
        # -------------------------------------------------

        "question": question,

        "answer": answer,

        # -------------------------------------------------
        # Detailed analysis
        # -------------------------------------------------

        "answer_length": length,

        "relevance": relevance,

        "technical_depth": technical_depth,

        "completeness": completeness,

        "clarity": clarity,

        "vagueness": vagueness,

        "answer_topics": answer_topics,

        "follow_up_targets": followup_targets,

        "follow_up": followup,

        "overall_quality": overall,

        # -------------------------------------------------
        # IMPORTANT TOP-LEVEL FIELDS
        #
        # These are used by decision_engine.py
        # -------------------------------------------------

        "quality": overall["level"],

        "score": overall["percentage"],

        "needs_followup": followup[
            "needs_follow_up"
        ],

        "followup_action": followup[
            "action"
        ],

        "followup_reason": followup.get(
            "reason",
            "",
        ),

        "technical_depth_level": (
            technical_depth["level"]
        ),

        "completeness_level": (
            completeness["level"]
        ),

        "clarity_level": (
            clarity["level"]
        ),

        "vagueness_level": (
            vagueness["level"]
        ),
    }

    return result