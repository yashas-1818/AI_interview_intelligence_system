"""
AI POWERED INTERVIEW INTELLIGENCE SYSTEM
Main Application Entry Point

Supports:
1. Interactive CLI: python -m mock_interview.app
2. Automated Demo:   python -m mock_interview.app --demo
3. Web Server:       python -m mock_interview.app --web
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from mock_interview.resume.parser import extract_text_from_pdf
from mock_interview.resume.analyzer import build_candidate_profile
from mock_interview.job.parser import extract_job_text
from mock_interview.job.analyzer import analyze_job_description
from mock_interview.job.matcher import build_match_report
from mock_interview.interview.strategy import build_interview_strategy
from mock_interview.interview.orchestrator import InterviewOrchestrator
from mock_interview.evaluation.evaluator import InterviewEvaluator
from mock_interview.report.generator import ReportGenerator


# ======================================================================
# CONSTANTS & PRESETS
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESUME_DIR = PROJECT_ROOT / "mock_interview" / "resume" / "test_data"
REPORTS_DIR = PROJECT_ROOT / "reports"

JOB_PRESETS = {
    "1": {
        "title": "AI / ML Engineer",
        "description": """AI/ML Engineer

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
- Bachelor's degree in Computer Science, Artificial Intelligence, Machine Learning or related field
- 0-2 years of experience
""",
    },
    "2": {
        "title": "Full Stack Software Engineer",
        "description": """Full Stack Software Engineer

We are seeking a Full Stack Software Engineer to build scalable web applications.

Required Skills:
- Python
- JavaScript or TypeScript
- REST APIs & FastAPI / Flask
- Relational Databases (PostgreSQL / MySQL)
- Git & Version Control

Preferred Skills:
- React or modern frontend frameworks
- Docker
- Cloud platforms (AWS or GCP)

Responsibilities:
- Design and develop robust backend services and APIs
- Implement interactive and responsive user interfaces
- Optimize database queries and application performance
- Collaborate in agile development sprints
""",
    },
    "3": {
        "title": "Data Scientist",
        "description": """Data Scientist

Looking for an analytical Data Scientist to turn complex datasets into actionable insights.

Required Skills:
- Python (pandas, numpy, scikit-learn)
- SQL and advanced data querying
- Statistical modeling and hypothesis testing
- Data visualization (Matplotlib, Seaborn)

Preferred Skills:
- Big Data tools
- Deep learning fundamentals
- MLOps and experiment tracking

Responsibilities:
- Perform exploratory data analysis and feature engineering
- Build predictive statistical and machine learning models
- Present insights and data stories to business stakeholders
""",
    },
}

DEMO_ANSWERS = {
    "introduction": (
        "I am an AI and Machine Learning graduate with extensive experience in "
        "Python, Natural Language Processing, and full-stack software development. "
        "During my academic tenure and internships, I developed end-to-end intelligent systems, "
        "focusing on practical data processing pipelines and API integrations."
    ),
    "resume": (
        "My background centers on AI engineering and practical software development. "
        "I have worked with Python, pandas, NLP algorithms, RESTful APIs, and relational databases. "
        "My projects emphasize modular design, scalable data processing, and maintainable architectures."
    ),
    "project": (
        "In the Skylark project, I architected a modular backend system separating data ingestion, "
        "NLP transformation pipelines, and REST API controllers. "
        "I implemented structured validation, cached recurring queries, and decoupled the inference engine "
        "to ensure high throughput and seamless extensibility."
    ),
    "technical": (
        "I have strong practical proficiency in Python, covering object-oriented design, asynchronous "
        "programming, and machine learning libraries like pandas, NumPy, and scikit-learn. "
        "I design robust data pipelines with error boundaries, input schema validation, and optimized "
        "vectorized operations."
    ),
    "role_specific": (
        "For production deployment, I containerize the model service using Docker, expose endpoints "
        "via FastAPI with strict schema validation, and implement health checks. "
        "Post-deployment, I track latency percentiles, memory utilization, and inference distribution "
        "to immediately catch data drift or model degradation."
    ),
    "skill_gap": (
        "While my production focus has primarily leveraged Python and machine learning pipelines, "
        "I understand deep learning principles such as computational graphs, backpropagation, and tensor operations. "
        "Given my strong Python foundation, I have already been experimenting with PyTorch neural network modules "
        "and can become productive rapidly."
    ),
    "behavioral": (
        "When faced with ambiguous technical challenges or unexpected production bugs, "
        "I isolate the root cause through reproducible unit tests and structured logging. "
        "I break the problem into incremental milestones, consult peer feedback when appropriate, "
        "and verify solutions before shipping."
    ),
    "situational": (
        "If a production service experiences unexpected latency spikes during peak load, "
        "I first review latency telemetry and API logs to identify bottleneck components. "
        "If an upstream model is slow, I implement request timeouts and graceful fallbacks "
        "while investigating cache hit rates and query optimizations."
    ),
    "closing": (
        "Thank you very much for this interview session. I enjoyed discussing my technical background, "
        "architectural decisions, and problem-solving methodology. I am very excited about the AI/ML Engineer role "
        "and look forward to contributing to the team."
    ),
}


# ======================================================================
# BANNER & FORMATTING HELPERS
# ======================================================================

def print_banner():
    banner = """
==============================================================================
         AI POWERED INTERVIEW INTELLIGENCE SYSTEM
    Realistic - Adaptive - Personalized Mock Interview & Evaluation Engine
==============================================================================
"""
    print(banner)


def find_default_resume() -> Optional[Path]:
    """Find the first PDF in the test_data directory."""
    if not RESUME_DIR.exists():
        return None
    pdf_files = sorted(RESUME_DIR.glob("*.pdf"))
    return pdf_files[0] if pdf_files else None


def prompt_user_answer() -> str:
    """
    Prompt candidate for answer in interactive mode.
    Supports single-line, multiline (end with '\\' to continue), :skip, and :quit.
    """
    print("\nCandidate Response:")
    print("  [Tip: Type response and press Enter. End a line with '\\' to continue on a new line]")
    print("  [Commands: ':skip' to pass, ':quit' to conclude interview early]")
    
    lines = []
    while True:
        try:
            prompt_str = "  > " if not lines else "  .. "
            line = input(prompt_str)
        except (EOFError, KeyboardInterrupt):
            print()
            return ":quit"
        
        if not lines:
            trimmed = line.strip()
            if trimmed.lower() in (":quit", ":exit"):
                return ":quit"
            if trimmed.lower() == ":skip":
                return ":skip"
        
        if line.endswith("\\"):
            lines.append(line[:-1].strip())
        else:
            lines.append(line.strip())
            break
            
    answer = " ".join(lines).strip()
    return answer if answer else "I don't have a specific answer for this question."


# ======================================================================
# CORE INTERVIEW PIPELINE RUNNER
# ======================================================================

def run_interview_session(
    resume_path: Path,
    job_description_text: str,
    job_title: str = "Target Role",
    interactive: bool = True,
    use_llm: bool = True,
    verbose: bool = False,
    max_questions: int = 25,
) -> Dict[str, Any]:
    """
    Executes the complete end-to-end interview intelligence pipeline:
    Resume -> Candidate Profile -> Job Profile -> Matching -> Strategy ->
    Adaptive Orchestrator -> Loop -> Evaluation Engine -> Report Generator.
    """
    print("\n" + "=" * 70)
    print("PHASE 1: RESUME INTELLIGENCE & CANDIDATE PROFILING")
    print("=" * 70)
    print(f"Loading Resume: {resume_path.name}")
    resume_text = extract_text_from_pdf(resume_path)
    candidate_profile = build_candidate_profile(resume_text)
    
    candidate_name = candidate_profile.candidate.name or "Candidate"
    print(f"Candidate Identified: {candidate_name}")
    if candidate_profile.candidate.email:
        print(f"Contact:              {candidate_profile.candidate.email}")
    all_skills = []
    if isinstance(candidate_profile.skills, dict):
        for s_list in candidate_profile.skills.values():
            if isinstance(s_list, list):
                all_skills.extend(s_list)
    elif isinstance(candidate_profile.skills, list):
        all_skills.extend(candidate_profile.skills)
    print(f"Extracted Skills:     {', '.join(all_skills[:10])}{'...' if len(all_skills) > 10 else ''}")

    print("\n" + "=" * 70)
    print("PHASE 2: JOB INTELLIGENCE & ROLE ANALYSIS")
    print("=" * 70)
    job_text = extract_job_text(job_description_text)
    job_profile = analyze_job_description(job_text)
    print(f"Target Role:          {job_profile.role_title or job_title}")
    req_skills = job_profile.required_skills or []
    pref_skills = job_profile.preferred_skills or []
    print(f"Required Skills:      {', '.join(req_skills)}")
    if pref_skills:
        print(f"Preferred Skills:     {', '.join(pref_skills)}")

    print("\n" + "=" * 70)
    print("PHASE 3: CANDIDATE-JOB MATCHING & GAP ANALYSIS")
    print("=" * 70)
    match_report = build_match_report(candidate_profile, job_profile)
    req_match_pct = match_report.get("required_skill_match_percentage", 0.0)
    matched_req = match_report.get("required_skills", {}).get("matched", [])
    missing_req = match_report.get("required_skills", {}).get("missing", [])
    missing_pref = match_report.get("preferred_skills", {}).get("missing", [])
    
    print(f"Required Skill Match: {req_match_pct:.1f}%")
    print(f"Matched Skills:       {', '.join(matched_req) if matched_req else 'None'}")
    print(f"Identified Gaps:      {', '.join(missing_req) if missing_req else 'None'}")
    if missing_pref:
        print(f"Secondary Gaps:       {', '.join(missing_pref)}")

    print("\n" + "=" * 70)
    print("PHASE 4: STRATEGY FORMULATION")
    print("=" * 70)
    strategy = build_interview_strategy(candidate_profile, job_profile, match_report)
    planned_categories = strategy.get("categories", [])
    print(f"Interview Roadmap:    {' -> '.join(planned_categories)}")
    print(f"LLM Engine:           {'Gemini API (with instant deterministic fallback)' if use_llm else 'Deterministic Rule-Based'}")

    print("\n" + "=" * 70)
    print("PHASE 5: ADAPTIVE INTERVIEW SESSION")
    print("=" * 70)
    orchestrator = InterviewOrchestrator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        match_report=match_report,
        strategy=strategy,
        use_llm=use_llm,
    )

    start_result = orchestrator.start()
    question_count = 0

    while orchestrator.state.is_active and question_count < max_questions:
        question_count += 1
        current_question = orchestrator.get_current_question()
        current_category = orchestrator.get_current_category()
        active_category = orchestrator.get_active_category()
        difficulty = orchestrator.state.current_difficulty

        category_label = current_category.upper()
        if current_category == "follow_up":
            category_label = f"FOLLOW-UP ({active_category.upper()})"

        diff_stars = "*" * difficulty + "-" * (5 - difficulty)
        
        print("\n" + "-" * 70)
        print(f"[QUESTION {question_count}]  Category: {category_label}  |  Difficulty: Level {difficulty} [{diff_stars}]")
        print("-" * 70)
        print(f"Interviewer: \"{current_question}\"")

        # Obtain answer based on mode
        if interactive:
            answer = prompt_user_answer()
            if answer == ":quit":
                print("\n[Candidate opted to conclude the interview early.]")
                orchestrator.state.end_session()
                break
        else:
            # Automated Demo Mode
            lookup_cat = active_category if current_category == "follow_up" else current_category
            answer = DEMO_ANSWERS.get(
                lookup_cat,
                "I approach this challenge by analyzing requirements, designing structured modules, and validating thoroughly.",
            )
            time.sleep(0.3)
            print(f"\nCandidate: \"{answer}\"")

        # Process Answer or Skip
        if answer == ":skip":
            print("\n>> Candidate skipped this question.")
            result = orchestrator.skip_question()
            decision = result.get("decision", {})
            action = decision.get("action", "skip")
            print(">> Interviewer Decision: Moving to next unique question...")
        else:
            result = orchestrator.process_answer(answer)
            assessment = result.get("assessment", {})
            decision = result.get("decision", {})

            # Provide live candidate feedback
            quality = assessment.get("quality", "moderate").upper()
            score = assessment.get("score", 50.0)
            depth = assessment.get("technical_depth_level", "medium")
            action = decision.get("action", "next")

            print(f"\n>> Live Assessment: Quality: {quality} | Score: {score:.1f}/100 | Tech Depth: {depth}")
            if decision.get("trigger_followup"):
                print(">> Interviewer Decision: Probing further with a contextual follow-up...")
            elif decision.get("complete_category"):
                print(f">> Category Complete: Moving to next evaluation domain.")

        if verbose:
            print(f"   [Debug] Action: {action} | Next Category: {decision.get('next_category')} | New Diff: {orchestrator.state.current_difficulty}")

        if not orchestrator.state.is_active:
            print("\n[Interviewer has completed all planned interview domains.]")
            break

    if question_count >= max_questions and orchestrator.state.is_active:
        print("\n[Safety limit reached; ending interview session.]")
        orchestrator.state.end_session()

    final_state = orchestrator.get_state()

    print("\n" + "=" * 70)
    print("PHASE 6: INTERVIEW INTELLIGENCE EVALUATION")
    print("=" * 70)
    evaluator = InterviewEvaluator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        match_report=match_report,
    )
    evaluation_result = evaluator.evaluate(final_state)

    overall_score = evaluation_result.get("overall_score", 0.0)
    perf_tier = evaluation_result.get("performance_tier", "N/A")
    competencies = evaluation_result.get("competency_scores", {})

    print(f"Candidate:              {candidate_name}")
    print(f"Overall Interview Score: {overall_score:.1f} / 100")
    print(f"Performance Tier:        {perf_tier}")
    print(f"Questions Evaluated:     {evaluation_result.get('total_questions', 0)}")
    print(f"Peak Difficulty Handled: Level {evaluation_result.get('max_difficulty_reached', 1)}")

    print("\nCore Competency Breakdown:")
    for comp, cscore in competencies.items():
        bar_len = int(cscore / 5)
        bar = "=" * bar_len + " " * (20 - bar_len)
        print(f"  - {comp.replace('_', ' ').title():<22} [{bar}] {cscore:>5.1f}%")

    strengths = evaluation_result.get("strengths", [])
    if strengths:
        print("\nKey Identified Strengths:")
        for s in strengths[:4]:
            print(f"  [+] {s}")

    weaknesses = evaluation_result.get("weaknesses", [])
    if weaknesses:
        print("\nAreas for Improvement:")
        for w in weaknesses[:4]:
            print(f"  [-] {w}")

    print("\n" + "=" * 70)
    print("PHASE 7: REPORT GENERATION & EXPORT")
    print("=" * 70)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_gen = ReportGenerator(
        candidate_profile=candidate_profile,
        job_profile=job_profile,
        match_report=match_report,
        evaluation_result=evaluation_result,
        conversation_history=final_state.get("conversation_history", []),
    )

    session_id = final_state.get("session_id", "session")
    saved_files = report_gen.save_report(REPORTS_DIR, f"report_{session_id}")
    print(f"Markdown Report Saved:   {saved_files['markdown']}")
    print(f"HTML Dashboard Saved:    {saved_files['html']}")

    print("\n" + "=" * 70)
    print("INTERVIEW PROCESS COMPLETE")
    print("=" * 70)

    return {
        "candidate_profile": candidate_profile,
        "job_profile": job_profile,
        "match_report": match_report,
        "final_state": final_state,
        "evaluation": evaluation_result,
        "reports": saved_files,
    }


# ======================================================================
# INTERACTIVE CLI SETUP HELPERS
# ======================================================================

def run_interactive_cli(args: argparse.Namespace):
    """Guide the user through setup and conduct the interactive interview."""
    print_banner()

    # Step 1: Select Resume
    print("[STEP 1/2] RESUME SELECTION")
    print("-" * 70)
    resume_path = None

    if args.resume:
        custom_p = Path(args.resume)
        if custom_p.exists() and custom_p.suffix.lower() == ".pdf":
            resume_path = custom_p
        else:
            print(f"Specified resume not found or invalid: {args.resume}")

    if not resume_path:
        default_p = find_default_resume()
        print("Available Resumes in test_data:")
        if default_p:
            print(f"  [1] {default_p.name} (Default)")
        print("  [2] Enter custom path to a PDF resume")

        choice = input("\nSelect an option [1]: ").strip()
        if choice == "2":
            custom_input = input("Enter full path to resume PDF: ").strip().strip('"').strip("'")
            custom_p = Path(custom_input)
            if custom_p.exists() and custom_p.suffix.lower() == ".pdf":
                resume_path = custom_p
            else:
                print("File not found. Falling back to default test resume.")
                resume_path = default_p
        else:
            resume_path = default_p

    if not resume_path or not resume_path.exists():
        print(f"Error: No valid PDF resume found in {RESUME_DIR}. Please place a resume.pdf there.")
        sys.exit(1)

    # Step 2: Select Job Description
    print("\n[STEP 2/2] TARGET JOB SELECTION")
    print("-" * 70)
    job_description_text = ""
    job_title = "Target Role"

    if args.job:
        job_p = Path(args.job)
        if job_p.exists():
            job_description_text = job_p.read_text(encoding="utf-8")
            job_title = job_p.stem
        else:
            job_description_text = args.job
            job_title = "Custom Job"
    else:
        print("Choose a target job profile:")
        for key, pinfo in JOB_PRESETS.items():
            print(f"  [{key}] {pinfo['title']}")
        print("  [4] Custom: Paste or enter custom job description")

        job_choice = input("\nSelect job preset [1]: ").strip()
        if job_choice in JOB_PRESETS:
            job_description_text = JOB_PRESETS[job_choice]["description"]
            job_title = JOB_PRESETS[job_choice]["title"]
        elif job_choice == "4":
            print("\nEnter or paste job description (Press Enter, then Ctrl+Z / Ctrl+D or type 'DONE' on a new line):")
            lines = []
            while True:
                try:
                    l = input()
                    if l.strip().upper() == "DONE":
                        break
                    lines.append(l)
                except (EOFError, KeyboardInterrupt):
                    break
            job_description_text = "\n".join(lines).strip()
            if not job_description_text:
                print("Empty input; using AI/ML Engineer default.")
                job_description_text = JOB_PRESETS["1"]["description"]
                job_title = JOB_PRESETS["1"]["title"]
            else:
                job_title = "Custom Role"
        else:
            job_description_text = JOB_PRESETS["1"]["description"]
            job_title = JOB_PRESETS["1"]["title"]

    print(f"\nReady to begin interview for: {job_title}")
    input("Press [Enter] to start the interview session...")

    run_interview_session(
        resume_path=resume_path,
        job_description_text=job_description_text,
        job_title=job_title,
        interactive=True,
        use_llm=not args.no_llm,
        verbose=args.verbose,
    )


# ======================================================================
# AUTOMATED DEMO RUNNER
# ======================================================================

def run_automated_demo(args: argparse.Namespace):
    """Run an automated end-to-end mock interview demonstration."""
    print_banner()
    print(">>> RUNNING AUTOMATED DEMONSTRATION MODE <<<")
    print("This mode simulates an intelligent candidate answering dynamic questions,")
    print("verifying all system capabilities without requiring manual typing.")

    default_resume = find_default_resume()
    if not default_resume or not default_resume.exists():
        print(f"Error: No resume PDF found in {RESUME_DIR}")
        sys.exit(1)

    job_text = JOB_PRESETS["1"]["description"]
    job_title = JOB_PRESETS["1"]["title"]

    run_interview_session(
        resume_path=default_resume,
        job_description_text=job_text,
        job_title=job_title,
        interactive=False,
        use_llm=not args.no_llm,
        verbose=args.verbose,
    )


# ======================================================================
# WEB SERVER LAUNCHER
# ======================================================================

def run_web_server(args: argparse.Namespace):
    """Launch the FastAPI Web Application & Interface."""
    print_banner()
    print(f"Starting Web Application Server at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server.")

    try:
        import uvicorn
        from mock_interview.api import app
        uvicorn.run(app, host=args.host, port=args.port, reload=False)
    except ImportError as exc:
        print(f"Error: Missing web server dependency: {exc}")
        print("Please ensure fastapi and uvicorn are installed.")
        sys.exit(1)


# ======================================================================
# CLI PARSER ENTRY
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI Powered Interview Intelligence System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run an automated end-to-end demonstration interview without typing.",
    )
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Start the FastAPI Web Server and browser interface.",
    )
    parser.add_argument(
        "--resume", "-r",
        type=str,
        default=None,
        help="Path to candidate resume PDF file.",
    )
    parser.add_argument(
        "--job", "-j",
        type=str,
        default=None,
        help="Path to job description text file or job text.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for web server (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for web server (default: 8000).",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable external Gemini LLM and use deterministic rule-based engine.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable detailed decision engine and assessment logging.",
    )

    args = parser.parse_args()

    if args.web:
        run_web_server(args)
    elif args.demo:
        run_automated_demo(args)
    else:
        run_interactive_cli(args)


if __name__ == "__main__":
    main()