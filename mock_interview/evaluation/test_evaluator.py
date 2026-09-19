import sys
from pathlib import Path

from mock_interview.evaluation.evaluator import InterviewEvaluator
from mock_interview.interview.conversation_state import ConversationState


def run_evaluator_test():
    print("=" * 70)
    print("INTERVIEW EVALUATION ENGINE TEST")
    print("=" * 70)

    # 1. Mock Match Report
    match_report = {
        "role": "AI/ML Engineer",
        "required_skills": {
            "matched": ["python", "machine learning", "nlp", "sql"],
            "missing": ["pytorch"],
        },
        "preferred_skills": {
            "matched": ["llm"],
            "missing": ["docker", "fastapi"],
        },
        "required_skill_match_percentage": 80.0,
    }

    # 2. Construct realistic ConversationState
    state = ConversationState(
        candidate_name="H S YASHAS GOWDA",
        role="AI/ML Engineer",
        session_id="TEST_SESSION_001",
    )
    state.current_difficulty = 3
    state.completed_categories = [
        "introduction",
        "resume",
        "project",
        "technical",
        "role_specific",
        "skill_gap",
        "behavioral",
        "situational",
        "closing",
    ]

    # Sample interview turns covering key categories
    turns = [
        (
            "introduction",
            "Could you introduce yourself?",
            "I am an AI and Machine Learning engineer with strong experience in Python, NLP, and building data-driven systems.",
        ),
        (
            "project",
            "Tell me about your Skylark project architecture.",
            "Skylark is an AI-powered business intelligence agent. I used Python, Claude API, GraphQL and Pandas to convert natural language queries into actionable insights from live business data. I implemented deterministic data processing and interactive Streamlit dashboards.",
        ),
        (
            "technical",
            "Can you explain your experience with Python and machine learning?",
            "I have extensive experience with Python, NumPy, and Pandas. I have built NLP pipelines, trained classifiers, evaluated models using precision and recall, and deployed inference APIs.",
        ),
        (
            "skill_gap",
            "This role requires PyTorch. How familiar are you with it?",
            "While I have primarily used scikit-learn and foundational machine learning libraries, I understand backpropagation, PyTorch tensors, and neural network training loops. I am actively learning PyTorch to build deep learning models.",
        ),
        (
            "behavioral",
            "Describe a time you faced a difficult technical challenge.",
            "During a recent project deployment, I encountered Linux case-sensitivity and proxy issues between Vercel and Render. I systematically inspected network logs, resolved the path casing, and validated the endpoints.",
        ),
        (
            "closing",
            "Do you have any final thoughts or questions?",
            "Thank you for the opportunity. I enjoyed discussing the AI/ML role and look forward to contributing to machine learning engineering projects.",
        ),
    ]

    for cat, q, a in turns:
        state.set_question(q, cat)
        state.record_answer(a)

    state.end_session()

    # 3. Instantiate Evaluator & Evaluate
    evaluator = InterviewEvaluator(
        candidate_profile={"name": "H S YASHAS GOWDA"},
        job_profile={"role_title": "AI/ML Engineer"},
        match_report=match_report,
    )

    result = evaluator.evaluate(state)

    # 4. Print Outputs
    print("\n[EVALUATION RESULT OVERVIEW]")
    print("-" * 70)
    print(f"Candidate: {result['candidate_name']}")
    print(f"Role: {result['role']}")
    print(f"Total Questions Evaluated: {result['total_questions']}")
    print(f"Overall Score: {result['overall_score']} / 100")
    print(f"Performance Tier: {result['performance_tier']}")

    print("\n[COMPETENCY DIMENSION SCORES]")
    print("-" * 70)
    for dim, score in result["competency_scores"].items():
        print(f"  - {dim.replace('_', ' ').title()}: {score}%")

    print("\n[CATEGORY EVALUATIONS]")
    print("-" * 70)
    for cat, data in result["category_evaluations"].items():
        print(f"  - {cat.upper()}: Average = {data['average_score']}% ({data['performance']})")

    print("\n[IDENTIFIED STRENGTHS]")
    print("-" * 70)
    for s in result["strengths"]:
        print(f"  + {s}")

    print("\n[IDENTIFIED WEAKNESSES]")
    print("-" * 70)
    if result["weaknesses"]:
        for w in result["weaknesses"]:
            print(f"  - {w}")
    else:
        print("  None detected.")

    print("\n[SKILL GAP ANALYSIS]")
    print("-" * 70)
    print(f"Missing Required: {result['skill_gap_summary']['missing_required_skills']}")
    print(f"Missing Preferred: {result['skill_gap_summary']['missing_preferred_skills']}")
    print(f"Gap Performance: {result['skill_gap_summary']['gap_interview_performance']}")

    print("\n[RECOMMENDATIONS]")
    print("-" * 70)
    for r in result["recommendations"]:
        print(f"  * {r}")

    # 5. Formal Assertions / Validation
    print("\n[VALIDATION CHECKS]")
    print("-" * 70)

    # Check 1: Score range
    assert 0.0 <= result["overall_score"] <= 100.0, "Overall score out of bounds"
    print("PASS: Overall score is within valid [0, 100] range.")

    # Check 2: Competency dimensions present
    expected_dims = ["technical_knowledge", "communication", "relevance", "completeness", "problem_solving"]
    for d in expected_dims:
        assert d in result["competency_scores"], f"Missing dimension {d}"
        assert 0.0 <= result["competency_scores"][d] <= 100.0, f"Dimension {d} out of range"
    print("PASS: All 5 core competency dimensions are valid.")

    # Check 3: Strengths and Recommendations populated
    assert len(result["strengths"]) > 0, "No strengths identified"
    assert len(result["recommendations"]) > 0, "No recommendations generated"
    print("PASS: Strengths and recommendations successfully generated.")

    # Check 4: Skill gap preservation
    assert "pytorch" in result["skill_gap_summary"]["missing_required_skills"]
    print("PASS: Skill gaps accurately preserved from match report.")

    # Check 5: Question breakdown matches turn count
    assert len(result["question_breakdown"]) == len(turns), "Question breakdown length mismatch"
    print("PASS: Question-by-question breakdown generated for all turns.")

    print("\n" + "=" * 70)
    print("EVALUATION ENGINE TEST PASSED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_evaluator_test()
