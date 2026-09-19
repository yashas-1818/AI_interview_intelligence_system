"""
AI POWERED INTERVIEW INTELLIGENCE SYSTEM
FastAPI Application & REST Backend Service

Exposes endpoints for:
- POST /api/upload-resume
- POST /api/setup-job
- POST /api/start-interview
- POST /api/submit-answer
- GET  /api/status
- POST /api/end-interview
- GET  /api/reports/{filename}
- GET  / (serves web UI)
"""

import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymupdf
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from mock_interview.resume.parser import normalize_pdf_text
from mock_interview.resume.analyzer import build_candidate_profile
from mock_interview.job.parser import extract_job_text
from mock_interview.job.analyzer import analyze_job_description
from mock_interview.job.matcher import build_match_report
from mock_interview.interview.strategy import build_interview_strategy
from mock_interview.interview.orchestrator import InterviewOrchestrator
from mock_interview.evaluation.evaluator import InterviewEvaluator
from mock_interview.report.generator import ReportGenerator


# ======================================================================
# DIRECTORY CONFIGURATION
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = PROJECT_ROOT / "reports"
WEB_DIR = PROJECT_ROOT / "mock_interview" / "web"
TEST_DATA_DIR = PROJECT_ROOT / "mock_interview" / "resume" / "test_data"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ======================================================================
# FASTAPI APP & MIDDLEWARE
# ======================================================================

app = FastAPI(
    title="AI Powered Interview Intelligence System",
    description="Adaptive mock interview platform with live analysis and intelligence reports.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ======================================================================
# IN-MEMORY SESSION STORE
# ======================================================================

class InterviewSession:
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.candidate_profile: Any = None
        self.job_profile: Any = None
        self.match_report: Dict[str, Any] = {}
        self.strategy: Dict[str, Any] = {}
        self.orchestrator: Optional[InterviewOrchestrator] = None
        self.evaluation_result: Optional[Dict[str, Any]] = None
        self.saved_reports: Dict[str, Path] = {}


sessions: Dict[str, InterviewSession] = {}
active_session_id: Optional[str] = None


def get_or_create_session(session_id: Optional[str] = None) -> InterviewSession:
    global active_session_id
    sid = session_id or active_session_id
    if not sid or sid not in sessions:
        sid = str(uuid.uuid4())[:8]
        sessions[sid] = InterviewSession(sid)
        active_session_id = sid
    return sessions[sid]


# ======================================================================
# REQUEST & RESPONSE MODELS
# ======================================================================

class JobSetupRequest(BaseModel):
    job_description: Optional[str] = None
    job_preset: Optional[str] = "1"
    session_id: Optional[str] = None


class StartInterviewRequest(BaseModel):
    use_llm: bool = True
    session_id: Optional[str] = None


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1)
    session_id: Optional[str] = None


class SkipQuestionRequest(BaseModel):
    session_id: Optional[str] = None


class EndInterviewRequest(BaseModel):
    session_id: Optional[str] = None


# Preset job definitions
JOB_PRESETS: Dict[str, Dict[str, str]] = {
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
""",
    },
}


# ======================================================================
# API ENDPOINTS
# ======================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serve the sleek Web Application Interface."""
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(
        """
        <html>
            <head><title>AI Mock Interview System</title></head>
            <body style="font-family: sans-serif; background: #0b0f19; color: #f8fafc; padding: 40px; text-align: center;">
                <h1>AI Powered Interview Intelligence System</h1>
                <p>FastAPI backend is operational. Place <code>mock_interview/web/index.html</code> to view the full frontend.</p>
                <p><a href="/docs" style="color: #38bdf8;">Explore Interactive API Documentation (Swagger)</a></p>
            </body>
        </html>
        """
    )


@app.post("/api/upload-resume")
async def upload_resume(
    file: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Query(None),
):
    """
    Accepts candidate PDF resume, extracts structured information,
    and initializes candidate profile.
    """
    session = get_or_create_session(session_id)

    if file and file.filename:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF resumes are supported.")
        try:
            content = await file.read()
            doc = pymupdf.open(stream=content, filetype="pdf")
            pages = [page.get_text() for page in doc]
            doc.close()
            resume_text = normalize_pdf_text("\n".join(pages))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to read PDF resume: {str(exc)}")
    else:
        # Fallback to test_data resume if none uploaded
        default_pdfs = sorted(TEST_DATA_DIR.glob("*.pdf"))
        if not default_pdfs:
            raise HTTPException(status_code=400, detail="No PDF uploaded and no default resume found in test_data.")
        doc = pymupdf.open(default_pdfs[0])
        pages = [page.get_text() for page in doc]
        doc.close()
        resume_text = normalize_pdf_text("\n".join(pages))

    candidate_profile = build_candidate_profile(resume_text)
    session.candidate_profile = candidate_profile

    skills_flat = []
    if isinstance(candidate_profile.skills, dict):
        for s_list in candidate_profile.skills.values():
            if isinstance(s_list, list):
                skills_flat.extend(s_list)
    elif isinstance(candidate_profile.skills, list):
        skills_flat.extend(candidate_profile.skills)

    return {
        "success": True,
        "session_id": session.session_id,
        "candidate": {
            "name": candidate_profile.candidate.name or "Candidate",
            "email": candidate_profile.candidate.email,
            "phone": candidate_profile.candidate.phone,
            "skills": skills_flat,
            "summary": candidate_profile.summary,
            "projects": [p.dict() if hasattr(p, "dict") else vars(p) for p in candidate_profile.projects],
            "education": [e.dict() if hasattr(e, "dict") else vars(e) for e in candidate_profile.education],
        },
    }


@app.post("/api/setup-job")
async def setup_job(request: JobSetupRequest):
    """
    Parses target job description, performs candidate-job matching,
    and generates personalized interview strategy.
    """
    session = get_or_create_session(request.session_id)

    # Ensure candidate profile exists
    if not session.candidate_profile:
        # Auto-load test_data resume
        default_pdfs = sorted(TEST_DATA_DIR.glob("*.pdf"))
        if default_pdfs:
            doc = pymupdf.open(default_pdfs[0])
            pages = [page.get_text() for page in doc]
            doc.close()
            resume_text = normalize_pdf_text("\n".join(pages))
            session.candidate_profile = build_candidate_profile(resume_text)
        else:
            raise HTTPException(
                status_code=400,
                detail="Candidate profile not found. Please upload a resume first.",
            )

    # Determine job description
    if request.job_description and request.job_description.strip():
        job_raw_text = request.job_description.strip()
    elif request.job_preset and request.job_preset in JOB_PRESETS:
        job_raw_text = JOB_PRESETS[request.job_preset]["description"]
    else:
        job_raw_text = JOB_PRESETS["1"]["description"]

    job_text = extract_job_text(job_raw_text)
    job_profile = analyze_job_description(job_text)
    session.job_profile = job_profile

    # Candidate-Job Matching
    match_report = build_match_report(session.candidate_profile, job_profile)
    session.match_report = match_report

    # Strategy Generation
    strategy = build_interview_strategy(session.candidate_profile, job_profile, match_report)
    session.strategy = strategy

    return {
        "success": True,
        "session_id": session.session_id,
        "job_profile": {
            "role_title": job_profile.role_title,
            "company": job_profile.company,
            "required_skills": job_profile.required_skills,
            "preferred_skills": job_profile.preferred_skills,
            "responsibilities": job_profile.responsibilities[:5],
        },
        "match_report": {
            "match_percentage": match_report.get("required_skill_match_percentage", 0.0),
            "matched_required": match_report.get("required_skills", {}).get("matched", []),
            "missing_required": match_report.get("required_skills", {}).get("missing", []),
            "matched_preferred": match_report.get("preferred_skills", {}).get("matched", []),
            "missing_preferred": match_report.get("preferred_skills", {}).get("missing", []),
        },
        "strategy": {
            "categories": strategy.get("categories", []),
            "total_categories": len(strategy.get("categories", [])),
            "primary_focus": strategy.get("primary_focus", []),
        },
    }


@app.post("/api/start-interview")
async def start_interview(request: StartInterviewRequest):
    """
    Initializes the adaptive InterviewOrchestrator and yields the first question.
    """
    session = get_or_create_session(request.session_id)

    if not session.candidate_profile or not session.job_profile:
        raise HTTPException(
            status_code=400,
            detail="Session incomplete. Please provide resume and job description first.",
        )

    orchestrator = InterviewOrchestrator(
        candidate_profile=session.candidate_profile,
        job_profile=session.job_profile,
        match_report=session.match_report,
        strategy=session.strategy,
        use_llm=request.use_llm,
    )
    session.orchestrator = orchestrator

    start_result = orchestrator.start()

    return {
        "success": True,
        "session_id": session.session_id,
        "question": start_result.get("question", orchestrator.get_current_question()),
        "category": start_result.get("category", orchestrator.get_current_category()),
        "active_category": start_result.get("active_category", orchestrator.get_active_category()),
        "difficulty": start_result.get("difficulty", orchestrator.state.current_difficulty),
        "is_active": orchestrator.state.is_active,
        "roadmap": session.strategy.get("categories", []),
    }


@app.post("/api/skip-question")
async def skip_question(request: SkipQuestionRequest):
    """
    Candidate skips the current question. The question is recorded in
    skipped_questions and will never be repeated. The next unique question
    is returned, or the category is advanced if questions are exhausted.
    """
    session = get_or_create_session(request.session_id)
    orchestrator = session.orchestrator

    if not orchestrator or not orchestrator.state.is_active:
        raise HTTPException(
            status_code=400,
            detail="No active interview session. Please start the interview first.",
        )

    result = orchestrator.skip_question()
    return {
        "success": True,
        "session_id": session.session_id,
        "skipped": True,
        "skipped_question": result.get("skipped_question", ""),
        "next_question": result.get("next_question", ""),
        "current_category": orchestrator.get_current_category(),
        "active_category": orchestrator.get_active_category(),
        "current_difficulty": orchestrator.state.current_difficulty,
        "is_active": orchestrator.state.is_active,
        "completed_categories": orchestrator.state.completed_categories,
        "questions_completed": len(orchestrator.state.answers_received),
        "previous_turn": {
            "question": result.get("skipped_question", ""),
            "answer": ":skip",
            "category": result.get("category", ""),
            "assessment": {
                "quality": "skipped",
                "score": 0.0,
                "technical_depth": "skipped",
                "clarity": "skipped",
                "needs_followup": False,
            },
            "decision": {
                "action": "skip",
                "trigger_followup": False,
                "complete_category": False,
                "next_category": result.get("next_category"),
            },
        },
    }


@app.post("/api/submit-answer")
async def submit_answer(request: SubmitAnswerRequest):
    """
    Receives candidate answer, analyzes performance, adaptively adjusts
    difficulty/follow-up, and returns the next question or concludes.
    """
    session = get_or_create_session(request.session_id)
    orchestrator = session.orchestrator

    if not orchestrator or not orchestrator.state.is_active:
        raise HTTPException(
            status_code=400,
            detail="No active interview session. Please start the interview first.",
        )

    # Route explicit skip commands to dedicated skip handler
    if request.answer.strip().lower() in (":skip", "skip", "/skip"):
        return await skip_question(SkipQuestionRequest(session_id=request.session_id))

    prev_question = orchestrator.get_current_question()
    prev_category = orchestrator.get_current_category()

    result = orchestrator.process_answer(request.answer)
    assessment = result.get("assessment", {})
    decision = result.get("decision", {})

    is_active = orchestrator.state.is_active

    return {
        "success": True,
        "session_id": session.session_id,
        "previous_turn": {
            "question": prev_question,
            "answer": request.answer,
            "category": prev_category,
            "assessment": {
                "quality": assessment.get("quality", "moderate"),
                "score": assessment.get("score", 50.0),
                "technical_depth": assessment.get("technical_depth_level", "medium"),
                "clarity": assessment.get("clarity_level", "good"),
                "needs_followup": assessment.get("needs_followup", False),
            },
            "decision": {
                "action": decision.get("action", "next"),
                "trigger_followup": decision.get("trigger_followup", False),
                "complete_category": decision.get("complete_category", False),
                "next_category": decision.get("next_category"),
            },
        },
        "current_difficulty": orchestrator.state.current_difficulty,
        "current_category": orchestrator.get_current_category(),
        "active_category": orchestrator.get_active_category(),
        "next_question": result.get("next_question"),
        "is_active": is_active,
        "completed_categories": orchestrator.state.completed_categories,
        "questions_completed": len(orchestrator.state.answers_received),
    }


@app.get("/api/status")
async def get_status(session_id: Optional[str] = Query(None)):
    """
    Returns current interview state without exposing sensitive credentials.
    """
    session = get_or_create_session(session_id)
    if not session.orchestrator:
        return {
            "initialized": False,
            "session_id": session.session_id,
            "has_candidate": session.candidate_profile is not None,
            "has_job": session.job_profile is not None,
        }

    state = session.orchestrator.get_state()
    return {
        "initialized": True,
        "session_id": session.session_id,
        "candidate_name": state.get("candidate_name"),
        "role": state.get("role"),
        "current_category": state.get("current_category"),
        "active_category": state.get("active_category"),
        "current_difficulty": state.get("current_difficulty"),
        "questions_asked": len(state.get("questions_asked", [])),
        "answers_received": len(state.get("answers_received", [])),
        "completed_categories": state.get("completed_categories", []),
        "is_active": state.get("is_active", False),
    }


@app.post("/api/end-interview")
async def end_interview(request: EndInterviewRequest):
    """
    Concludes interview, invokes InterviewEvaluator and ReportGenerator,
    saves HTML and Markdown reports, and returns intelligence summary.
    """
    session = get_or_create_session(request.session_id)
    orchestrator = session.orchestrator

    if not orchestrator:
        raise HTTPException(status_code=400, detail="No interview session found to evaluate.")

    if orchestrator.state.is_active:
        orchestrator.state.end_session()

    final_state = orchestrator.get_state()

    # Evaluation Engine
    evaluator = InterviewEvaluator(
        candidate_profile=session.candidate_profile,
        job_profile=session.job_profile,
        match_report=session.match_report,
    )
    evaluation_result = evaluator.evaluate(final_state)
    session.evaluation_result = evaluation_result

    # Report Generator
    report_gen = ReportGenerator(
        candidate_profile=session.candidate_profile,
        job_profile=session.job_profile,
        match_report=session.match_report,
        evaluation_result=evaluation_result,
        conversation_history=final_state.get("conversation_history", []),
    )

    sid = final_state.get("session_id", session.session_id)
    saved_files = report_gen.save_report(REPORTS_DIR, f"report_{sid}")
    session.saved_reports = saved_files

    md_filename = saved_files["markdown"].name
    html_filename = saved_files["html"].name

    return {
        "success": True,
        "session_id": sid,
        "evaluation": evaluation_result,
        "reports": {
            "markdown_url": f"/api/reports/{md_filename}",
            "html_url": f"/api/reports/{html_filename}",
            "markdown_filename": md_filename,
            "html_filename": html_filename,
        },
    }


@app.get("/api/reports/{filename}")
async def get_report_file(filename: str):
    """
    Safely serves generated Markdown and HTML report files,
    preventing directory traversal attacks.
    """
    # Restrict to safe filename
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename format.")

    if not (filename.endswith(".html") or filename.endswith(".md")):
        raise HTTPException(status_code=400, detail="Only HTML and Markdown reports may be accessed.")

    safe_path = (REPORTS_DIR / filename).resolve()

    # Ensure path is strictly inside REPORTS_DIR
    if not str(safe_path).startswith(str(REPORTS_DIR.resolve())):
        raise HTTPException(status_code=403, detail="Access denied.")

    if not safe_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found.")

    media_type = "text/html" if filename.endswith(".html") else "text/markdown"
    return FileResponse(safe_path, media_type=media_type)
