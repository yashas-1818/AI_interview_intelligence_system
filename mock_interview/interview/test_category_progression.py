from mock_interview.resume.parser import extract_text_from_pdf
from mock_interview.resume.analyzer import build_candidate_profile

from mock_interview.job.parser import extract_job_text
from mock_interview.job.analyzer import analyze_job_description

from mock_interview.job.matcher import build_match_report

from mock_interview.interview.strategy import (
    build_interview_strategy,
)

from mock_interview.interview.orchestrator import (
    InterviewOrchestrator,
)


# ================================================================
# TEST DATA
# ================================================================

RESUME_PATH = (
    r"D:\AI_Interview_Intelligence_System"
    r"\mock_interview\resume\test_data\resume.pdf"
)


JOB_DESCRIPTION = """
AI/ML Engineer

Requirements:
- Strong Python programming
- Machine Learning and NLP
- PyTorch or TensorFlow
- SQL and databases

Preferred:
- LLM experience
- FastAPI
- Docker

Responsibilities:
- Develop and deploy machine learning models
- Build NLP and AI-powered applications
- Work with data and databases
- Collaborate with engineering teams

Education:
Bachelor's degree in Computer Science, AI, ML or related field.
"""


# ================================================================
# MAIN TEST
# ================================================================

def main():

    print("=" * 70)
    print("INTERVIEW CATEGORY PROGRESSION TEST")
    print("=" * 70)

    # ============================================================
    # 1. LOAD RESUME
    # ============================================================

    print("\n[1] LOADING RESUME")
    print("-" * 70)

    resume_text = extract_text_from_pdf(
        RESUME_PATH
    )

    candidate = build_candidate_profile(
        resume_text
    )

    print(
        f"Candidate: "
        f"{candidate.candidate.name}"
    )

    # ============================================================
    # 2. PARSE JOB
    # ============================================================

    print("\n[2] PARSING JOB")
    print("-" * 70)

    job_text = extract_job_text(
        JOB_DESCRIPTION
    )

    job = analyze_job_description(
        job_text
    )

    print(
        f"Role: {job.role_title}"
    )

    # ============================================================
    # 3. MATCH CANDIDATE
    # ============================================================

    print("\n[3] MATCHING")
    print("-" * 70)

    match_report = build_match_report(
        candidate,
        job,
    )

    print(
        "Required skill match:",
        match_report[
            "required_skills"
        ].get(
            "match_percentage",
            "N/A",
        ),
    )

    # ============================================================
    # 4. BUILD STRATEGY
    # ============================================================

    print("\n[4] BUILDING STRATEGY")
    print("-" * 70)

    strategy = build_interview_strategy(
        candidate,
        job,
        match_report,
    )

    print(
        "Categories:"
    )

    print(
        strategy["categories"]
    )

    # ============================================================
    # 5. CREATE ORCHESTRATOR
    # ============================================================

    print("\n[5] CREATING ORCHESTRATOR")
    print("-" * 70)

    orchestrator = InterviewOrchestrator(
        candidate_profile=candidate,
        job_profile=job,
        match_report=match_report,
        strategy=strategy,
        use_llm=False,
    )

    print(
        "Orchestrator created."
    )

    # ============================================================
    # 6. START INTERVIEW
    # ============================================================

    print("\n[6] STARTING INTERVIEW")
    print("-" * 70)

    start_result = orchestrator.start()

    print(
        "Question:",
        start_result["question"],
    )

    print(
        "Current category:",
        start_result["category"],
    )

    print(
        "Active category:",
        start_result["active_category"],
    )

    # ============================================================
    # 7. FIRST ANSWER
    # ============================================================

    print("\n[7] ANSWER 1")
    print("-" * 70)

    answer_1 = """
    I am an AI and Machine Learning student with experience
    in Python, NLP and AI application development. I have
    worked on multiple projects and internships where I
    applied these skills to real problems.
    """

    result_1 = orchestrator.process_answer(
        answer_1
    )

    print(
        "Action:",
        result_1["action"],
    )

    print(
        "Complete category:",
        result_1.get(
            "complete_category"
        ),
    )

    print(
        "Next question:",
        result_1["next_question"],
    )

    state = orchestrator.get_state()

    print(
        "Current category:",
        state["current_category"],
    )

    print(
        "Active category:",
        state["active_category"],
    )

    # ============================================================
    # 8. SECOND ANSWER
    # ============================================================

    print("\n[8] ANSWER 2")
    print("-" * 70)

    answer_2 = """
    In my Skylark project, I designed and developed an
    AI-powered business intelligence application. I used
    Python and machine learning concepts to process business
    data and generate useful insights.
    """

    result_2 = orchestrator.process_answer(
        answer_2
    )

    print(
        "Action:",
        result_2["action"],
    )

    print(
        "Complete category:",
        result_2.get(
            "complete_category"
        ),
    )

    print(
        "Next question:",
        result_2["next_question"],
    )

    state = orchestrator.get_state()

    print(
        "Current category:",
        state["current_category"],
    )

    print(
        "Active category:",
        state["active_category"],
    )

    print(
        "Follow-ups:",
        state["followups_asked"],
    )

    # ============================================================
    # 9. THIRD ANSWER — STRONG ANSWER
    # ============================================================

    print("\n[9] ANSWER 3 — STRONG ANSWER")
    print("-" * 70)

    answer_3 = """
    In the Skylark project, I was responsible for designing
    the overall architecture and implementing the core AI
    functionality. I used Python for the backend processing,
    Claude API for natural language understanding, GraphQL
    for retrieving structured business data, and Pandas for
    data processing. The system accepts natural language
    queries from users, converts them into structured requests,
    retrieves the relevant business information, processes the
    data and finally generates actionable insights. One of the
    main challenges was connecting natural language input with
    structured business data reliably, so I separated the
    processing into clear stages for query understanding,
    data retrieval and response generation.
    """

    result_3 = orchestrator.process_answer(
        answer_3
    )

    print(
        "Action:",
        result_3["action"],
    )

    print(
        "Complete category:",
        result_3.get(
            "complete_category"
        ),
    )

    print(
        "Next question:",
        result_3["next_question"],
    )

    # ============================================================
    # 10. FINAL STATE
    # ============================================================

    print("\n[10] FINAL STATE")
    print("-" * 70)

    state = orchestrator.get_state()

    print(
        "Questions asked:",
        len(
            state["questions_asked"]
        ),
    )

    print(
        "Answers recorded:",
        len(
            state["answers_received"]
        ),
    )

    print(
        "Current category:",
        state["current_category"],
    )

    print(
        "Active category:",
        state["active_category"],
    )

    print(
        "Completed categories:",
        state["completed_categories"],
    )

    print(
        "Topics covered:",
        state["topics_covered"],
    )

    print(
        "Difficulty:",
        state["current_difficulty"],
    )

    print(
        "Follow-ups:",
        state["followups_asked"],
    )

    print(
        "Interview active:",
        state["is_active"],
    )

    # ============================================================
    # 11. VALIDATION
    # ============================================================

    print("\n[11] VALIDATION")
    print("-" * 70)

    if (
        "follow_up"
        not in state["completed_categories"]
    ):

        print(
            "PASS: follow_up was not stored "
            "as a permanent category."
        )

    else:

        print(
            "FAIL: follow_up incorrectly became "
            "a completed category."
        )

    if (
        "introduction"
        in state["completed_categories"]
    ):

        print(
            "PASS: introduction category completed."
        )

    else:

        print(
            "INFO: introduction has not yet "
            "been completed by this test."
        )

    if (
        "project"
        in state["completed_categories"]
    ):

        print(
            "PASS: project category completed."
        )

    else:

        print(
            "INFO: project has not yet "
            "been completed by this test."
        )

    print("\n" + "=" * 70)
    print(
        "CATEGORY PROGRESSION TEST COMPLETED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()