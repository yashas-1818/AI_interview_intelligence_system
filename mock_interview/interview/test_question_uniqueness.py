"""
Automated Test Suite: Question Deduplication, Semantic Uniqueness & Skip Behavior

Validates:
1. Exact duplicate question detection.
2. Minor wording variation detection.
3. Semantic intent similarity detection with topic overlap.
4. Different aspects of the same topic/project/skill are allowed.
5. Skipping a question never produces that question again.
6. LLM duplicate rejection with template fallback.
7. Template fallback duplicate avoidance.
8. Follow-up questions on same topic with distinct angles are allowed.
9. Category exhaustion transitions to next category.
10. Successive skips transition through categories cleanly without infinite loop.
"""

import unittest
from typing import Dict, Any

from mock_interview.interview.question_validator import (
    QuestionValidator,
    are_questions_similar,
    detect_intents,
    extract_entities,
)
from mock_interview.interview.conversation_state import ConversationState
from mock_interview.interview.orchestrator import InterviewOrchestrator
from mock_interview.interview.strategy import build_interview_strategy


class MockCandidate:
    name = "Jane Doe"
    email = "jane@example.com"
    phone = "555-0100"
    skills = {"languages": ["Python", "SQL"], "frameworks": ["PyTorch", "FastAPI"]}
    projects = [
        {"title": "Skylark Drone Navigation", "description": "Autonomous vision pipeline using Python and PyTorch."},
        {"title": "Customer Churn Predictor", "description": "Predictive analytics pipeline."}
    ]
    experience = [{"role": "ML Intern", "company": "Tech Corp"}]
    education = [{"degree": "B.S. Computer Science"}]
    summary = "Experienced AI/ML developer specializing in Python and deep learning."


class MockJob:
    title = "AI / ML Engineer"
    role_title = "AI / ML Engineer"
    required_skills = ["Python", "Machine Learning", "PyTorch", "SQL"]
    preferred_skills = ["FastAPI", "Docker"]
    responsibilities = [
        "Build and deploy machine learning models",
        "Develop NLP and AI solutions",
        "Process and analyze datasets"
    ]


class TestQuestionUniqueness(unittest.TestCase):
    """Unit tests for QuestionValidator and Orchestrator deduplication logic."""

    def setUp(self):
        self.validator = QuestionValidator()
        self.validator.register_entities(
            projects=["Skylark Drone Navigation", "Skylark", "Customer Churn Predictor"],
            skills=["Python", "PyTorch", "SQL", "FastAPI", "Machine Learning"]
        )

    def test_01_exact_duplicate_rejected(self):
        """Exact identical question is detected and rejected."""
        q = "Can you explain your Skylark Drone Navigation project?"
        self.validator.record_question(q, category="project")
        self.assertTrue(self.validator.is_duplicate(q, category="project"))
        self.assertTrue(self.validator.is_duplicate(q.lower(), category="project"))

    def test_02_minor_wording_variation_rejected(self):
        """Minor phrasing variations of identical question are rejected."""
        q1 = "What challenges did you face using Python?"
        q2 = "What challenges did you face when using Python?"
        q3 = "Can you explain the challenges you encountered while using Python?"

        self.validator.record_question(q1, category="technical")
        self.assertTrue(self.validator.is_duplicate(q2, category="technical"))
        self.assertTrue(self.validator.is_duplicate(q3, category="technical"))

    def test_03_same_intent_paraphrase_rejected(self):
        """Paraphrased question with same intent and same entity is rejected."""
        q1 = "What was the most difficult challenge you encountered on the Skylark project?"
        q2 = "What technical obstacles or challenges did you face during Skylark?"

        self.validator.record_question(q1, category="project")
        dup, reason = are_questions_similar(q2, q1)
        self.assertTrue(dup, f"Expected duplicate detection, got: {reason}")
        self.assertTrue(self.validator.is_duplicate(q2, category="project"))

    def test_04_different_aspects_accepted(self):
        """Distinct inquiry aspects (architecture vs contribution vs challenge) on same project are accepted."""
        q_arch = "What architecture did you use for the Skylark project?"
        q_chal = "What was your biggest technical challenge on the Skylark project?"
        q_cont = "What was your personal contribution to the Skylark project?"

        # All 3 share the entity 'skylark', but have completely different intents
        dup1, _ = are_questions_similar(q_chal, q_arch)
        dup2, _ = are_questions_similar(q_cont, q_arch)
        dup3, _ = are_questions_similar(q_cont, q_chal)

        self.assertFalse(dup1, "Architecture vs Challenge should not be considered duplicate")
        self.assertFalse(dup2, "Architecture vs Contribution should not be considered duplicate")
        self.assertFalse(dup3, "Contribution vs Challenge should not be considered duplicate")

    def test_05_skip_never_repeats_question(self):
        """When a candidate skips, the skipped question is never repeated in the session."""
        orchestrator = InterviewOrchestrator(
            candidate_profile=MockCandidate(),
            job_profile=MockJob(),
            use_llm=False,
        )
        orchestrator.start()
        first_q = orchestrator.get_current_question()
        self.assertTrue(len(first_q) > 0)

        # Skip question
        skip_res = orchestrator.skip_question()
        self.assertTrue(skip_res["success"])
        second_q = skip_res["next_question"]

        self.assertNotEqual(first_q, second_q)
        dup, reason = are_questions_similar(first_q, second_q)
        self.assertFalse(dup, f"Next question after skip must not be duplicate: {reason}")
        self.assertIn(first_q, orchestrator.state.skipped_questions)

    def test_06_llm_duplicate_fallback_to_template(self):
        """If LLM generates a duplicate question, orchestrator rejects it and falls back to unique template."""
        class MockDuplicateLLM:
            def __init__(self, dup_text):
                self.dup_text = dup_text
                self.calls = 0

            def generate_question(self, context, category, previous_question="", previous_answer=""):
                self.calls += 1
                return {
                    "question": self.dup_text,
                    "category": category,
                    "difficulty": 1,
                    "generation_method": "llm",
                }

        orchestrator = InterviewOrchestrator(
            candidate_profile=MockCandidate(),
            job_profile=MockJob(),
            use_llm=True,
            llm_adapter=MockDuplicateLLM("Can you introduce yourself?"),
        )
        orchestrator.start()
        # Pre-record the LLM's fixed response
        orchestrator.validator.record_question("Can you introduce yourself?", category="introduction")

        # Now ask orchestrator to generate next question
        res = orchestrator.generate_question(category="introduction")
        # LLM generated duplicate "Can you introduce yourself?", so orchestrator should reject LLM and fall back to template
        self.assertNotEqual(res.get("question"), "Can you introduce yourself?")
        self.assertTrue(len(res.get("question", "")) > 0)
        self.assertEqual(res.get("generation_method"), "template")

    def test_07_template_duplicate_cycling(self):
        """Template generation cycles through available templates rather than repeating."""
        orchestrator = InterviewOrchestrator(
            candidate_profile=MockCandidate(),
            job_profile=MockJob(),
            use_llm=False,
        )
        orchestrator.start()
        q1 = orchestrator.get_current_question()
        # Answer q1 to trigger next question
        res1 = orchestrator.process_answer("My background is in machine learning and Python development.")
        q2 = res1.get("next_question")

        if q2:
            self.assertNotEqual(q1, q2)
            dup, _ = are_questions_similar(q1, q2)
            self.assertFalse(dup)

    def test_08_followup_topic_reuse_with_distinct_intents_accepted(self):
        """Follow-up questions probing the same topic with different inquiry angles are accepted."""
        q_base = "How did you use PyTorch in the Skylark project?"
        q_followup1 = "Could you give a specific example of optimizing the PyTorch computational graph?"
        q_followup2 = "What trade-offs did you evaluate when deploying that PyTorch model?"

        dup1, _ = are_questions_similar(q_followup1, q_base)
        dup2, _ = are_questions_similar(q_followup2, q_followup1)

        self.assertFalse(dup1, "Deep-dive example follow-up should be accepted")
        self.assertFalse(dup2, "Trade-off follow-up should be accepted")

    def test_09_category_exhaustion_transitions(self):
        """When questions in a category are exhausted, category transitions cleanly."""
        orchestrator = InterviewOrchestrator(
            candidate_profile=MockCandidate(),
            job_profile=MockJob(),
            use_llm=False,
        )
        orchestrator.start()
        initial_cat = orchestrator.get_current_category()

        # Repeatedly skip within initial category until it transitions
        categories_visited = [initial_cat]
        for _ in range(10):
            if not orchestrator.state.is_active:
                break
            skip_res = orchestrator.skip_question()
            cat = orchestrator.get_current_category()
            if cat != categories_visited[-1]:
                categories_visited.append(cat)

        self.assertGreater(len(categories_visited), 1, "Should have transitioned away from initial category")

    def test_10_successive_skips_terminate_cleanly_without_loop(self):
        """Consecutive skips progress through all categories and terminate cleanly without infinite loop."""
        orchestrator = InterviewOrchestrator(
            candidate_profile=MockCandidate(),
            job_profile=MockJob(),
            use_llm=False,
        )
        orchestrator.start()

        max_skips = 50
        skips_done = 0
        all_questions = []

        while orchestrator.state.is_active and skips_done < max_skips:
            curr_q = orchestrator.get_current_question()
            if curr_q:
                all_questions.append(curr_q)
            res = orchestrator.skip_question()
            skips_done += 1

        # Must terminate before 50 skips
        self.assertLess(skips_done, max_skips, "Session should terminate after exhausting interview strategy")
        self.assertFalse(orchestrator.state.is_active, "Interview should conclude after exhausting categories")

        # Verify NO duplicate questions were asked during the entire sequence of skips
        for i in range(len(all_questions)):
            for j in range(i + 1, len(all_questions)):
                q_a = all_questions[i]
                q_b = all_questions[j]
                dup, reason = are_questions_similar(q_a, q_b)
                self.assertFalse(dup, f"Duplicate found between #{i} and #{j}: '{q_a}' vs '{q_b}'. Reason: {reason}")


if __name__ == "__main__":
    unittest.main()
