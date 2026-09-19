# AI POWERED INTERVIEW INTELLIGENCE SYSTEM
### Autonomous, Adaptive, and Personalized Mock Interview Platform

---

## 1. Project Title & Overview
**AI Powered Interview Intelligence System** is an advanced engineering platform designed to simulate realistic, personalized, and adaptive job interviews. Unlike traditional interview preparation tools that display a static, predetermined list of questions, this system dynamically constructs an interview tailored specifically to a candidate's uploaded resume and target job description. It actively evaluates candidate answers in real time, adjusts technical difficulty, asks deep contextual follow-ups to probe ambiguities or skill gaps, and synthesizes an evidence-based **Interview Intelligence Report**.

---

## 2. Problem Statement
Traditional technical interview preparation exhibits major limitations:
- **Static & Generic Questionnaires**: Question banks ask generic queries without considering a candidate's actual projects, claimed skills, or target role requirements.
- **Lack of Adaptive Follow-up**: Real-world interviewers probe vague or evasive responses with targeted follow-ups. Static platforms fail to challenge the candidate or verify practical depth.
- **Disconnected Skill Gap Analysis**: Candidates rarely receive an interview that intentionally tests the delta (gap) between what their resume shows and what the job demands.
- **Superficial Feedback**: Candidates typically receive binary scores or generic comments rather than competency-based rubrics across technical depth, communication, completeness, and problem solving.

---

## 3. Motivation
In modern engineering hiring, technical competence is multidimensional. Candidates must articulate architectural trade-offs, explain failure modes, demonstrate communication clarity, and acknowledge skill gaps proactively. This project bridges the gap by building an AI interviewer that mimics a senior technical interviewer: challenging high performers with elevated difficulty, probing shallow explanations, and providing detailed post-interview intelligence dashboards for candidate readiness.

---

## 4. Key Objectives
1. **Resume Intelligence**: Automatically parse PDF resumes and extract candidate contact info, technical skill taxonomy, project architectures, and education.
2. **Job Description Intelligence**: Ingest unstructured job descriptions and identify core role requirements, required skills, preferred qualifications, and key responsibilities.
3. **Candidate-Job Match Engine**: Determine skill overlap, calculate match percentages, and pinpoint missing required/preferred skills.
4. **Adaptive Interview Strategy**: Formulate a sequential interview roadmap (`introduction` → `resume` → `project` → `technical` → `role_specific` → `skill_gap` → `behavioral` → `situational` → `closing`).
5. **Multi-Model Orchestration with Zero-Crash Fallback**: Leverage Google Gemini generative models for contextual questions and analysis, with deterministic local fallback handling rate limits (`429 RESOURCE_EXHAUSTED`), timeouts, or network errors seamlessly.
6. **Dynamic Difficulty & Follow-up**: Adapt difficulty between Level 1 and 5 in real time, triggering targeted follow-ups whenever answers lack depth or clarity.
7. **Comprehensive Evaluation & Reporting**: Synthesize a comprehensive performance report assessing 5 core competencies, categorizing strengths, weaknesses, and prioritized preparation recommendations.
8. **Multi-Modal Interfaces**: Deliver an interactive terminal CLI, automated demonstration mode (`--demo`), and a FastAPI web application with speech-to-text dictation and voice synthesis.

---

## 5. System Architecture

```
                                 +-------------------------+
                                 |   Candidate Resume PDF  |
                                 +-------------------------+
                                              |
                                              v
                                 +-------------------------+
                                 |      Resume Parser      |
                                 +-------------------------+
                                              |
                                              v
                                 +-------------------------+
                                 |    Candidate Profile    |
                                 +-------------------------+
                                              |
     +-------------------------+              |
     | Target Job Description  |              |
     +-------------------------+              |
                  |                           |
                  v                           |
     +-------------------------+              |
     |   Job Description Parser|              |
     +-------------------------+              |
                  |                           |
                  v                           |
     +-------------------------+              |
     |       Job Profile       |              |
     +-------------------------+              |
                  |                           |
                  +-------------+-------------+
                                |
                                v
                   +-------------------------+
                   |  Candidate-Job Matcher  |
                   +-------------------------+
                                |
                                v
                   +-------------------------+
                   |       Match Report      |
                   | (Match %, Gaps, Overlap)|
                   +-------------------------+
                                |
                                v
                   +-------------------------+
                   |    Interview Strategy   |
                   +-------------------------+
                                |
                                v
            +---------------------------------------+
            |         Interview Orchestrator        |
            +---------------------------------------+
                                |
             +------------------+-------------------+
             |                                      |
             v                                      v
     [ Gemini LLM ]                         [ Fallback Engine ]
  (Flash 3.7 / 3.6 API)                  (Deterministic Templates)
             |                                      |
             +------------------+-------------------+
                                |
                                v
                   +-------------------------+
                   |    Generated Question   |
                   +-------------------------+
                                |
                                v
                   +-------------------------+
                   |     Candidate Answer    |
                   +-------------------------+
                                |
                                v
                   +-------------------------+
                   |     Answer Analyzer     |
                   | (Rule-Based + LLM Eval) |
                   +-------------------------+
                                |
                                v
                   +-------------------------+
                   |     Decision Engine     |
                   | (Follow-up, Category,   |
                   |  Difficulty Adaptation) |
                   +-------------------------+
                                |
                                v
                   +-------------------------+
                   |    Conversation State   |
                   +-------------------------+
                                |
               (Repeat until all categories complete)
                                |
                                v
                   +-------------------------+
                   |    Evaluation Engine    |
                   | (5 Competencies, Tier)  |
                   +-------------------------+
                                |
                                v
                   +-------------------------+
                   |     Report Generator    |
                   |  (Markdown & HTML Dash) |
                   +-------------------------+
```

---

## 6. Module Architecture & File Map

```
AI_Interview_Intelligence_System/
│
├── mock_interview/
│   ├── app.py                     # Multi-mode Application Entry Point (CLI, Demo, Web)
│   ├── api.py                     # FastAPI REST API Backend
│   ├── test_api.py                # FastAPI Automated Integration Test Suite
│   │
│   ├── resume/                    # Resume Ingestion & Profiling Module
│   │   ├── parser.py              # PyMuPDF PDF Text Extraction & Cleaning
│   │   ├── profile.py             # Pydantic Candidate Profile Schema
│   │   ├── analyzer.py            # Skills, Experience, and Education Extractor
│   │   └── test_data/             # Sample Candidate Resumes (resume.pdf)
│   │
│   ├── job/                       # Job Description Intelligence Module
│   │   ├── parser.py              # Section & Bullet Normalization
│   │   ├── profile.py             # Structured Job Profile Schema
│   │   ├── analyzer.py            # Requirements, Responsibilities & Skills Extractor
│   │   └── matcher.py             # Candidate-Job Skill Matcher & Gap Detector
│   │
│   ├── interview/                 # Core Adaptive Interview Engine (Stabilized & Frozen)
│   │   ├── conversation_state.py  # Session State & Turn History Tracker
│   │   ├── strategy.py            # Category Sequencing & Focus Formulator
│   │   ├── question_generator.py  # Deterministic Contextual Question Bank
│   │   ├── answer_analyzer.py     # Multi-metric Rubric (Score, Depth, Vagueness)
│   │   ├── decision_engine.py     # Adaptive Decision Logic (Difficulty, Follow-up)
│   │   ├── orchestrator.py        # Central State Controller & Execution Driver
│   │   └── test_full_interview_flow.py # 14-Check End-to-End Test Suite
│   │
│   ├── llm/                       # LLM Provider & Adapter Layer
│   │   ├── gemini_provider.py     # Dual-model Gemini Client with Fast Fallback
│   │   ├── prompts.py             # Few-shot System Prompts
│   │   └── interview_adapter.py   # Question Generation & Answer Evaluation Adapter
│   │
│   ├── evaluation/                # Post-Interview Evaluation Engine
│   │   ├── evaluator.py           # Competency Rubric & Performance Tier Calculator
│   │   └── test_evaluator.py      # Evaluation Unit Tests
│   │
│   ├── report/                    # Intelligence Report Generation Module
│   │   ├── generator.py           # Structured JSON, Markdown & HTML Exporters
│   │   └── test_report.py         # Report Generation Unit Tests
│   │
│   └── web/                       # Modern Browser Interface
│       └── index.html             # Responsive Dark-Mode Glassmorphism Web App
│
├── reports/                       # Export Directory for Generated HTML & Markdown Reports
├── requirements.txt               # Project Dependencies
└── README.md                      # Comprehensive Technical Documentation
```

---

## 7. Technology Stack
- **Programming Language**: Python 3.11+
- **PDF Extraction**: PyMuPDF (`pymupdf` / `fitz`)
- **Data Modeling & Validation**: Pydantic v2
- **External AI Model**: Google Gemini (`google-genai` SDK, `gemini-3.7-flash` with `gemini-3.6-flash` fallback)
- **Web Backend**: FastAPI & Uvicorn (ASGI)
- **Frontend**: Vanilla HTML5, CSS3 (Modern Glassmorphism & Custom Properties), and JavaScript (ES6+)
- **Audio & Speech**: Web Speech API (`SpeechRecognition` for voice input, `SpeechSynthesis` for question reading)
- **Reporting**: GitHub-Flavored Markdown & Self-Contained Responsive HTML5/CSS Dashboards

---

## 8. Resume Ingestion Pipeline
1. `extract_text_from_pdf()` opens the PDF file via PyMuPDF.
2. `normalize_pdf_text()` fixes broken line hyphens (e.g. `natural-\nlanguage` → `natural-language`), strips excessive whitespace, and removes duplicate empty lines.
3. `build_candidate_profile()` scans the cleaned text:
   - Identifies candidate name, email, phone, and LinkedIn.
   - Extracts categorized technical skills (languages, frameworks, databases, tools).
   - Identifies completed projects, technologies used, and descriptions.
   - Extracts education history, degrees, and institutions.

---

## 9. Job Analysis Pipeline
1. `extract_job_text()` normalizes bullet points, hyphens, and whitespace.
2. `analyze_job_description()` parses sections using regex headers:
   - Role Title & Organization.
   - Required Skills vs. Preferred / Nice-to-have Skills.
   - Core Responsibilities.
   - Educational & Experience Qualifications.

---

## 10. Candidate-Job Matcher
`build_match_report(candidate, job)` computes:
- **Required Skill Match Percentage**: `(matched_required / total_required) * 100`.
- **Matched Skills**: Overlap between candidate resume and job requirements.
- **Identified Skill Gaps**: Crucial job requirements missing from candidate resume (e.g. PyTorch, Docker). These gaps are forwarded directly to the interview strategy to be explored during the interview.

---

## 11. Interview Strategy
`build_interview_strategy()` establishes a 9-category interview roadmap:
1. `introduction`: Greeting, career overview, professional background.
2. `resume`: Verification of claimed experience, tools, and background.
3. `project`: Deep-dive into technical architecture, components, and trade-offs.
4. `technical`: Core programming, algorithms, and domain knowledge.
5. `role_specific`: Production deployment, testing, monitoring, data drift.
6. `skill_gap`: Probing candidate understanding of identified missing skills (e.g. PyTorch).
7. `behavioral`: Conflict resolution, prioritization, and team collaboration.
8. `situational`: Crisis management, production latency spikes, incident response.
9. `closing`: Candidate reflection, future outlook, and wrap-up.

---

## 12. Adaptive Interview Mechanics & Decision Engine
During each turn:
1. **Answer Analysis**:
   - Scores answer quality (`excellent`, `good`, `moderate`, `weak`).
   - Measures technical depth level (`high`, `medium`, `low`, `minimal`).
   - Detects clarity, completeness, and vagueness indicators.
2. **Hybrid Decision Logic**:
   - If an answer is vague or lacks concrete implementation specifics: triggers a `follow_up` question without permanently altering the category roadmap.
   - If an answer exhibits high quality and deep technical mastery: increases interview difficulty (`Level 1` through `Level 5`).
   - If quality threshold is satisfied: advances to the next category in the roadmap.

---

## 13. LLM Integration & Zero-Crash Fallback Architecture
External generative APIs frequently encounter network latency, socket drops, rate limits (`429 RESOURCE_EXHAUSTED`), or 503 high demand. The system enforces a zero-crash architecture:
- **Fast Failover**: Uses `HttpOptions(timeout=10000)` to eliminate hanging sockets.
- **Quota Exceeded Handling**: When a 429 occurs, it immediately catches the exception without futile retries, logs the incident, and activates the local deterministic template generator.
- **The candidate never experiences an application freeze or crash.**

---

## 14. Post-Interview Evaluation Engine
`InterviewEvaluator` assesses the full session across **5 Core Competencies (0–100 Scale)**:
1. **Technical Knowledge (30% weight)**: Technical depth level, mastery of algorithms and concepts.
2. **Communication (20% weight)**: Clarity, conciseness, structural flow, minimal filler phrasing.
3. **Relevance (20% weight)**: Direct alignment with the specific question asked.
4. **Completeness (15% weight)**: Coverage of required problem-solving dimensions.
5. **Problem Solving (15% weight)**: Methodical diagnosis, handling trade-offs, and practical execution.

### Performance Tiers:
- **80% – 100%**: Advanced / Recommended
- **65% – 79.9%**: Proficient / Solid Candidate
- **50% – 64.9%**: Developing / Promising
- **Below 50%**: Needs Substantial Preparation

---

## 15. Intelligence Report Generation
`ReportGenerator` creates:
1. **JSON Report**: Machine-readable structured dictionary containing all analytics.
2. **Markdown Report (`report_<session_id>.md`)**: Formatted for GitHub, IDEs, and text viewing.
3. **Interactive HTML Dashboard (`report_<session_id>.html`)**: A responsive dashboard containing:
   - Overall Score ring & Performance Tier badge.
   - Competency breakdown visual progress bars.
   - Category performance breakdown table.
   - Identified strengths and weaknesses.
   - Skill-gap analysis.
   - Actionable preparation recommendations.
   - Question-by-question transcript with score, quality, and technical depth tags.

---

## 16. REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the browser web application UI (`index.html`) |
| `POST` | `/api/upload-resume` | Upload candidate resume PDF, returns parsed `CandidateProfile` |
| `POST` | `/api/setup-job` | Select job preset or paste custom job, returns `JobProfile` and `MatchReport` |
| `POST` | `/api/start-interview` | Initializes `InterviewOrchestrator` and returns the first question |
| `POST` | `/api/submit-answer` | Submits candidate answer, returns assessment, decision, and next question |
| `GET` | `/api/status` | Returns sanitized interview status without exposing internal keys |
| `POST` | `/api/end-interview` | Concludes interview, runs evaluator, and generates report files |
| `GET` | `/api/reports/{filename}`| Safely serves generated HTML or Markdown report files |

---

## 17. Installation & Setup

### Prerequisites
- Python 3.11 or higher
- PowerShell (Windows) or Bash (Linux/macOS)

### 1. Clone & Navigate to Repository
```powershell
cd D:\AI_Interview_Intelligence_System
```

### 2. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Gemini API Key (Optional)
Create a `.env` file in the project root:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: If no API key is provided, or if quota is exhausted, the system automatically uses the deterministic fallback engine without crashing.)*

---

## 18. How to Run the System

### Mode 1: Interactive Terminal CLI (Default)
Conduct an interactive interview right inside your terminal:
```powershell
.\venv\Scripts\python.exe -m mock_interview.app
```
- Step 1: Select resume PDF (press Enter to use default `resume.pdf` or specify custom path).
- Step 2: Choose job preset (1: AI/ML Engineer, 2: Full Stack, 3: Data Scientist, 4: Custom).
- Step 3: Answer questions interactively. Type your response and press Enter.
  - Type `:skip` to pass on a question.
  - Type `:quit` to finish early and generate your report.
  - End a line with `\` to write multiline paragraphs.

### Mode 2: Automated Demo Mode (`--demo`)
Run an automated end-to-end mock interview simulation with contextual candidate answers:
```powershell
.\venv\Scripts\python.exe -m mock_interview.app --demo
```
*Executes all 9 categories, dynamically adapts difficulty, and outputs generated reports in `reports/`.*

### Mode 3: Web Server & Modern Browser Interface (`--web`)
Launch the FastAPI server and open the web dashboard:
```powershell
.\venv\Scripts\python.exe -m mock_interview.app --web
```
Open your browser at:
```
http://127.0.0.1:8000
```
- **Stage 1 (Setup)**: Drag-and-drop resume PDF or click "Use Built-in Sample Resume".
- **Stage 2 (Match Intelligence)**: Inspect match percentage, matched skills, and identified skill gaps.
- **Stage 3 (Live Interview Room)**:
  - Hear questions read aloud via Web Speech Synthesis.
  - Dictate your answers using the microphone (`🎙️ Dictate Answer`).
  - View live difficulty stars and previous answer assessment badges.
- **Stage 4 (Intelligence Report)**: View competency scores, performance tier, strengths, weaknesses, and direct links to generated reports.

---

## 19. Automated Verification Test Suite
Run the complete suite of tests to verify all system components:

```powershell
# 1. Test FastAPI Backend & REST Endpoints
.\venv\Scripts\python.exe -m mock_interview.test_api

# 2. Test Evaluation Engine
.\venv\Scripts\python.exe -m mock_interview.evaluation.test_evaluator

# 3. Test Report Generator
.\venv\Scripts\python.exe -m mock_interview.report.test_report

# 4. Test 14-Check End-to-End Adaptive Interview Flow
.\venv\Scripts\python.exe -m mock_interview.interview.test_full_interview_flow

# 5. Test Automated Demonstration CLI
.\venv\Scripts\python.exe -m mock_interview.app --demo
```

---

## 20. Example Demonstration Walkthrough
1. **Candidate**: H S Yashas Gowda (B.E. Computer Science, AI/ML specialization).
2. **Target Role**: AI/ML Engineer at Tech Corp.
3. **Match Analysis**: 66.7% match on required skills (`python`, `machine learning`, `nlp`, `sql`). Gaps detected: `pytorch`, `docker`.
4. **Adaptive Progression**:
   - Candidate gives high-depth explanation of Skylark modular architecture in `project` domain. Difficulty increases to Level 3.
   - Interviewer pivots to `skill_gap` domain, asking about neural network pipelines and PyTorch.
   - Candidate provides structured, honest response acknowledging lack of production PyTorch experience while explaining tensor fundamentals.
   - System recognizes candidate honesty and technical foundation, asks follow-up, and progresses cleanly.
5. **Final Evaluation**:
   - Overall Score: **70.7 / 100** (Proficient / Solid Candidate)
   - Technical Knowledge: **77.7%**
   - Problem Solving: **70.0%**
   - Communication: **67.0%**
   - Relevance: **65.0%**
   - Completeness: **65.0%**
   - Reports saved: `reports/report_20260915_120836.html` and `.md`.

---

## 21. Limitations & Future Enhancements
- **Multi-Modal Video Analysis**: Future iterations could integrate computer vision (MediaPipe / OpenCV) for gaze tracking, posture, and facial confidence analysis.
- **Live Code Execution Sandbox**: Integrating a WebAssembly / Docker-based code sandbox to allow live algorithm testing.
- **Enterprise Multi-Tenancy**: Expanding beyond in-memory sessions to distributed PostgreSQL and Redis session caches for multi-user university deployments.

---

## 22. Authors & Acknowledgments
Developed as a final-year engineering capstone project: **AI Powered Interview Intelligence System**. Built with a commitment to modularity, architectural robustness, zero-crash design, and explainable AI evaluation.
