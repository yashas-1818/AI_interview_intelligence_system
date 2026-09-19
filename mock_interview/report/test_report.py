import shutil
from pathlib import Path

from mock_interview.evaluation.evaluator import InterviewEvaluator
from mock_interview.interview.conversation_state import ConversationState
from mock_interview.report.generator import ReportGenerator


def run_report_test():
    print("=" * 70)
    print("INTERVIEW REPORT GENERATOR TEST")
    print("=" * 70)

    # 1. Mock Profiles & Match Data
    candidate_profile = {
        "candidate": {
            "name": "H S YASHAS GOWDA",
            "email": "yashasgowda14318@gmail.com",
        },
        "education": [
            {
                "institution": "Jyothy Institute of Technology, Bangalore",
                "degree": "B.E. in AI & ML",
                "score": "CGPA: 7.5",
            }
        ],
    }

    job_profile = {
        "role_title": "AI/ML Engineer",
        "company": "Tech Corp",
        "required_skills": ["Python", "Machine Learning", "NLP", "PyTorch"],
    }

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
        "required_skill_match_percentage": 75.0,
    }

    # 2. Conversation State
    state = ConversationState(
        candidate_name="H S YASHAS GOWDA",
        role="AI/ML Engineer",
        session_id="REPORT_TEST_SESSION_01",
    )
    state.current_difficulty = 3

    turns = [
        ("introduction", "Tell me about yourself.", "I am an AI/ML undergraduate with hands-on experience in Python, NLP and building AI agents."),
        ("project", "Explain your Skylark project architecture.", "Skylark is an AI-powered business intelligence agent. I used Python, Claude API, GraphQL and Pandas to convert natural language queries into actionable insights from live business data."),
        ("technical", "How do you evaluate machine learning models?", "I use precision, recall, F1-score, and ROC-AUC curves depending on class imbalance, and cross-validation for stability."),
        ("skill_gap", "This role requires PyTorch. What is your experience?", "I understand PyTorch tensors and training loops conceptually from deep learning coursework and am actively completing practical projects with it."),
        ("closing", "Do you have any questions for us?", "I would love to learn more about the team's deployment stack and production machine learning workflows."),
    ]

    for cat, q, a in turns:
        state.set_question(q, cat)
        state.record_answer(a)

    state.end_session()

    # 3. Generate Evaluation
    evaluator = InterviewEvaluator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        match_report=match_report,
    )
    evaluation_result = evaluator.evaluate(state)

    # 4. Generate Report
    generator = ReportGenerator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        match_report=match_report,
        evaluation_result=evaluation_result,
    )

    report_dict = generator.build_report()
    md_report = generator.generate_markdown(report_dict)
    html_report = generator.generate_html(report_dict)

    # 5. Output Verification
    print("\n[STRUCTURED REPORT VERIFICATION]")
    print("-" * 70)
    print(f"Candidate: {report_dict['candidate']['name']}")
    print(f"Role: {report_dict['job']['role']}")
    print(f"Overall Score: {report_dict['interview_summary']['overall_score']}")
    print(f"Competencies: {list(report_dict['competency_scores'].keys())}")
    print(f"Total Questions in Breakdown: {len(report_dict['question_breakdown'])}")

    print("\n[MARKDOWN REPORT SNIPPET]")
    print("-" * 70)
    print(md_report[:500] + "\n... [truncated for display]")

    print("\n[HTML REPORT SNIPPET]")
    print("-" * 70)
    print(html_report[:350] + "\n... [truncated for display]")

    # 6. Save Report Test
    test_out_dir = Path(__file__).resolve().parent / "test_output"
    files = generator.save_report(test_out_dir, "test_interview_report")
    print("\n[SAVED FILES]")
    print("-" * 70)
    print(f"Markdown: {files['markdown']}")
    print(f"HTML: {files['html']}")

    # 7. Validations
    assert files["markdown"].exists() and files["markdown"].stat().st_size > 0
    assert files["html"].exists() and files["html"].stat().st_size > 0
    assert "H S YASHAS GOWDA" in md_report
    assert "AI/ML Engineer" in md_report
    assert "Core Competency Dimensions" in md_report
    assert "Candidate-Job Alignment" in md_report
    assert "<!DOCTYPE html>" in html_report

    # Cleanup temporary test output directory
    if test_out_dir.exists():
        shutil.rmtree(test_out_dir)

    print("\n" + "=" * 70)
    print("REPORT GENERATOR TEST PASSED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_report_test()
