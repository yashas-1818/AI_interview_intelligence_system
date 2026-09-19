"""
AI POWERED INTERVIEW INTELLIGENCE SYSTEM
Centralized Question Deduplication and Validation Engine

Enforces:
1. Exact and minor wording duplicate detection.
2. Paraphrased same-intent duplicate rejection.
3. Permitting multi-aspect follow-ups on the same topic (e.g. architecture vs. challenge vs. contribution).
4. Normalization and semantic intent extraction.
"""

import difflib
import re
from typing import Dict, List, Optional, Set, Tuple


# ======================================================================
# INTENT TAXONOMY
# ======================================================================

INTENT_PATTERNS: Dict[str, List[str]] = {
    "architecture": [
        r"\barchitectur\w*",
        r"\bdesign\b",
        r"\bstructur\w*",
        r"\bcomponents\b",
        r"\blayers\b",
        r"\bdata flow\b",
        r"\bhigh[- ]level\b",
    ],
    "contribution": [
        r"\bcontribution\w*",
        r"\byour role\b",
        r"\byour part\b",
        r"\bspecific contribution\b",
        r"\bwhat did you build\b",
        r"\bpersonal contribution\b",
    ],
    "challenge": [
        r"\bchalleng\w*",
        r"\bobstacle\w*",
        r"\bdifficult\w*",
        r"\bfaced\b",
        r"\bencounter\w*",
        r"\bbottleneck\w*",
        r"\bstruggle\w*",
        r"\bbug\w*",
    ],
    "decision_tradeoff": [
        r"\bwhy (?:did you )?choose\b",
        r"\btrade[- ]?off\w*",
        r"\bdecision\w*",
        r"\balternative\w*",
        r"\brationale\b",
    ],
    "testing_evaluation": [
        r"\bevaluat\w*",
        r"\btest(?:ing)?\b",
        r"\bmetric\w*",
        r"\baccuracy\b",
        r"\bvalidat\w*",
        r"\bbenchmark\w*",
    ],
    "deployment_production": [
        r"\bdeploy\w*",
        r"\bproduction\b",
        r"\bmonitor\w*",
        r"\blatency\b",
        r"\bscal\w*",
        r"\bdrift\b",
    ],
    "learning_gap": [
        r"\blearn\w*",
        r"\bget started\b",
        r"\bfamiliar\w*",
        r"\bhow would you approach learning\b",
        r"\bnot used\b",
    ],
    "intro_background": [
        r"\bintroduc\w*",
        r"\bbackground\b",
        r"\byourself\b",
    ],
    "closing": [
        r"\bhighlight\b",
        r"\bquestions for\b",
        r"\banything else\b",
        r"\bconclude\b",
    ],
}

# Conversational filler phrases to strip
CONVERSATIONAL_FILLERS = [
    r"^could you briefly\b",
    r"^could you please\b",
    r"^could you\b",
    r"^can you please\b",
    r"^can you\b",
    r"^would you please\b",
    r"^would you\b",
    r"^please\b",
    r"^tell me about\b",
    r"^walk me through\b",
    r"^explain to me\b",
    r"^explain\b",
    r"^describe\b",
    r"^suppose you are given\b",
    r"^suppose you had to\b",
    r"^suppose you\b",
    r"^imagine you\b",
    r"^what was your\b",
    r"^what is your\b",
    r"^what are some\b",
    r"^what were the\b",
    r"^what\b",
    r"^how did you\b",
    r"^how would you\b",
    r"^how\b",
]

STOPWORDS = {
    "a", "an", "the", "and", "or", "to", "of", "in", "on", "at", "by", "for",
    "with", "from", "your", "my", "this", "that", "these", "those", "is", "are",
    "was", "were", "did", "do", "does", "have", "has", "had", "when", "while",
    "some", "one", "be", "being", "been", "using", "use", "used", "work", "worked",
    "working", "project", "skill", "candidate", "role", "experience",
}


# ======================================================================
# NORMALIZATION & INTENT EXTRACTION
# ======================================================================

def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, and collapse whitespace."""
    if not text:
        return ""
    cleaned = text.lower().strip()
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def strip_conversational_fillers(text: str) -> str:
    """Strip introductory conversational phrases."""
    cleaned = normalize_text(text)
    for pattern in CONVERSATIONAL_FILLERS:
        cleaned = re.sub(pattern, "", cleaned).strip()
    return cleaned


def extract_content_tokens(text: str) -> Set[str]:
    """Extract informative non-stopword tokens."""
    cleaned = strip_conversational_fillers(text)
    tokens = cleaned.split()
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def detect_intents(text: str) -> Set[str]:
    """Detect all intent categories present in the question."""
    lower = text.lower()
    intents = set()
    for intent_name, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, lower):
                intents.add(intent_name)
                break
    return intents


def extract_entities(text: str, known_entities: Optional[List[str]] = None) -> Set[str]:
    """
    Extract key subject entities (e.g. project names like Skylark,
    tech like Python, PyTorch, Docker).
    """
    lower = text.lower()
    entities = set()
    
    # Common tech/project tokens
    common_entities = [
        "skylark", "python", "pytorch", "tensorflow", "docker", "fastapi",
        "sql", "nlp", "machine learning", "pandas", "numpy", "api", "rest",
        "postgres", "mysql", "mongodb", "aws", "gcp", "azure", "git",
    ]
    all_known = set(common_entities)
    if known_entities:
        for ent in known_entities:
            all_known.add(ent.lower().strip())
            
    for ent in all_known:
        if re.search(r"\b" + re.escape(ent) + r"\b", lower):
            entities.add(ent)
            
    return entities


# ======================================================================
# CORE SIMILARITY & DUPLICATE CHECKER
# ======================================================================

def are_questions_similar(
    q1: str,
    q2: str,
    known_entities: Optional[List[str]] = None,
    similarity_threshold: float = 0.75,
) -> Tuple[bool, str]:
    """
    Determines whether q1 and q2 are duplicates.
    
    Returns:
        (is_duplicate, reason)
    """
    norm1 = normalize_text(q1)
    norm2 = normalize_text(q2)

    # 1. Exact string match
    if norm1 == norm2:
        return True, "Exact normalized match"

    # 2. Filler-stripped match
    clean1 = strip_conversational_fillers(q1)
    clean2 = strip_conversational_fillers(q2)
    if clean1 and clean2 and clean1 == clean2:
        return True, "Identical content after removing conversational fillers"

    # 3. Content tokens and intent comparison
    tokens1 = extract_content_tokens(q1)
    tokens2 = extract_content_tokens(q2)

    # Jaccard similarity of content tokens
    if tokens1 and tokens2:
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        jaccard = len(intersection) / len(union)
        if jaccard >= 0.75:
            return True, f"High token overlap ({jaccard:.2f})"

    # Sequence similarity of cleaned text
    seq_ratio = difflib.SequenceMatcher(None, clean1, clean2).ratio()
    if seq_ratio >= similarity_threshold:
        return True, f"High sequence similarity ({seq_ratio:.2f})"

    # 4. Entity & Intent Intersection
    entities1 = extract_entities(q1, known_entities)
    entities2 = extract_entities(q2, known_entities)
    shared_entities = entities1.intersection(entities2)

    intents1 = detect_intents(q1)
    intents2 = detect_intents(q2)
    shared_intents = intents1.intersection(intents2)

    # If both questions share an entity AND share the same question intent
    # e.g. both ask about the "challenges" of "python"
    if shared_entities and shared_intents:
        # Check if they also share significant core tokens
        if tokens1 and tokens2 and len(tokens1.intersection(tokens2)) >= 1:
            return True, f"Shared entity ({', '.join(shared_entities)}) and shared intent ({', '.join(shared_intents)})"

    return False, "Distinct questions"


# ======================================================================
# CENTRALIZED VALIDATION INTERFACE
# ======================================================================

class QuestionValidator:
    """
    Centralized validation engine that ensures every question generated
    in an interview session is novel and non-repetitive.
    """

    def __init__(self, known_entities: Optional[List[str]] = None):
        self.known_entities = list(known_entities or [])
        self.asked_questions: List[str] = []
        self.skipped_questions: List[str] = []

    def register_known_entities(self, entities: List[str]):
        for e in entities:
            if e and e not in self.known_entities:
                self.known_entities.append(e)

    def register_entities(
        self,
        projects: Optional[List[str]] = None,
        skills: Optional[List[str]] = None,
        entities: Optional[List[str]] = None,
    ):
        """Register project names, skills, and entity keywords into known_entities."""
        all_items: List[str] = []
        if projects:
            all_items.extend(projects)
        if skills:
            all_items.extend(skills)
        if entities:
            all_items.extend(entities)
        self.register_known_entities(all_items)

    def check_duplicate(
        self,
        candidate_question: str,
        threshold: float = 0.75,
    ) -> Tuple[bool, Optional[str], str]:
        """
        Detailed duplicate check returning (is_duplicate, matching_prior_question, reason).
        """
        if not candidate_question or not candidate_question.strip():
            return True, None, "Empty question"

        cand_clean = candidate_question.strip()

        # Check against all previously asked and skipped questions
        all_prior = self.asked_questions + self.skipped_questions

        for prior_q in all_prior:
            dup, reason = are_questions_similar(
                cand_clean,
                prior_q,
                known_entities=self.known_entities,
                similarity_threshold=threshold,
            )
            if dup:
                return True, prior_q, reason

        return False, None, "Unique question"

    def is_duplicate(
        self,
        candidate_question: str,
        category: Optional[str] = None,
        threshold: float = 0.75,
    ) -> bool:
        """
        Returns True if candidate_question duplicates any asked or skipped question,
        False otherwise.
        """
        is_dup, _, _ = self.check_duplicate(candidate_question, threshold=threshold)
        return is_dup

    def record_question(self, question: str, category: Optional[str] = None):
        """Record a question as accepted and asked."""
        if question and question.strip() not in self.asked_questions:
            self.asked_questions.append(question.strip())

    def record_skip(self, question: str, category: Optional[str] = None):
        """Record a question as consumed/skipped."""
        if question and question.strip() not in self.skipped_questions:
            self.skipped_questions.append(question.strip())
        if question and question.strip() not in self.asked_questions:
            self.asked_questions.append(question.strip())
