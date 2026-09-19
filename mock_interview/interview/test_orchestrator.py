from mock_interview.resume.parser import extract_text_from_pdf
from mock_interview.resume.analyzer import build_candidate_profile

from mock_interview.job.parser import extract_job_text
from mock_interview.job.analyzer import analyze_job_description
from mock_interview.job.matcher import build_match_report

from mock_interview.interview.strategy import build_interview_strategy
from mock_interview.interview.orchestrator import InterviewOrchestrator


# =========================================================
# CONFIGURATION
# =========================================================

RESUME_PATH = (
    "mock_interview/resume/test_data/resume.pdf"
)


JOB_DESCRIPTION = """
AI/ML Engineer

We are looking for an AI/ML Engineer to join our team.

Requirements:
- Strong Python programming skills
- Knowledge of Machine Learning and NLP
- Experience with PyTorch or TensorFlow
- Understanding of SQL and databases

Preferred:
- Experience with LLMs
- Experience with FastAPI
- Docker knowledge

Responsibilities:
- Develop and deploy machine learning models
- Build NLP and AI-powered applications
- Work with data and databases
- Collaborate with engineering teams

Education:
Bachelor's degree in Computer Science, Artificial Intelligence,
or a related field.

Experience:
0-2 years
"""


# =========================================================
# DISPLAY HELPERS
# =========================================================

def print_separator():
    print("-" * 70)


def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# =========================================================
# MAIN TEST
# =========================================================

def main():

    print_header(
        "AI INTERVIEW ORCHESTRATOR TEST"
    )

    # -----------------------------------------------------
    # 1. LOAD RESUME
    # -----------------------------------------------------

    print()
    print("[1] LOADING RESUME")
    print_separator()

    resume_text = extract_text_from_pdf(
        RESUME_PATH
    )

    candidate_profile = build_candidate_profile(
        resume_text
    )

    print(
        "Resume text extracted successfully."
    )

    print(
        f"Candidate: "
        f"{candidate_profile.candidate.name}"
    )

    # -----------------------------------------------------
    # 2. PARSE JOB DESCRIPTION
    # -----------------------------------------------------

    print()
    print("[2] PARSING JOB DESCRIPTION")
    print_separator()

    job_text = extract_job_text(
        JOB_DESCRIPTION
    )

    job_profile = analyze_job_description(
        job_text
    )

    print(
        f"Role: {job_profile.role_title}"
    )

    # -----------------------------------------------------
    # 3. MATCH CANDIDATE WITH JOB
    # -----------------------------------------------------

    print()
    print("[3] MATCHING CANDIDATE WITH JOB")
    print_separator()

    match_report = build_match_report(
        candidate=candidate_profile,
        job=job_profile,
    )

    print(
        "Candidate-job matching completed."
    )

    print(
        "Required skill match: "
        f"{match_report['required_skill_match_percentage']:.2f}%"
    )

    # -----------------------------------------------------
    # 4. BUILD INTERVIEW STRATEGY
    # -----------------------------------------------------

    print()
    print("[4] BUILDING INTERVIEW STRATEGY")
    print_separator()

    strategy = build_interview_strategy(
        candidate=candidate_profile,
        job=job_profile,
        match_report=match_report,
    )

    print(
        "Interview strategy created successfully."
    )

    print(
        f"Categories: "
        f"{strategy['categories']}"
    )

    print(
        f"Skill gaps: "
        f"{strategy['skill_gaps']}"
    )

    print(
        f"Project topics: "
        f"{strategy['project_topics']}"
    )

    # -----------------------------------------------------
    # 5. CREATE ORCHESTRATOR
    # -----------------------------------------------------

    print()
    print("[5] CREATING INTERVIEW ORCHESTRATOR")
    print_separator()

    orchestrator = InterviewOrchestrator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        strategy=strategy,
        use_llm=False,
    )

    print(
        "Interview orchestrator created successfully."
    )

    # -----------------------------------------------------
    # 6. START INTERVIEW
    # -----------------------------------------------------

    print()
    print("[6] STARTING INTERVIEW")
    print_separator()

    first_question = orchestrator.start()

    print(
        f"First question:\n"
        f"{first_question}"
    )

    # -----------------------------------------------------
    # 7. PROCESS FIRST ANSWER
    # -----------------------------------------------------

    print()
    print("[7] PROCESSING FIRST ANSWER")
    print_separator()

    first_answer = (
        "I am an AI and Machine Learning student "
        "with experience in Python, machine learning, "
        "NLP and building AI-based applications. "
        "I have also worked on several academic and "
        "personal projects involving modern web and "
        "AI technologies."
    )

    print(
        f"Candidate answer:\n{first_answer}"
    )

    result_1 = orchestrator.process_answer(
        first_answer
    )

    print()
    print(
        "First answer processed successfully."
    )

    print(
        f"Result:\n{result_1}"
    )

    # -----------------------------------------------------
    # 8. PROCESS SECOND ANSWER
    # -----------------------------------------------------

    print()
    print("[8] PROCESSING SECOND ANSWER")
    print_separator()

    second_question = (
        orchestrator.get_current_question()
    )

    print(
        f"Next question:\n"
        f"{second_question}"
    )

    second_answer = (
        "In my Skylark project, I worked on "
        "building an AI-powered application. "
        "I used Python and machine learning concepts "
        "to process the required data and generate "
        "useful results."
    )

    print(
        f"\nCandidate answer:\n{second_answer}"
    )

    result_2 = orchestrator.process_answer(
        second_answer
    )

    print()
    print(
        "Second answer processed successfully."
    )

    print(
        f"Result:\n{result_2}"
    )

    # -----------------------------------------------------
    # 9. DISPLAY CURRENT STATE
    # -----------------------------------------------------

    print()
    print("[9] CURRENT INTERVIEW STATE")
    print_separator()

    state = orchestrator.state

    print(
        f"Candidate: "
        f"{state.candidate_name}"
    )

    print(
        f"Role: "
        f"{state.role}"
    )

    print(
        f"Questions asked: "
        f"{len(state.questions_asked)}"
    )

    print(
        f"Answers recorded: "
        f"{len(state.answers_received)}"
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Completed categories and covered topics
    # are two different things.
    # -----------------------------------------------------

    print(
        f"Completed categories: "
        f"{state.completed_categories}"
    )

    print(
        f"Topics covered: "
        f"{state.topics_covered}"
    )

    print(
        f"Current category: "
        f"{state.current_category}"
    )

    print(
        f"Current difficulty: "
        f"{state.current_difficulty}"
    )

    print(
        f"Topics remaining: "
        f"{len(state.topics_remaining)}"
    )

    print(
        f"Follow-ups asked: "
        f"{state.followups_asked}"
    )

    print(
        f"Interview active: "
        f"{state.is_active}"
    )

    # -----------------------------------------------------
    # 10. SERIALIZED STATE
    # -----------------------------------------------------

    print()
    print("[10] SERIALIZED INTERVIEW STATE")
    print_separator()

    state_dict = state.to_dict()

    print(
        f"Session ID: "
        f"{state_dict['session_id']}"
    )

    print(
        f"Question number: "
        f"{state_dict['question_number']}"
    )

    print(
        f"Questions stored: "
        f"{len(state_dict['questions_asked'])}"
    )

    print(
        f"Answers stored: "
        f"{len(state_dict['answers_received'])}"
    )

    print(
        f"Completed categories stored: "
        f"{state_dict['completed_categories']}"
    )

    print(
        f"Topics covered stored: "
        f"{state_dict['topics_covered']}"
    )

    print(
        f"Topics remaining stored: "
        f"{state_dict['topics_remaining']}"
    )

    # -----------------------------------------------------
    # 11. FINAL STATUS
    # -----------------------------------------------------

    print_header(
        "ORCHESTRATOR TEST COMPLETED"
    )

    print(
        "Resume -> Job -> Matching -> "
        "Strategy -> Orchestrator -> "
        "Question -> Answer -> Analysis -> "
        "Decision -> Topic Tracking -> "
        "Adaptive Next Question"
    )

    print()
    print(
        "All tested stages completed successfully."
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()