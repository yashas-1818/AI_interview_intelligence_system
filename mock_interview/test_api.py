"""
FASTAPI ENDPOINT INTEGRATION TESTS
Tests all required endpoints of the AI Interview Intelligence System API.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from mock_interview.api import app

client = TestClient(app)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PDF = PROJECT_ROOT / "mock_interview" / "resume" / "test_data" / "resume.pdf"


def test_api_workflow():
    print("=" * 70)
    print("TESTING FASTAPI BACKEND WORKFLOW")
    print("=" * 70)

    # 1. Test Root
    print("\n[1] Testing GET /")
    res = client.get("/")
    assert res.status_code == 200, f"Root endpoint returned {res.status_code}"
    print("PASS: Root endpoint returned 200")

    # 2. Test Resume Upload
    print("\n[2] Testing POST /api/upload-resume")
    if SAMPLE_PDF.exists():
        with open(SAMPLE_PDF, "rb") as f:
            res = client.post(
                "/api/upload-resume",
                files={"file": ("resume.pdf", f, "application/pdf")},
            )
    else:
        res = client.post("/api/upload-resume")

    assert res.status_code == 200, f"Upload resume failed: {res.text}"
    cand_data = res.json()
    assert cand_data.get("success") is True
    assert "candidate" in cand_data
    candidate_name = cand_data["candidate"]["name"]
    session_id = cand_data["session_id"]
    print(f"PASS: Resume uploaded successfully for '{candidate_name}' (Session: {session_id})")

    # 3. Test Job Setup
    print("\n[3] Testing POST /api/setup-job")
    res = client.post(
        "/api/setup-job",
        json={
            "job_preset": "1",
            "session_id": session_id,
        },
    )
    assert res.status_code == 200, f"Setup job failed: {res.text}"
    job_data = res.json()
    assert job_data.get("success") is True
    assert "match_report" in job_data
    assert "strategy" in job_data
    match_pct = job_data["match_report"]["match_percentage"]
    print(f"PASS: Job setup complete. Match percentage: {match_pct:.1f}%")

    # 4. Test Start Interview
    print("\n[4] Testing POST /api/start-interview")
    res = client.post(
        "/api/start-interview",
        json={
            "use_llm": False,  # Deterministic rule-based for fast test execution
            "session_id": session_id,
        },
    )
    assert res.status_code == 200, f"Start interview failed: {res.text}"
    start_data = res.json()
    assert start_data.get("success") is True
    assert "question" in start_data
    first_q = start_data["question"]
    print(f"PASS: Interview started. First Question: '{first_q[:50]}...'")

    # 5. Test Status
    print("\n[5] Testing GET /api/status")
    res = client.get(f"/api/status?session_id={session_id}")
    assert res.status_code == 200, f"Status check failed: {res.text}"
    status_data = res.json()
    assert status_data.get("initialized") is True
    assert status_data.get("is_active") is True
    print(f"PASS: Status endpoint verified. Active category: {status_data.get('active_category')}")

    # 6. Test Submit Answer
    print("\n[6] Testing POST /api/submit-answer")
    test_answer = (
        "I am an AI and machine learning student with solid experience in Python, "
        "natural language processing, and scalable software pipelines."
    )
    res = client.post(
        "/api/submit-answer",
        json={
            "answer": test_answer,
            "session_id": session_id,
        },
    )
    assert res.status_code == 200, f"Submit answer failed: {res.text}"
    turn_data = res.json()
    assert turn_data.get("success") is True
    assessment = turn_data.get("previous_turn", {}).get("assessment", {})
    score = assessment.get("score")
    quality = assessment.get("quality")
    next_q = turn_data.get("next_question")
    print(f"PASS: Answer processed. Score: {score}/100, Quality: {quality}")
    print(f"      Next Question: '{next_q[:50]}...'")

    # 6b. Test Skip Question
    print("\n[6b] Testing POST /api/skip-question")
    res_skip = client.post(
        "/api/skip-question",
        json={"session_id": session_id},
    )
    assert res_skip.status_code == 200, f"Skip question failed: {res_skip.text}"
    skip_data = res_skip.json()
    assert skip_data.get("success") is True
    assert skip_data.get("skipped") is True
    assert skip_data.get("skipped_question") == next_q
    after_skip_q = skip_data.get("next_question")
    assert after_skip_q != next_q, "Next question after skip must not be the same question!"
    print(f"PASS: Skip question succeeded. Skipped: '{skip_data['skipped_question'][:40]}...'")
    print(f"      New Question: '{after_skip_q[:40]}...'")

    # 7. Test End Interview
    print("\n[7] Testing POST /api/end-interview")
    res = client.post(
        "/api/end-interview",
        json={"session_id": session_id},
    )
    assert res.status_code == 200, f"End interview failed: {res.text}"
    end_data = res.json()
    assert end_data.get("success") is True
    eval_result = end_data.get("evaluation", {})
    overall_score = eval_result.get("overall_score")
    reports_info = end_data.get("reports", {})
    html_filename = reports_info.get("html_filename")
    print(f"PASS: Interview ended. Overall Score: {overall_score}/100, Tier: {eval_result.get('performance_tier')}")
    print(f"      Reports generated: {reports_info.get('markdown_filename')}, {html_filename}")

    # 8. Test Serve Reports
    print(f"\n[8] Testing GET /api/reports/{html_filename}")
    res = client.get(f"/api/reports/{html_filename}")
    assert res.status_code == 200, f"Fetch report failed: {res.status_code}"
    assert "<!DOCTYPE html>" in res.text
    print("PASS: Generated HTML report served successfully.")

    # 9. Test Security / Path Traversal Prevention
    print("\n[9] Testing Security & Path Traversal Rejection")
    res_bad = client.get("/api/reports/..%2F..%2Fsecrets.txt")
    assert res_bad.status_code in (400, 403, 404), f"Path traversal not blocked! Got {res_bad.status_code}"
    print(f"PASS: Path traversal appropriately blocked (Status: {res_bad.status_code})")

    print("\n" + "=" * 70)
    print("ALL 9 FASTAPI ENDPOINT TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_api_workflow()
