"""
Unit Tests for Speech Delivery Analytics.

Tests:
1. Deterministic word counting across punctuation and contractions.
2. Filler word and phrase detection with token boundaries.
3. Substring false-positive protection (umbrella, error, ahead, likely, etc.).
4. Conservative handling of grammatical 'like'.
5. Safe calculation of filler rates without ZeroDivisionError.
6. Duration and speaking pace (WPM) calculations with validation thresholds.
7. Strict pause metrics isolation (never inferred from text/punctuation).
8. Full session roll-up and neutral observations.
9. JSON serializability of all outputs.
"""

import json
import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path when executed directly
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mock_interview.speech.analyzer import (
    SessionSpeechAnalytics,
    SpeechDeliveryAnalyzer,
    SpeechMetricValue,
    TurnSpeechAnalytics,
)
from mock_interview.speech.metrics import (
    calculate_duration_seconds,
    calculate_filler_rate,
    calculate_speaking_pace,
    count_words,
    extract_pause_metrics,
    find_filler_words,
)


class TestWordCounting(unittest.TestCase):
    """Test token-bounded word counting."""

    def test_standard_sentences(self):
        self.assertEqual(count_words("I am a software engineer."), 5)
        self.assertEqual(
            count_words("FastAPI and Python provide high performance for backend APIs."),
            9,
        )

    def test_contractions_and_alphanumerics(self):
        # "I'm" counts as 1 word, "don't" as 1 word, "Python3" as 1 word
        text = "I'm sure we don't need Python3 here."
        self.assertEqual(count_words(text), 7)

    def test_heavy_punctuation(self):
        text = "Hello, world! (Is this working? Yes... it is: 100%.)"
        words = count_words(text)
        # Hello(1), world(2), Is(3), this(4), working(5), Yes(6), it(7), is(8), 100(9)
        self.assertEqual(words, 9)

    def test_empty_and_edge_cases(self):
        self.assertEqual(count_words(""), 0)
        self.assertEqual(count_words("   \t\n  "), 0)
        self.assertEqual(count_words(None), 0)
        self.assertEqual(count_words("...,,, --- ???"), 0)


class TestFillerDetection(unittest.TestCase):
    """Test token-boundary filler matching and substring protection."""

    def test_unambiguous_hesitations(self):
        text = "Um, I think uh maybe we should er try hmm this."
        result = find_filler_words(text)
        self.assertIn("um", result["breakdown"])
        self.assertIn("uh", result["breakdown"])
        self.assertIn("er", result["breakdown"])
        self.assertIn("hmm", result["breakdown"])
        self.assertEqual(result["breakdown"]["um"], 1)
        self.assertEqual(result["breakdown"]["uh"], 1)

    def test_multi_word_phrases(self):
        text = "We designed the database, you know, sort of like a graph, at the end of the day."
        result = find_filler_words(text)
        self.assertIn("you know", result["breakdown"])
        self.assertIn("sort of", result["breakdown"])
        self.assertIn("at the end of the day", result["breakdown"])
        self.assertEqual(result["breakdown"]["you know"], 1)
        self.assertEqual(result["breakdown"]["sort of"], 1)

    def test_discourse_markers(self):
        text = "Basically, we actually used Redis for caching."
        result = find_filler_words(text)
        self.assertIn("basically", result["breakdown"])
        self.assertIn("actually", result["breakdown"])
        self.assertEqual(result["breakdown"]["basically"], 1)
        self.assertEqual(result["breakdown"]["actually"], 1)

    def test_substring_false_positive_immunity(self):
        """
        CRITICAL: Words that contain filler letters as substrings
        MUST NOT be matched as filler words.
        """
        tricky_text = (
            "The umbrella had an error when ahead of the welcome ceremony. "
            "It was likely a solution that would resemble another approach."
        )
        result = find_filler_words(tricky_text)
        # 'umbrella' must not trigger 'um'
        # 'error' must not trigger 'er'
        # 'ahead' must not trigger 'ah'
        # 'welcome' must not trigger 'well'
        # 'likely' must not trigger 'like'
        # 'solution' must not trigger 'so'
        # 'resemble' must not trigger 'um'
        self.assertEqual(result["total_count"], 0)
        self.assertEqual(result["breakdown"], {})

    def test_conservative_like_grammatical(self):
        """
        Verify that grammatical uses of 'like' are NOT counted as fillers.
        """
        grammatical_cases = [
            "I like Python and distributed systems.",
            "We would like to deploy on Kubernetes.",
            "It felt like an optimal database structure.",
            "This sounds like a viable alternative.",
            "They seem like competent engineers.",
            "Tools such like Docker and Git.",
            "Something like a message broker.",
        ]
        for sentence in grammatical_cases:
            result = find_filler_words(sentence, conservative_like=True)
            self.assertEqual(
                result["total_count"],
                0,
                f"Failed on grammatical sentence: '{sentence}'",
            )

    def test_conservative_like_filler_usage(self):
        """
        Verify that isolated or hesitation 'like' IS counted as a filler.
        """
        text = "Um, like, the microservice was struggling."
        result = find_filler_words(text, conservative_like=True)
        self.assertIn("um", result["breakdown"])
        self.assertIn("like", result["breakdown"])


class TestFillerRateCalculation(unittest.TestCase):
    """Test filler rate percentage and safety guards."""

    def test_standard_rates(self):
        # 5 fillers in 100 words = 5.0%
        self.assertEqual(calculate_filler_rate(5, 100), 5.0)
        # 1 filler in 3 words = 33.33%
        self.assertEqual(calculate_filler_rate(1, 3), 33.33)
        # 0 fillers in 50 words = 0.0%
        self.assertEqual(calculate_filler_rate(0, 50), 0.0)

    def test_zero_and_negative_guards(self):
        # 0 words must not cause ZeroDivisionError
        self.assertEqual(calculate_filler_rate(0, 0), 0.0)
        self.assertEqual(calculate_filler_rate(5, 0), 0.0)
        self.assertEqual(calculate_filler_rate(-1, 50), 0.0)
        self.assertEqual(calculate_filler_rate(2, -10), 0.0)


class TestDurationAndSpeakingPace(unittest.TestCase):
    """Test duration and WPM pace calculations."""

    def test_duration_from_ms(self):
        telemetry = {"duration_ms": 15400}
        self.assertEqual(calculate_duration_seconds(telemetry), 15.4)

    def test_duration_from_start_end(self):
        telemetry = {"start_time_ms": 10000, "end_time_ms": 25500}
        self.assertEqual(calculate_duration_seconds(telemetry), 15.5)

    def test_duration_invalid_and_missing(self):
        self.assertIsNone(calculate_duration_seconds(None))
        self.assertIsNone(calculate_duration_seconds({}))
        self.assertIsNone(calculate_duration_seconds({"duration_ms": "invalid"}))
        self.assertIsNone(calculate_duration_seconds({"duration_ms": -500}))
        self.assertIsNone(calculate_duration_seconds({"start_time_ms": 500, "end_time_ms": 200}))

    def test_speaking_pace_standard(self):
        # 150 words in 60s = 150.0 WPM
        self.assertEqual(calculate_speaking_pace(150, 60.0), 150.0)
        # 75 words in 30s = 150.0 WPM
        self.assertEqual(calculate_speaking_pace(75, 30.0), 150.0)
        # 45 words in 20s = 135.0 WPM
        self.assertEqual(calculate_speaking_pace(45, 20.0), 135.0)

    def test_speaking_pace_threshold_guards(self):
        # Under 1.0 second cannot give reliable WPM
        self.assertIsNone(calculate_speaking_pace(2, 0.5))
        self.assertIsNone(calculate_speaking_pace(10, 0.0))
        self.assertIsNone(calculate_speaking_pace(10, None))
        self.assertIsNone(calculate_speaking_pace(10, -5.0))


class TestPauseMetricsStrictness(unittest.TestCase):
    """
    Ensure pauses are NEVER inferred from text/punctuation alone,
    and only reported when verified audio telemetry is supplied.
    """

    def test_no_telemetry_means_unavailable_pauses(self):
        # Text has tons of commas and pauses in punctuation
        text = "Well... um, let's see, uh... wait! Let me think... okay."
        # Without audio telemetry, pause metrics MUST be unavailable
        metrics = extract_pause_metrics(None)
        self.assertEqual(metrics["status"], "unavailable")
        self.assertIsNone(metrics["pause_count"])
        self.assertIsNone(metrics["total_pause_duration_sec"])

    def test_verified_audio_telemetry_pauses(self):
        telemetry = {
            "pause_count": 3,
            "silence_duration_ms": 4200,
            "speech_duration_ms": 15800,
            "pause_events": [
                {"start_ms": 2000, "end_ms": 3400, "duration_ms": 1400},
                {"start_ms": 7000, "end_ms": 8500, "duration_ms": 1500},
                {"start_ms": 12000, "end_ms": 13300, "duration_ms": 1300},
            ],
        }
        metrics = extract_pause_metrics(telemetry)
        self.assertEqual(metrics["status"], "measured")
        self.assertEqual(metrics["reliability"], "high")
        self.assertEqual(metrics["pause_count"], 3)
        self.assertEqual(metrics["total_pause_duration_sec"], 4.2)
        self.assertEqual(metrics["active_speech_duration_sec"], 15.8)
        self.assertEqual(len(metrics["pause_events"]), 3)


class TestSpeechDeliveryAnalyzer(unittest.TestCase):
    """Test TurnSpeechAnalytics and SessionSpeechAnalytics."""

    def setUp(self):
        self.analyzer = SpeechDeliveryAnalyzer(conservative_like=True)

    def test_turn_analysis_full(self):
        transcript = "Um, I used FastAPI basically because it offers asynchronous request handling."
        telemetry = {
            "duration_ms": 5000,
            "pause_count": 1,
            "silence_duration_ms": 1000,
            "speech_duration_ms": 4000,
        }
        turn = self.analyzer.analyze_turn(transcript, telemetry, turn_id="turn_1")

        self.assertEqual(turn.turn_id, "turn_1")
        self.assertEqual(turn.telemetry_status, "full")
        self.assertEqual(turn.transcript_metrics["word_count"].value, 11)
        self.assertEqual(turn.transcript_metrics["filler_count"].value, 2)  # 'um' and 'basically'
        self.assertEqual(turn.timing_metrics["answer_duration_sec"].value, 5.0)
        self.assertEqual(turn.timing_metrics["pause_count"].value, 1)
        self.assertEqual(turn.timing_metrics["pause_count"].status, "measured")

    def test_turn_analysis_transcript_only(self):
        transcript = "We scaled the database using read replicas and sharding."
        turn = self.analyzer.analyze_turn(transcript, telemetry=None, turn_id="turn_2")

        self.assertEqual(turn.telemetry_status, "transcript_only")
        self.assertEqual(turn.transcript_metrics["word_count"].value, 9)
        self.assertEqual(turn.timing_metrics["answer_duration_sec"].status, "unavailable")
        self.assertEqual(turn.timing_metrics["speaking_pace_wpm"].status, "unavailable")
        self.assertEqual(turn.timing_metrics["pause_count"].status, "unavailable")

    def test_turn_analysis_empty_answer(self):
        turn = self.analyzer.analyze_turn("", telemetry=None, turn_id="turn_empty")
        self.assertEqual(turn.telemetry_status, "empty_answer")
        self.assertEqual(turn.transcript_metrics["word_count"].value, 0)
        self.assertEqual(turn.transcript_metrics["filler_count"].value, 0)
        self.assertEqual(turn.transcript_metrics["filler_rate_pct"].value, 0.0)

    def test_session_aggregation(self):
        turn1 = self.analyzer.analyze_turn(
            "Um, we used Docker containers for deployment.",
            {"duration_ms": 3000, "pause_count": 1, "silence_duration_ms": 500},
            turn_id="q1",
        )
        turn2 = self.analyzer.analyze_turn(
            "Basically, the Kubernetes cluster managed scaling automatically.",
            {"duration_ms": 3000, "pause_count": 0, "silence_duration_ms": 0},
            turn_id="q2",
        )

        session = self.analyzer.aggregate_session([turn1, turn2])

        self.assertEqual(session.total_turns, 2)
        self.assertEqual(session.valid_timing_turns, 2)
        self.assertEqual(session.total_duration_sec, 6.0)
        self.assertEqual(session.total_fillers, 2)  # 'um' + 'basically'
        self.assertEqual(session.pause_summary["total_pauses"], 1)
        self.assertEqual(session.data_completeness, "full")
        self.assertTrue(len(session.delivery_observations) > 0)

    def test_session_aggregation_empty_turns(self):
        session = self.analyzer.aggregate_session([])
        self.assertEqual(session.total_turns, 0)
        self.assertEqual(session.data_completeness, "no_data")
        self.assertEqual(session.pause_summary["status"], "unavailable")

    def test_json_serialization(self):
        """Verify that all dataclasses cleanly convert to serializable dicts."""
        turn = self.analyzer.analyze_turn(
            "Actually, we improved latency by 40 percent.",
            {"duration_ms": 4000, "pause_count": 1, "silence_duration_ms": 800},
            turn_id="q_json",
        )
        turn_dict = turn.to_dict()
        # Must not raise TypeError
        json_str = json.dumps(turn_dict)
        self.assertIn("actually", json_str.lower())

        session = self.analyzer.aggregate_session([turn])
        session_dict = session.to_dict()
        session_json_str = json.dumps(session_dict)
        self.assertIn("delivery_observations", session_json_str)


if __name__ == "__main__":
    unittest.main()
