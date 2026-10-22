"""
Filler Word and Discourse Marker Lexicon.

Provides categorized collections of hesitation sounds, filler phrases,
and discourse markers used for objective speech-delivery analytics.

All matching is token-bounded. Context-sensitive words like "like" are
handled conservatively to avoid misclassifying grammatical usage.
"""

from typing import FrozenSet, Tuple, Optional


# =====================================================================
# 1. UNAMBIGUOUS HESITATION SOUNDS
# Words that almost exclusively function as vocalized pauses / hesitations.
# =====================================================================

UNAMBIGUOUS_FILLERS: FrozenSet[str] = frozenset({
    "um",
    "uh",
    "er",
    "ah",
    "erm",
    "uhm",
    "hmm",
})


# =====================================================================
# 2. MULTI-WORD FILLER PHRASES
# Multi-token expressions commonly used as hesitation or filler devices.
# Ordered by token length descending during matching.
# =====================================================================

MULTI_WORD_FILLERS: Tuple[str, ...] = (
    "at the end of the day",
    "you know what i mean",
    "you know",
    "i mean",
    "sort of",
    "kind of",
    "as in",
)


# =====================================================================
# 3. DISCOURSE MARKERS (SINGLE WORD)
# Words that frequently serve as discourse padding rather than semantic content.
# =====================================================================

DISCOURSE_MARKERS: FrozenSet[str] = frozenset({
    "basically",
    "actually",
    "literally",
    "honestly",
})


# =====================================================================
# 4. CONTEXT-SENSITIVE FILLERS
# Words that can be grammatical (preposition, verb) or filler depending on context.
# =====================================================================

CONTEXT_SENSITIVE_FILLERS: FrozenSet[str] = frozenset({
    "like",
})


# Words immediately preceding "like" that strongly indicate grammatical usage
# (verbs, modals, pronouns, comparative markers).
LIKE_GRAMMATICAL_PRECEDING_WORDS: FrozenSet[str] = frozenset({
    # Subject pronouns
    "i",
    "we",
    "they",
    "you",
    "he",
    "she",
    "it",
    "who",
    # Modals / auxiliaries
    "would",
    "could",
    "should",
    "will",
    "might",
    "must",
    "can",
    "do",
    "does",
    "did",
    "dont",
    "don't",
    "didnt",
    "didn't",
    "doesnt",
    "doesn't",
    # Sensory & comparative verbs / markers
    "feel",
    "feels",
    "felt",
    "feeling",
    "look",
    "looks",
    "looked",
    "looking",
    "sound",
    "sounds",
    "sounded",
    "sounding",
    "seem",
    "seems",
    "seemed",
    "seeming",
    "taste",
    "tastes",
    "smell",
    "smells",
    # Quantifiers & qualifiers
    "something",
    "anything",
    "nothing",
    "everything",
    "much",
    "more",
    "such",
    "just",
    "act",
    "acts",
    "acting",
    "acted",
})


def is_conservative_filler_like(preceding_word: Optional[str]) -> bool:
    """
    Determine if an occurrence of 'like' is conservatively a filler.

    If preceded by a grammatical trigger (e.g. 'I like', 'would like',
    'feels like', 'such like', 'something like'), it is considered
    grammatical and NOT a filler.

    Only considered a filler when preceding context is absent, a pause/hesitation,
    or not one of the grammatical triggers.
    """
    if not preceding_word:
        return True

    clean_preceding = preceding_word.lower().strip(".,!?;:\"'()[]{}")
    if clean_preceding in LIKE_GRAMMATICAL_PRECEDING_WORDS:
        return False

    return True
