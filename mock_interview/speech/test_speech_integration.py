"""
Integration Tests for Speech Analytics in Interview Sessions and FastAPI API.

Tests:
1. Answer submission with no telemetry (backward compatibility).
2. Answer submission with valid timing telemetry.
3. Safe rejection/flagging of invalid, malformed, negative, or inconsistent telemetry.
4. Correct association of metrics with individual turns in conversation history.
5. Handling of skipped questions and early interview termination.
6. Multi-turn session speech aggregation.
7. Complete independence between speech metrics and answer competency scores.
"""

import os
import sys
import unittest
from pathlib import Path

# Bootstrap project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

from mock_interview.api import app, sessions
from mock_interview.interview.orchestrator import InterviewOrchestrator
from mock_interview.speech.analyzer import SpeechDeliveryAnalyzer


class TestSpeechAPIIntegration(unittest.TestCase):
    """Test API endpoints with speech telemetry."""

    def setUp(self):
        self.client = TestClient(app)
        # Setup session with default resume & preset job
        res_upload = self.client.post("/api/upload-resume")
        self.assertEqual(res_upload.status_code, 200)
        self.session_id = res_upload.json()["session_id"]

        res_job = self.client.post(
            "/api/setup-job",
            json={"job_preset": "1", "session_id": self.session_id},
        )
        self.assertEqual(res_job.status_code, 200)

        res_start = self.client.post(
            "/api/start-interview",
            json={"use_llm": False, "session_id": self.session_id},
        )
        self.assertEqual(res_start.status_code, 200)

    def test_submit_answer_backward_compatibility_no_telemetry(self):
        """
        Verify existing requests containing only session_id and answer
        continue to work without error.
        """
        payload = {
            "session_id": self.session_id,
            "answer": "I have extensive experience with Python, FastAPI, and relational databases.",
        }
        response = self.client.post("/api/submit-answer", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        prev_turn = data.get("previous_turn", {})
        self.assertIn("speech_analytics", prev_turn)
        speech = prev_turn["speech_analytics"]

        self.assertEqual(speech["telemetry_status"], "transcript_only")
        # Transcript metrics must be measured
        self.assertEqual(speech["transcript_metrics"]["word_count"]["value"], 10)
        self.assertEqual(speech["transcript_metrics"]["word_count"]["status"], "measured")
        self.assertEqual(speech["transcript_metrics"]["filler_count"]["value"], 0)

        # Timing metrics must be explicitly marked unavailable
        self.assertIsNone(speech["timing_metrics"]["answer_duration_sec"]["value"])
        self.assertEqual(speech["timing_metrics"]["answer_duration_sec"]["status"], "unavailable")
        self.assertIsNone(speech["timing_metrics"]["speaking_pace_wpm"]["value"])
        self.assertEqual(speech["timing_metrics"]["speaking_pace_wpm"]["status"], "unavailable")
        self.assertIsNone(speech["timing_metrics"]["pause_count"]["value"])
        self.assertEqual(speech["timing_metrics"]["pause_count"]["status"], "unavailable")

    def test_submit_answer_with_valid_telemetry(self):
        """
        Verify that valid speech telemetry is parsed and accurately calculated.
        """
        payload = {
            "session_id": self.session_id,
            "answer": "Um, basically I implemented asynchronous API endpoints using FastAPI and Redis.",
            "speech_telemetry": {
                "duration_ms": 6000,
                "speech_duration_ms": 4800,
                "silence_duration_ms": 1200,
                "pause_count": 1,
                "pause_events": [
                    {"start_ms": 1500, "end_ms": 2700, "duration_ms": 1200}
                ],
            },
        }
        response = self.client.post("/api/submit-answer", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        speech = data["previous_turn"]["speech_analytics"]
        self.assertEqual(speech["telemetry_status"], "full")

        # Transcript metrics
        # "Um, basically I implemented asynchronous API endpoints using FastAPI and Redis." -> 11 words
        self.assertEqual(speech["transcript_metrics"]["word_count"]["value"], 11)
        self.assertEqual(speech["transcript_metrics"]["filler_count"]["value"], 2)  # 'um' and 'basically'
        self.assertEqual(speech["transcript_metrics"]["filler_rate_pct"]["value"], 18.18)

        # Timing metrics
        self.assertEqual(speech["timing_metrics"]["answer_duration_sec"]["value"], 6.0)
        self.assertEqual(speech["timing_metrics"]["answer_duration_sec"]["status"], "measured")
        # 11 words in 6.0s = 110.0 WPM
        self.assertEqual(speech["timing_metrics"]["speaking_pace_wpm"]["value"], 110.0)
        self.assertEqual(speech["timing_metrics"]["speaking_pace_wpm"]["status"], "measured")
        # Audio pauses
        self.assertEqual(speech["timing_metrics"]["pause_count"]["value"], 1)
        self.assertEqual(speech["timing_metrics"]["pause_count"]["status"], "measured")
        self.assertEqual(speech["timing_metrics"]["total_pause_duration_sec"]["value"], 1.2)
        self.assertEqual(speech["timing_metrics"]["active_speech_duration_sec"]["value"], 4.8)

    def test_submit_answer_with_invalid_telemetry_safe_handling(self):
        """
        Verify that corrupt or invalid telemetry does NOT crash the endpoint,
        marks telemetry_status as 'invalid_telemetry', and preserves transcript metrics.
        """
        invalid_payloads = [
            # Negative duration
            {"duration_ms": -5000},
            # Non-numeric string
            {"duration_ms": "not-a-number"},
            # Inconsistent timestamps (end < start)
            {"start_time_ms": 15000, "end_time_ms": 5000},
            # Negative pause count
            {"pause_count": -5},
        ]

        for bad_telemetry in invalid_payloads:
            payload = {
                "session_id": self.session_id,
                "answer": "We deployed the backend on Kubernetes using Docker containers.",
                "speech_telemetry": bad_telemetry,
            }
            response = self.client.post("/api/submit-answer", json=payload)
            self.assertEqual(response.status_code, 200, f"Crashed on {bad_telemetry}")
            data = response.json()

            speech = data["previous_turn"]["speech_analytics"]
            self.assertEqual(speech["telemetry_status"], "invalid_telemetry")
            # Transcript metrics must remain intact
            self.assertEqual(speech["transcript_metrics"]["word_count"]["value"], 9)
            # Timing metrics must be safe None with status 'unavailable'
            self.assertIsNone(speech["timing_metrics"]["answer_duration_sec"]["value"])
            self.assertEqual(speech["timing_metrics"]["answer_duration_sec"]["status"], "unavailable")
            self.assertIn("Invalid telemetry", speech["timing_metrics"]["answer_duration_sec"]["details"])

    def test_turn_association_and_ordering(self):
        """
        Verify that multiple consecutive answers maintain their exact, isolated
        metrics in conversation history without cross-contamination.
        """
        session_obj = sessions[self.session_id]
        orchestrator = session_obj.orchestrator

        # Turn 1: 4 seconds with 0 fillers
        self.client.post(
            "/api/submit-answer",
            json={
                "session_id": self.session_id,
                "answer": "First answer discussing machine learning models and data pipelines.",
                "speech_telemetry": {"duration_ms": 4000, "pause_count": 0, "silence_duration_ms": 0},
            },
        )

        # Turn 2: Untimed with 1 filler
        self.client.post(
            "/api/submit-answer",
            json={
                "session_id": self.session_id,
                "answer": "Um, the second answer focuses on database indexing.",
                # No telemetry provided
            },
        )

        history = orchestrator.state.conversation_history
        self.assertEqual(len(history), 2)

        turn_1_speech = history[0]["speech_analytics"]
        turn_2_speech = history[1]["speech_analytics"]

        # Check turn 1
        self.assertEqual(turn_1_speech["timing_metrics"]["answer_duration_sec"]["value"], 4.0)
        self.assertEqual(turn_1_speech["transcript_metrics"]["filler_count"]["value"], 0)

        # Check turn 2
        self.assertIsNone(turn_2_speech["timing_metrics"]["answer_duration_sec"]["value"])
        self.assertEqual(turn_2_speech["transcript_metrics"]["filler_count"]["value"], 1)

    def test_skipped_question_handling(self):
        """
        Verify that skipped questions attach empty/safe speech analytics.
        """
        session_obj = sessions[self.session_id]
        orchestrator = session_obj.orchestrator

        res_skip = self.client.post(
            "/api/skip-question",
            json={"session_id": self.session_id},
        )
        self.assertEqual(res_skip.status_code, 200)
        data = res_skip.json()

        self.assertTrue(data["skipped"])
        history = orchestrator.state.conversation_history
        self.assertEqual(len(history), 1)

        skip_turn = history[0]
        self.assertTrue(skip_turn.get("skipped"))
        self.assertIn("speech_analytics", skip_turn)
        speech = skip_turn["speech_analytics"]
        self.assertEqual(speech["telemetry_status"], "empty_answer")
        self.assertEqual(speech["transcript_metrics"]["word_count"]["value"], 0)

    def test_session_aggregation_and_end_interview(self):
        """
        Verify that POST /api/end-interview aggregates all turns safely
        and returns 'speech_delivery_analytics' without affecting competency evaluation.
        """
        # Submit 1 answer with valid telemetry
        self.client.post(
            "/api/submit-answer",
            json={
                "session_id": self.session_id,
                "answer": "Actually, I used PyTorch to train a custom Transformer model.",
                "speech_telemetry": {
                    "duration_ms": 5000,
                    "pause_count": 1,
                    "silence_duration_ms": 1000,
                    "speech_duration_ms": 4000,
                },
            },
        )

        # Submit 1 answer with transcript only
        self.client.post(
            "/api/submit-answer",
            json={
                "session_id": self.session_id,
                "answer": "We deployed with Docker and evaluated latency under load.",
            },
        )

        # End interview
        res_end = self.client.post(
            "/api/end-interview",
            json={"session_id": self.session_id},
        )
        self.assertEqual(res_end.status_code, 200)
        end_data = res_end.json()

        self.assertIn("speech_delivery_analytics", end_data)
        delivery = end_data["speech_delivery_analytics"]

        self.assertEqual(delivery["total_turns"], 2)
        self.assertEqual(delivery["valid_timing_turns"], 1)
        self.assertEqual(delivery["total_fillers"], 1)  # 'actually'
        self.assertEqual(delivery["pause_summary"]["status"], "measured")
        self.assertEqual(delivery["pause_summary"]["total_pauses"], 1)
        self.assertEqual(delivery["data_completeness"], "partial")
        self.assertTrue(len(delivery["delivery_observations"]) > 0)

        # Competency score integrity
        self.assertIn("evaluation", end_data)
        self.assertIn("overall_score", end_data["evaluation"])
        self.assertGreater(end_data["evaluation"]["overall_score"], 0.0)

    def test_competency_scores_unaffected_by_speech_metrics(self):
        """
        CRITICAL: Proves that speech delivery timing, pace, and pause telemetry
        do NOT alter or penalize candidate competency/answer assessment scores.
        """
        session_obj = sessions[self.session_id]
        orchestrator = session_obj.orchestrator

        test_answer = "I used Python, PyTorch, and NLP algorithms to build the Skylark pipeline."

        # 1. Answer with fast duration (5s) and 0 pauses
        fast_res = orchestrator.process_answer(
            test_answer,
            speech_telemetry={"duration_ms": 5000, "pause_count": 0},
        )
        score_fast = fast_res["assessment"]["score"]

        # Reset orchestrator for identical question comparison
        orchestrator_2 = InterviewOrchestrator(
            candidate_profile=session_obj.candidate_profile,
            job_profile=session_obj.job_profile,
            match_report=session_obj.match_report,
            strategy=session_obj.strategy,
            use_llm=False,
        )
        orchestrator_2.start()

        # 2. Same answer with very slow duration (40s) and multiple pauses
        slow_res = orchestrator_2.process_answer(
            test_answer,
            speech_telemetry={
                "duration_ms": 40000,
                "pause_count": 8,
                "silence_duration_ms": 12000,
                "speech_duration_ms": 28000,
            },
        )
        score_slow = slow_res["assessment"]["score"]

        # Reset orchestrator for third comparison (no telemetry at all)
        orchestrator_3 = InterviewOrchestrator(
            candidate_profile=session_obj.candidate_profile,
            job_profile=session_obj.job_profile,
            match_report=session_obj.match_report,
            strategy=session_obj.strategy,
            use_llm=False,
        )
        orchestrator_3.start()

        # 3. Same answer with no telemetry (transcript only)
        none_res = orchestrator_3.process_answer(
            test_answer,
            speech_telemetry=None,
        )
        score_none = none_res["assessment"]["score"]

        # All scores must be strictly identical
        self.assertEqual(
            score_fast,
            score_slow,
            "Speech duration and pause metrics must not modify competency score!",
        )
        self.assertEqual(
            score_fast,
            score_none,
            "Presence of speech telemetry must not modify competency score!",
        )

    def test_typed_telemetry_payload_without_audio_events(self):
        """
        Verify that when a candidate types their answer (hasSpeechActivity = false),
        elapsed duration is recorded, but pause count and speech duration are NEVER fabricated.
        """
        payload = {
            "session_id": self.session_id,
            "answer": "I prefer using PostgreSQL for relational transactions and Redis for session caching.",
            "speech_telemetry": {
                "start_time_ms": 1000.0,
                "end_time_ms": 7000.0,
                "duration_ms": 6000.0,
                "speech_duration_ms": None,
                "silence_duration_ms": None,
                "pause_count": None,
                "pause_events": [],
                "speech_segments": [],
            },
        }
        response = self.client.post("/api/submit-answer", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        speech = data["previous_turn"]["speech_analytics"]
        self.assertEqual(speech["telemetry_status"], "duration_only")

        # Duration is measured
        self.assertEqual(speech["timing_metrics"]["answer_duration_sec"]["value"], 6.0)
        self.assertEqual(speech["timing_metrics"]["answer_duration_sec"]["status"], "measured")

        # Speaking pace is measured from duration
        self.assertIsNotNone(speech["timing_metrics"]["speaking_pace_wpm"]["value"])
        self.assertEqual(speech["timing_metrics"]["speaking_pace_wpm"]["status"], "measured")

        # Crucial check: pause metrics must be UNAVAILABLE, never fabricated
        self.assertIsNone(speech["timing_metrics"]["pause_count"]["value"])
        self.assertEqual(speech["timing_metrics"]["pause_count"]["status"], "unavailable")
        self.assertIsNone(speech["timing_metrics"]["total_pause_duration_sec"]["value"])
        self.assertEqual(speech["timing_metrics"]["total_pause_duration_sec"]["status"], "unavailable")
        self.assertIsNone(speech["timing_metrics"]["active_speech_duration_sec"]["value"])
        self.assertEqual(speech["timing_metrics"]["active_speech_duration_sec"]["status"], "unavailable")

    def test_end_interview_generated_reports_contain_speech_section(self):
        """
        Verify that POST /api/end-interview writes reports containing
        the Speech & Verbal Delivery section and serves them via GET /api/reports/{filename}.
        """
        # Submit 1 answer with full telemetry
        self.client.post(
            "/api/submit-answer",
            json={
                "session_id": self.session_id,
                "answer": "Like, I designed a microservice architecture using FastAPI and Docker containers.",
                "speech_telemetry": {
                    "duration_ms": 5000,
                    "pause_count": 1,
                    "silence_duration_ms": 800,
                    "speech_duration_ms": 4200,
                },
            },
        )

        # End interview
        res_end = self.client.post(
            "/api/end-interview",
            json={"session_id": self.session_id},
        )
        self.assertEqual(res_end.status_code, 200)
        end_data = res_end.json()

        reports = end_data["reports"]
        md_url = reports["markdown_url"]
        html_url = reports["html_url"]

        # Fetch Markdown report via API
        res_md = self.client.get(md_url)
        self.assertEqual(res_md.status_code, 200)
        md_text = res_md.text
        self.assertIn("Speech & Verbal Delivery Analytics", md_text)
        self.assertIn("Total Spoken Words", md_text)
        self.assertIn("Average Speaking Pace", md_text)
        self.assertIn("Audio Pauses & Silence", md_text)
        self.assertIn("evaluated separately from technical knowledge", md_text)

        # Fetch HTML report via API
        res_html = self.client.get(html_url)
        self.assertEqual(res_html.status_code, 200)
        html_text = res_html.text
        self.assertIn("Speech & Verbal Delivery Analytics", html_text)
        self.assertIn("Speaking Pace", html_text)
        self.assertIn("Audio Silence / Pauses", html_text)
        self.assertIn("Independence Guarantee", html_text)


if __name__ == "__main__":
    unittest.main()
