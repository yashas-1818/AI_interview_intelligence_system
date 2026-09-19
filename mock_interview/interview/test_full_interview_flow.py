"""
REALISTIC ADAPTIVE INTERVIEW FLOW TEST

Tests:

    Resume
       ↓
    Job
       ↓
    Matching
       ↓
    Strategy
       ↓
    LLM-enabled Orchestrator
       ↓
    Question Generation
       ↓
    Candidate Answer
       ↓
    Answer Analysis
       ↓
    Decision Engine
       ↓
    Adaptive Follow-up
       ↓
    Category Progression
       ↓
    Closing
       ↓
    Interview End
"""

from pathlib import Path

from mock_interview.resume.parser import (
    extract_text_from_pdf,
)

from mock_interview.resume.analyzer import (
    build_candidate_profile,
)

from mock_interview.job.parser import (
    extract_job_text,
)

from mock_interview.job.analyzer import (
    analyze_job_description,
)

from mock_interview.job.matcher import (
    build_match_report,
)

from mock_interview.interview.strategy import (
    build_interview_strategy,
)

from mock_interview.interview.orchestrator import (
    InterviewOrchestrator,
)

from mock_interview.evaluation import (
    InterviewEvaluator,
)

from mock_interview.report import (
    ReportGenerator,
)


# ======================================================================
# CONFIGURATION
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RESUME_DIR = (
    PROJECT_ROOT
    / "mock_interview"
    / "resume"
    / "test_data"
)

MAX_QUESTIONS = 30


# ======================================================================
# FIND RESUME AUTOMATICALLY
# ======================================================================

def find_resume():
    """
    Find the first PDF inside the resume test_data directory.

    This avoids hardcoding a particular resume filename.
    """

    if not RESUME_DIR.exists():
        raise FileNotFoundError(
            f"Resume directory does not exist:\n{RESUME_DIR}"
        )

    resume_files = sorted(
        RESUME_DIR.glob("*.pdf")
    )

    if not resume_files:
        raise FileNotFoundError(
            "No PDF resume was found in:\n"
            f"{RESUME_DIR}"
        )

    return resume_files[0]


# ======================================================================
# SAMPLE JOB DESCRIPTION
# ======================================================================

JOB_DESCRIPTION = """
AI/ML Engineer

We are looking for an AI/ML Engineer to join our engineering team.

Required Skills:
- Strong Python programming
- Machine Learning
- Natural Language Processing
- PyTorch or TensorFlow
- SQL and databases

Preferred Skills:
- Large Language Models
- FastAPI
- Docker

Responsibilities:
- Build and deploy machine learning models
- Develop NLP and AI solutions
- Process and analyze datasets
- Build APIs for machine learning applications
- Evaluate and improve model performance
- Work with engineering teams to integrate AI systems

Qualifications:
- Bachelor's degree in Computer Science, Artificial Intelligence,
  Machine Learning or related field
- 0-2 years of experience
"""


# ======================================================================
# SAMPLE ANSWERS
# ======================================================================

def get_sample_answer(
    category: str,
    question: str,
) -> str:
    """
    Return realistic test answers.

    The answers are intentionally varied so that the
    adaptive decision engine can be exercised.
    """

    answers = {

        "introduction": (
            "I am an AI and machine learning student with "
            "experience in Python, NLP and software development. "
            "I have worked on several AI projects and also gained "
            "internship experience where I worked with machine "
            "learning and data processing."
        ),

        "resume": (
            "My background is mainly focused on artificial "
            "intelligence and machine learning. I have worked "
            "with Python, NLP, pandas, APIs and databases. "
            "During my internship and academic projects, I "
            "developed practical software and AI-based applications."
        ),

        "project": (
            "The Skylark architecture consisted of a backend "
            "layer that handled APIs and data processing. "
            "The system processed data, applied the required "
            "logic and exposed functionality through APIs. "
            "I separated the components so that the application "
            "could be extended with more AI functionality later."
        ),

        "technical": (
            "I have strong practical experience with Python. "
            "I have used it for machine learning, NLP, data "
            "processing and backend development. I am comfortable "
            "working with libraries such as pandas and building "
            "application logic around APIs."
        ),

        "role_specific": (
            "I would first validate the model and its preprocessing "
            "pipeline, then expose the model through an API and "
            "deploy it in a controlled environment. I would monitor "
            "latency, accuracy, failures and data drift after deployment."
        ),

        "skill_gap": (
            "I have not used PyTorch extensively in production yet, "
            "but I understand neural networks, model training and "
            "machine learning fundamentals. I have strong Python "
            "experience and I am confident I can learn PyTorch and "
            "apply it to practical projects."
        ),

        "behavioral": (
            "When I face a difficult problem, I first understand "
            "the root cause and break the problem into smaller parts. "
            "I test possible solutions and use the results to decide "
            "the next step."
        ),

        "situational": (
            "I would first understand the situation and identify "
            "the main constraint. Then I would evaluate possible "
            "solutions, choose the most practical one and monitor "
            "the result."
        ),

        "closing": (
            "Thank you. I enjoyed discussing my technical background "
            "and projects. I am particularly interested in developing "
            "my skills further in machine learning and AI engineering."
        ),
    }

    return answers.get(
        category,
        (
            "I would approach the problem systematically by first "
            "understanding the requirements, then implementing and "
            "testing the solution before evaluating its performance."
        ),
    )


# ======================================================================
# MAIN TEST
# ======================================================================

def main():

    print("=" * 70)
    print("REALISTIC ADAPTIVE INTERVIEW FLOW TEST")
    print("=" * 70)

    # ==================================================================
    # 1. FIND AND LOAD RESUME
    # ==================================================================

    print("\n[1] LOADING RESUME")
    print("-" * 70)

    resume_path = find_resume()

    print(
        f"Resume: {resume_path.name}"
    )

    resume_text = extract_text_from_pdf(
        resume_path
    )

    candidate = build_candidate_profile(
        resume_text
    )

    print(
        f"Candidate: {candidate.candidate.name}"
    )

    # ==================================================================
    # 2. PARSE JOB
    # ==================================================================

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

    # ==================================================================
    # 3. MATCHING
    # ==================================================================

    print("\n[3] MATCHING")
    print("-" * 70)

    match_report = build_match_report(
        candidate,
        job,
    )

    print(
        "Match report created."
    )

    # ==================================================================
    # 4. BUILD STRATEGY
    # ==================================================================

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
        strategy.get(
            "categories",
            [],
        )
    )

    # ==================================================================
    # 5. CREATE ORCHESTRATOR
    # ==================================================================

    print("\n[5] CREATING ORCHESTRATOR")
    print("-" * 70)

    orchestrator = InterviewOrchestrator(
        candidate_profile=candidate,
        job_profile=job,
        match_report=match_report,
        strategy=strategy,

        # --------------------------------------------------------------
        # IMPORTANT:
        # Enable Gemini-powered question generation.
        # --------------------------------------------------------------

        use_llm=True,
        max_questions=MAX_QUESTIONS,
    )

    print(
        "Orchestrator created."
    )

    print(
        "LLM question generation: ENABLED"
    )

    # ==================================================================
    # 6. START INTERVIEW
    # ==================================================================

    print("\n[6] STARTING INTERVIEW")
    print("-" * 70)

    start_result = orchestrator.start()

    print(
        f"Question: {start_result['question']}"
    )

    print(
        f"Category: {start_result['category']}"
    )

    print(
        f"Active category: "
        f"{start_result['active_category']}"
    )

    print(
        f"Difficulty: "
        f"{start_result['difficulty']}"
    )

    # ==================================================================
    # 7. INTERVIEW LOOP
    # ==================================================================

    question_count = 0

    while (
        orchestrator.state.is_active
        and question_count < MAX_QUESTIONS
    ):

        question_count += 1

        current_question = (
            orchestrator.get_current_question()
        )

        current_category = (
            orchestrator.get_current_category()
        )

        active_category = (
            orchestrator.get_active_category()
        )

        difficulty = (
            orchestrator.state.current_difficulty
        )

        print("\n")
        print(
            f"[QUESTION {question_count}]"
        )

        print("-" * 70)

        print(
            f"Category: {current_category}"
        )

        print(
            f"Active category: {active_category}"
        )

        print(
            f"Difficulty: {difficulty}"
        )

        print(
            f"Question: {current_question}"
        )

        # --------------------------------------------------------------
        # Determine which category should be used for the test answer.
        # For follow-ups, use the underlying active category.
        # --------------------------------------------------------------

        answer_category = current_category

        if current_category == "follow_up":
            answer_category = active_category

        # --------------------------------------------------------------
        # Generate sample answer
        # --------------------------------------------------------------

        answer = get_sample_answer(
            answer_category,
            current_question,
        )

        print(
            f"Answer: {answer}"
        )

        # --------------------------------------------------------------
        # Process answer
        # --------------------------------------------------------------

        result = orchestrator.process_answer(
            answer
        )

        # --------------------------------------------------------------
        # Extract decision
        # --------------------------------------------------------------

        decision = result.get(
            "decision",
            {},
        )

        assessment = result.get(
            "assessment",
            {},
        )

        # --------------------------------------------------------------
        # Display decision
        # --------------------------------------------------------------

        print(
            f"Action: "
            f"{decision.get('action')}"
        )

        print(
            f"Complete category: "
            f"{decision.get('complete_category')}"
        )

        # --------------------------------------------------------------
        # Display answer analysis
        # --------------------------------------------------------------

        print(
            f"Quality: "
            f"{assessment.get('quality')}"
        )

        print(
            f"Score: "
            f"{assessment.get('score')}"
        )

        print(
            f"Technical depth: "
            f"{assessment.get('technical_depth_level')}"
        )

        print(
            f"Needs follow-up: "
            f"{assessment.get('needs_followup')}"
        )

        # --------------------------------------------------------------
        # Interview ended
        # --------------------------------------------------------------

        if not orchestrator.state.is_active:

            print(
                "No next question."
            )

            print(
                "\nInterview session ended."
            )

            break

        # --------------------------------------------------------------
        # Next question
        # --------------------------------------------------------------

        next_question = result.get(
            "next_question"
        )

        print(
            f"Next question: "
            f"{next_question}"
        )

        print(
            f"Next category: "
            f"{orchestrator.get_current_category()}"
        )

        print(
            f"Next active category: "
            f"{orchestrator.get_active_category()}"
        )

    # ==================================================================
    # 8. MAX QUESTION SAFETY
    # ==================================================================

    if (
        question_count >= MAX_QUESTIONS
        and orchestrator.state.is_active
    ):

        print(
            "\nWARNING: Maximum question limit reached."
        )

        print(
            "Ending test session."
        )

        orchestrator.state.end_session()

    # ==================================================================
    # 9. FINAL STATE
    # ==================================================================

    final_state = (
        orchestrator.get_state()
    )

    print("\n")
    print(
        "[FINAL STATE]"
    )

    print("-" * 70)

    print(
        f"Questions asked: "
        f"{len(final_state.get('questions_asked', []))}"
    )

    print(
        f"Answers recorded: "
        f"{len(final_state.get('answers_received', []))}"
    )

    print(
        f"Current category: "
        f"{final_state.get('current_category')}"
    )

    print(
        f"Active category: "
        f"{final_state.get('active_category')}"
    )

    print(
        f"Completed categories: "
        f"{final_state.get('completed_categories')}"
    )

    print(
        f"Topics covered: "
        f"{final_state.get('topics_covered')}"
    )

    print(
        f"Difficulty: "
        f"{final_state.get('current_difficulty')}"
    )

    print(
        f"Follow-ups: "
        f"{final_state.get('followups_asked')}"
    )

    print(
        f"Interview active: "
        f"{final_state.get('is_active')}"
    )

    # ==================================================================
    # 10. VALIDATION
    # ==================================================================

    print("\n")
    print(
        "[VALIDATION]"
    )

    print("-" * 70)

    completed = final_state.get(
        "completed_categories",
        [],
    )

    expected_categories = [
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

    # --------------------------------------------------------------
    # Category validation
    # --------------------------------------------------------------

    for category in expected_categories:

        if category in completed:

            print(
                f"PASS: {category} completed."
            )

        else:

            print(
                f"FAIL: {category} not completed."
            )

    # --------------------------------------------------------------
    # Follow-up validation
    # --------------------------------------------------------------

    if "follow_up" not in completed:

        print(
            "PASS: follow_up is not a permanent category."
        )

    else:

        print(
            "FAIL: follow_up became a permanent category."
        )

    # --------------------------------------------------------------
    # Multiple question validation
    # --------------------------------------------------------------

    total_questions = len(
        final_state.get(
            "questions_asked",
            [],
        )
    )

    if total_questions > 1:

        print(
            "PASS: adaptive interview generated "
            "multiple questions."
        )

    else:

        print(
            "FAIL: insufficient questions generated."
        )

    # --------------------------------------------------------------
    # Answer validation
    # --------------------------------------------------------------

    total_answers = len(
        final_state.get(
            "answers_received",
            [],
        )
    )

    if total_answers > 0:

        print(
            "PASS: answers were recorded."
        )

    else:

        print(
            "FAIL: no answers recorded."
        )

    # --------------------------------------------------------------
    # Difficulty validation
    # --------------------------------------------------------------

    final_difficulty = final_state.get(
        "current_difficulty",
        1,
    )

    if final_difficulty > 1:

        print(
            "PASS: difficulty adaptation occurred."
        )

    else:

        print(
            "WARNING: difficulty did not increase."
        )

    # --------------------------------------------------------------
    # Interview termination validation
    # --------------------------------------------------------------

    if not final_state.get(
        "is_active",
        True,
    ):

        print(
            "PASS: interview session ended."
        )

    else:

        print(
            "FAIL: interview session is still active."
        )

    # ==================================================================
    # 11. EVALUATION & REPORT GENERATION
    # ==================================================================

    print("\n")
    print("=" * 70)
    print("GENERATING INTERVIEW INTELLIGENCE EVALUATION & REPORT")
    print("=" * 70)

    evaluator = InterviewEvaluator(
        candidate_profile=candidate,
        job_profile=job,
        match_report=match_report,
    )

    evaluation = evaluator.evaluate(final_state)

    print(f"\nCandidate: {evaluation['candidate_name']}")
    print(f"Overall Interview Score: {evaluation['overall_score']} / 100")
    print(f"Assessment Tier: {evaluation['performance_tier']}")

    print("\nCompetency Scores:")
    for dim, score in evaluation["competency_scores"].items():
        print(f"  - {dim.replace('_', ' ').title()}: {score}%")

    generator = ReportGenerator(
        candidate_profile=candidate,
        job_profile=job,
        match_report=match_report,
        evaluation_result=evaluation,
    )

    reports_dir = PROJECT_ROOT / "reports"
    saved = generator.save_report(reports_dir, f"report_{final_state.get('session_id')}")
    print(f"\nIntelligence Report saved to:")
    print(f"  - Markdown: {saved['markdown']}")
    print(f"  - HTML:     {saved['html']}")

    print("\nPASS: evaluation and intelligence report generated.")

    # ==================================================================
    # COMPLETE
    # ==================================================================

    print("\n")
    print("=" * 70)

    print(
        "REALISTIC ADAPTIVE INTERVIEW FLOW TEST COMPLETED"
    )

    print("=" * 70)


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    main()