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
    assert "Speech & Verbal Delivery Analytics" in md_report
    assert "Speech & Verbal Delivery" in html_report

    # Cleanup temporary test output directory
    if test_out_dir.exists():
        shutil.rmtree(test_out_dir)

    # 8. Test Report with Explicit Speech Analytics
    print("\n[TEST: REPORT WITH EXPLICIT SPEECH ANALYTICS]")
    print("-" * 70)
    explicit_speech = {
        "total_turns": 3,
        "valid_timing_turns": 3,
        "total_words": 150,
        "total_duration_sec": 65.0,
        "average_speaking_pace_wpm": 138.5,
        "total_fillers": 3,
        "average_filler_rate_pct": 2.0,
        "filler_breakdown": {"like": 2, "basically": 1},
        "most_frequent_fillers": [{"filler": "like", "count": 2}, {"filler": "basically", "count": 1}],
        "pause_summary": {
            "total_pauses": 4,
            "total_pause_duration_sec": 5.2,
            "measured_turns": 3,
            "status": "measured",
            "details": "Measured across 3 turns with audio telemetry.",
        },
        "data_completeness": "full",
        "delivery_observations": [
            "Candidate spoke at an average pace of 138.5 WPM, which is within the standard conversational range.",
            "Filler usage was minimal at 2.0% of spoken words.",
            "A total of 4 pause events (5.2s total silence) were recorded across 3 timed turns.",
        ],
    }

    gen_explicit = ReportGenerator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        match_report=match_report,
        evaluation_result=evaluation_result,
        speech_analytics=explicit_speech,
    )
    rep_explicit_data = gen_explicit.build_report()
    md_explicit = gen_explicit.generate_markdown(rep_explicit_data)
    html_explicit = gen_explicit.generate_html(rep_explicit_data)

    assert "Speech & Verbal Delivery Analytics" in md_explicit
    assert "138.5 WPM" in md_explicit
    assert "150" in md_explicit
    assert "65.0s" in md_explicit
    assert "2.00%" in md_explicit
    assert "4 pauses (5.2s silence)" in md_explicit
    assert "Independence Guarantee" in html_explicit or "evaluated separately" in md_explicit
    print("Report with explicit speech analytics validated successfully.")

    # 9. Test Report with Missing Audio Timing (Transcript Only - Never Fabricate)
    print("\n[TEST: REPORT WITH MISSING TIMING (NEVER FABRICATE PAUSES)]")
    print("-" * 70)
    transcript_only_speech = {
        "total_turns": 2,
        "valid_timing_turns": 0,
        "total_words": 80,
        "total_duration_sec": None,
        "average_speaking_pace_wpm": None,
        "total_fillers": 1,
        "average_filler_rate_pct": 1.25,
        "filler_breakdown": {"actually": 1},
        "most_frequent_fillers": [{"filler": "actually", "count": 1}],
        "pause_summary": {
            "total_pauses": None,
            "total_pause_duration_sec": None,
            "measured_turns": 0,
            "status": "unavailable",
            "details": "Audio pause telemetry was not provided; pause metrics were not inferred from text.",
        },
        "data_completeness": "transcript_only",
        "delivery_observations": [
            "Speaking pace was unavailable because audio timing telemetry was not recorded.",
            "Audio pause telemetry was not recorded; pauses were not inferred from transcript text.",
        ],
    }

    gen_partial = ReportGenerator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        match_report=match_report,
        evaluation_result=evaluation_result,
        speech_analytics=transcript_only_speech,
    )
    rep_partial_data = gen_partial.build_report()
    md_partial = gen_partial.generate_markdown(rep_partial_data)
    html_partial = gen_partial.generate_html(rep_partial_data)

    assert "Unavailable" in md_partial
    assert "Audio pause telemetry was not provided; pauses are never inferred from text" in md_partial
    assert "Not recorded" in html_partial or "Unavailable" in html_partial
    print("Missing timing correctly reports Unavailable without inventing pauses or pacing.")

    # 10. Test Zero-Answer Session Report Generation
    print("\n[TEST: ZERO-ANSWER / EARLY TERMINATION SESSION]")
    print("-" * 70)
    empty_state = ConversationState(
        candidate_name="H S YASHAS GOWDA",
        role="AI/ML Engineer",
        session_id="EMPTY_SESSION_TEST",
    )
    empty_state.end_session()
    eval_empty = evaluator.evaluate(empty_state)
    gen_empty = ReportGenerator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        match_report=match_report,
        evaluation_result=eval_empty,
        conversation_history=[],
    )
    rep_empty_data = gen_empty.build_report()
    md_empty = gen_empty.generate_markdown(rep_empty_data)
    html_empty = gen_empty.generate_html(rep_empty_data)

    assert "<!DOCTYPE html>" in html_empty
    assert len(md_empty) > 100
    print("Zero-answer report generation passed gracefully.")

    print("\n" + "=" * 70)
    print("ALL REPORT GENERATOR TESTS PASSED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    run_report_test()
