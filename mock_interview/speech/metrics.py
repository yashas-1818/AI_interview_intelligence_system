"""
Deterministic Speech and Transcript Metrics.

Provides mathematical and string analysis functions for:
- Token-bounded word counting
- Substring-safe filler word and phrase detection
- Filler percentage calculation
- Answer duration and speaking pace (Words Per Minute)
- Audio-verified pause metrics extraction (never inferred from text)

All functions are pure, deterministic, and safe against ZeroDivisionError,
None values, corrupt types, and negative inputs.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple

from mock_interview.speech.filler_lexicon import (
    CONTEXT_SENSITIVE_FILLERS,
    DISCOURSE_MARKERS,
    MULTI_WORD_FILLERS,
    UNAMBIGUOUS_FILLERS,
    is_conservative_filler_like,
)


# Token regex for words (supports alphanumeric words and simple contractions like "I'm", "don't")
WORD_TOKEN_PATTERN = re.compile(r"\b[a-zA-Z0-9]+(?:'[a-zA-Z0-9]+)?\b")


def count_words(text: Optional[str]) -> int:
    """
    Count the number of complete word tokens in a text string.

    Returns 0 for None, empty strings, whitespace, or strings with no alphanumeric tokens.
    Never raises an exception on malformed inputs.
    """
    if not text or not isinstance(text, str):
        return 0

    tokens = WORD_TOKEN_PATTERN.findall(text)
    return len(tokens)


def find_filler_words(
    text: Optional[str],
    conservative_like: bool = True,
) -> Dict[str, Any]:
    """
    Detect filler words and phrases using token-boundary matching.

    Ensures:
    - Multi-word phrases (e.g. 'you know', 'sort of') are matched first.
    - Substring false positives are impossible (e.g. 'umbrella' != 'um',
      'error' != 'er', 'ahead' != 'ah', 'likely' != 'like', 'solution' != 'so').
    - Contextual 'like' is evaluated conservatively to protect grammatical uses.

    Returns:
        Dict containing:
        - "total_count": int
        - "breakdown": Dict[str, int]
        - "by_category": Dict[str, int]
        - "matches": List[Dict[str, Any]] (token, start, end, category)
    """
    empty_result: Dict[str, Any] = {
        "total_count": 0,
        "breakdown": {},
        "by_category": {
            "unambiguous": 0,
            "phrases": 0,
            "discourse": 0,
            "contextual": 0,
        },
        "matches": [],
    }

    if not text or not isinstance(text, str) or not text.strip():
        return empty_result

    breakdown: Dict[str, int] = {}
    by_category: Dict[str, int] = {
        "unambiguous": 0,
        "phrases": 0,
        "discourse": 0,
        "contextual": 0,
    }
    matches: List[Dict[str, Any]] = []
    occupied_indices: set = set()

    # 1. Match multi-word filler phrases first
    for phrase in MULTI_WORD_FILLERS:
        words = phrase.split()
        phrase_regex = re.compile(
            r"\b" + r"\s+".join(re.escape(w) for w in words) + r"\b",
            re.IGNORECASE,
        )
        for m in phrase_regex.finditer(text):
            span_indices = set(range(m.start(), m.end()))
            # Avoid overlapping previously matched multi-word phrases
            if span_indices & occupied_indices:
                continue

            occupied_indices.update(span_indices)
            canonical = phrase.lower()
            breakdown[canonical] = breakdown.get(canonical, 0) + 1
            by_category["phrases"] += 1
            matches.append({
                "filler": canonical,
                "start": m.start(),
                "end": m.end(),
                "category": "phrase",
            })

    # 2. Extract single-word tokens and check unambiguous, discourse, and contextual fillers
    all_word_matches: List[re.Match] = list(WORD_TOKEN_PATTERN.finditer(text))

    for idx, match in enumerate(all_word_matches):
        span_indices = set(range(match.start(), match.end()))
        if span_indices & occupied_indices:
            continue

        raw_word = match.group(0).lower()

        # A. Unambiguous hesitation sounds ('um', 'uh', 'er', etc.)
        if raw_word in UNAMBIGUOUS_FILLERS:
            breakdown[raw_word] = breakdown.get(raw_word, 0) + 1
            by_category["unambiguous"] += 1
            occupied_indices.update(span_indices)
            matches.append({
                "filler": raw_word,
                "start": match.start(),
                "end": match.end(),
                "category": "unambiguous",
            })
            continue

        # B. Single-word discourse markers ('basically', 'actually', etc.)
        if raw_word in DISCOURSE_MARKERS:
            breakdown[raw_word] = breakdown.get(raw_word, 0) + 1
            by_category["discourse"] += 1
            occupied_indices.update(span_indices)
            matches.append({
                "filler": raw_word,
                "start": match.start(),
                "end": match.end(),
                "category": "discourse",
            })
            continue

        # C. Context-sensitive fillers ('like')
        if raw_word in CONTEXT_SENSITIVE_FILLERS:
            is_filler = True
            if conservative_like:
                preceding_token = (
                    all_word_matches[idx - 1].group(0) if idx > 0 else None
                )
                is_filler = is_conservative_filler_like(preceding_token)

            if is_filler:
                breakdown[raw_word] = breakdown.get(raw_word, 0) + 1
                by_category["contextual"] += 1
                occupied_indices.update(span_indices)
                matches.append({
                    "filler": raw_word,
                    "start": match.start(),
                    "end": match.end(),
                    "category": "contextual",
                })

    # Sort matches chronologically by start position
    matches.sort(key=lambda item: item["start"])

    return {
        "total_count": sum(breakdown.values()),
        "breakdown": breakdown,
        "by_category": by_category,
        "matches": matches,
    }


def calculate_filler_rate(filler_count: int, word_count: int) -> float:
    """
    Calculate the filler rate as a percentage of total words.

    Returns:
        float percentage rounded to 2 decimal places (e.g. 4.50 for 4.5%).
        Returns 0.0 if word_count <= 0 or filler_count <= 0.
    """
    if not isinstance(filler_count, (int, float)) or not isinstance(word_count, (int, float)):
        return 0.0

    if word_count <= 0 or filler_count <= 0:
        return 0.0

    rate = (float(filler_count) / float(word_count)) * 100.0
    return round(rate, 2)


def calculate_duration_seconds(telemetry: Optional[Dict[str, Any]]) -> Optional[float]:
    """
    Safely extract and compute answer duration in seconds from telemetry data.

    Accepts:
    - telemetry['duration_ms'] directly
    - or (telemetry['end_time_ms'] - telemetry['start_time_ms'])

    Returns:
        float rounded to 2 decimal places, or None if timing is missing or invalid.
    """
    if not telemetry or not isinstance(telemetry, dict):
        return None

    # Check for direct duration_ms
    raw_duration = telemetry.get("duration_ms")
    if raw_duration is not None:
        try:
            val = float(raw_duration)
            if not math.isnan(val) and not math.isinf(val) and val >= 0.0:
                return round(val / 1000.0, 2)
        except (ValueError, TypeError):
            pass

    # Check for start and end timestamps
    start_time = telemetry.get("start_time_ms")
    end_time = telemetry.get("end_time_ms")
    if start_time is not None and end_time is not None:
        try:
            start_val = float(start_time)
            end_val = float(end_time)
            if not math.isnan(start_val) and not math.isnan(end_val):
                diff = end_val - start_val
                if diff >= 0.0:
                    return round(diff / 1000.0, 2)
        except (ValueError, TypeError):
            pass

    return None


def calculate_speaking_pace(
    word_count: int,
    duration_seconds: Optional[float],
    min_duration_sec: float = 1.0,
) -> Optional[float]:
    """
    Calculate speaking pace in Words Per Minute (WPM).

    Pace requires a reliable duration >= min_duration_sec.
    If duration is None, <= 0, or < min_duration_sec, returns None
    because sub-second durations cannot provide a reliable WPM estimate.

    Returns:
        float rounded to 1 decimal place (e.g. 135.2), or None if pace cannot be reliably measured.
    """
    if duration_seconds is None or not isinstance(duration_seconds, (int, float)):
        return None

    if math.isnan(duration_seconds) or math.isinf(duration_seconds):
        return None

    if duration_seconds < min_duration_sec:
        return None

    if not isinstance(word_count, (int, float)) or word_count < 0:
        clean_word_count = 0
    else:
        clean_word_count = int(word_count)

    pace = (float(clean_word_count) / float(duration_seconds)) * 60.0
    return round(pace, 1)


def extract_pause_metrics(telemetry: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract audio-verified pause metrics from telemetry.

    CRITICAL RULE:
    Pauses are NEVER inferred from transcript text, punctuation, or sentence boundaries.
    If audio timing data is absent, pause metrics are explicitly marked 'unavailable'.

    Returns:
        Dict containing:
        - "status": "measured" | "unavailable"
        - "reliability": "high" | "none"
        - "pause_count": Optional[int]
        - "total_pause_duration_sec": Optional[float]
        - "active_speech_duration_sec": Optional[float]
        - "pause_events": List[Dict[str, Any]]
        - "details": str
    """
    if not telemetry or not isinstance(telemetry, dict):
        return {
            "status": "unavailable",
            "reliability": "none",
            "pause_count": None,
            "total_pause_duration_sec": None,
            "active_speech_duration_sec": None,
            "pause_events": [],
            "details": "Audio timing telemetry is not provided; pauses are never estimated from transcript text.",
        }

    # Audio pause data indicators
    raw_pause_count = telemetry.get("pause_count")
    raw_silence_ms = telemetry.get("silence_duration_ms")
    raw_speech_ms = telemetry.get("speech_duration_ms")
    raw_pause_events = telemetry.get("pause_events")

    # If no audio timing fields are present, report unavailable
    if (
        raw_pause_count is None
        and raw_silence_ms is None
        and raw_speech_ms is None
        and not raw_pause_events
    ):
        return {
            "status": "unavailable",
            "reliability": "none",
            "pause_count": None,
            "total_pause_duration_sec": None,
            "active_speech_duration_sec": None,
            "pause_events": [],
            "details": "No audio pause events or silence durations were recorded in telemetry.",
        }

    # Safely parse pause count
    pause_count: Optional[int] = None
    if raw_pause_count is not None:
        try:
            val_int = int(raw_pause_count)
            if val_int >= 0:
                pause_count = val_int
        except (ValueError, TypeError):
            pass

    # Safely parse silence duration
    total_pause_duration_sec: Optional[float] = None
    if raw_silence_ms is not None:
        try:
            silence_val = float(raw_silence_ms)
            if not math.isnan(silence_val) and silence_val >= 0.0:
                total_pause_duration_sec = round(silence_val / 1000.0, 2)
        except (ValueError, TypeError):
            pass

    # Safely parse active speech duration
    active_speech_sec: Optional[float] = None
    if raw_speech_ms is not None:
        try:
            speech_val = float(raw_speech_ms)
            if not math.isnan(speech_val) and speech_val >= 0.0:
                active_speech_sec = round(speech_val / 1000.0, 2)
        except (ValueError, TypeError):
            pass

    # Safely sanitize pause events list
    clean_events: List[Dict[str, Any]] = []
    if isinstance(raw_pause_events, list):
        for event in raw_pause_events:
            if isinstance(event, dict):
                clean_events.append(dict(event))

    # If pause count wasn't explicitly set but events list was provided, derive count
    if pause_count is None and clean_events:
        pause_count = len(clean_events)

    return {
        "status": "measured",
        "reliability": "high",
        "pause_count": pause_count if pause_count is not None else 0,
        "total_pause_duration_sec": total_pause_duration_sec,
        "active_speech_duration_sec": active_speech_sec,
        "pause_events": clean_events,
        "details": "Measured from audio telemetry events.",
    }


def validate_and_sanitize_telemetry(
    raw_telemetry: Any,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """
    Safely validate and sanitize incoming speech timing telemetry.

    Ensures:
    - Telemetry payload is a dictionary (or None).
    - Numeric fields are finite, non-NaN, and non-negative.
    - Timestamp consistency (end_time_ms >= start_time_ms).
    - pause_count is a non-negative integer.
    - Does not throw exceptions on unexpected types or corrupt structures.

    Returns:
        Tuple of (sanitized_telemetry_dict, list_of_validation_errors).
        If raw_telemetry is None, returns (None, []).
    """
    if raw_telemetry is None:
        return None, []

    if not isinstance(raw_telemetry, dict):
        return None, ["Telemetry payload must be a key-value object."]

    errors: List[str] = []
    sanitized: Dict[str, Any] = {}

    def _validate_non_negative_float(key: str) -> Optional[float]:
        val = raw_telemetry.get(key)
        if val is None:
            return None
        try:
            float_val = float(val)
            if math.isnan(float_val) or math.isinf(float_val):
                errors.append(f"Field '{key}' must be a finite number.")
                return None
            if float_val < 0.0:
                errors.append(f"Field '{key}' cannot be negative (got {float_val}).")
                return None
            return float_val
        except (ValueError, TypeError):
            errors.append(f"Field '{key}' must be numeric.")
            return None

    # Validate timing numbers
    for float_field in ("duration_ms", "speech_duration_ms", "silence_duration_ms"):
        if float_field in raw_telemetry:
            clean_val = _validate_non_negative_float(float_field)
            if clean_val is not None:
                sanitized[float_field] = clean_val

    # Validate start/end timestamps
    start_time = None
    end_time = None
    if "start_time_ms" in raw_telemetry:
        start_time = _validate_non_negative_float("start_time_ms")
        if start_time is not None:
            sanitized["start_time_ms"] = start_time

    if "end_time_ms" in raw_telemetry:
        end_time = _validate_non_negative_float("end_time_ms")
        if end_time is not None:
            sanitized["end_time_ms"] = end_time

    if start_time is not None and end_time is not None:
        if end_time < start_time:
            errors.append(
                f"end_time_ms ({end_time}) cannot be earlier than start_time_ms ({start_time})."
            )

    # Validate pause_count
    if "pause_count" in raw_telemetry:
        raw_pc = raw_telemetry.get("pause_count")
        if raw_pc is not None:
            try:
                pc_int = int(raw_pc)
                if pc_int < 0:
                    errors.append(f"pause_count cannot be negative (got {pc_int}).")
                else:
                    sanitized["pause_count"] = pc_int
            except (ValueError, TypeError):
                errors.append("pause_count must be an integer.")

    # Validate pause_events
    if "pause_events" in raw_telemetry:
        raw_events = raw_telemetry.get("pause_events")
        if isinstance(raw_events, list):
            clean_events = []
            for ev in raw_events:
                if isinstance(ev, dict):
                    clean_events.append(dict(ev))
            sanitized["pause_events"] = clean_events
        elif raw_events is not None:
            errors.append("pause_events must be a list of event objects.")

    # Pass through optional speech segments if valid list
    if "speech_segments" in raw_telemetry:
        raw_segments = raw_telemetry.get("speech_segments")
        if isinstance(raw_segments, list):
            clean_segments = []
            for seg in raw_segments:
                if isinstance(seg, dict):
                    clean_segments.append(dict(seg))
            sanitized["speech_segments"] = clean_segments
        elif raw_segments is not None:
            errors.append("speech_segments must be a list of segment objects.")

    return (sanitized if not errors else sanitized), errors

