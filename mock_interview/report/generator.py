from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ReportGenerator:
    """
    Generates structured Interview Intelligence Reports.

    Consumes:
    - Candidate Profile
    - Job Profile
    - Match Report
    - Evaluation Result (from InterviewEvaluator)
    - Conversation History (optional, if not in evaluation_result)

    Produces:
    - Structured dictionary
    - Markdown report
    - Responsive HTML dashboard report
    """

    def __init__(
        self,
        candidate_profile: Any = None,
        job_profile: Any = None,
        match_report: Optional[Dict[str, Any]] = None,
        evaluation_result: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ):
        self.candidate_profile = candidate_profile
        self.job_profile = job_profile
        self.match_report = match_report or {}
        self.evaluation_result = evaluation_result or {}
        self.conversation_history = conversation_history or []

    # =============================================================
    # UTILITY HELPERS
    # =============================================================

    @staticmethod
    def _to_dict(obj: Any) -> Dict[str, Any]:
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "__dict__"):
            return vars(obj)
        return {}

    # =============================================================
    # STRUCTURED REPORT BUILDER
    # =============================================================

    def build_report(
        self,
        evaluation_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Assemble the comprehensive structured report dictionary.
        """
        eval_data = evaluation_result or self.evaluation_result
        cand_data = self._to_dict(self.candidate_profile)
        job_data = self._to_dict(self.job_profile)

        # Candidate Info
        cand_name = (
            eval_data.get("candidate_name")
            or cand_data.get("candidate", {}).get("name")
            or cand_data.get("name")
            or "Candidate"
        )
        cand_email = cand_data.get("candidate", {}).get("email") or cand_data.get("email", "N/A")
        cand_education = cand_data.get("education", [])

        # Job Info
        role = (
            eval_data.get("role")
            or job_data.get("role_title")
            or job_data.get("title")
            or "Target Role"
        )
        company = job_data.get("company", "Target Organization")

        # Match Info
        match_pct = self.match_report.get("required_skill_match_percentage", 0.0)
        req_matched = self.match_report.get("required_skills", {}).get("matched", [])
        req_missing = self.match_report.get("required_skills", {}).get("missing", [])
        pref_matched = self.match_report.get("preferred_skills", {}).get("matched", [])
        pref_missing = self.match_report.get("preferred_skills", {}).get("missing", [])

        # Evaluation Data
        overall_score = eval_data.get("overall_score", 0.0)
        performance_tier = eval_data.get("performance_tier", "Evaluated")
        competencies = eval_data.get("competency_scores", {})
        category_evals = eval_data.get("category_evaluations", {})
        strengths = eval_data.get("strengths", [])
        weaknesses = eval_data.get("weaknesses", [])
        recommendations = eval_data.get("recommendations", [])
        skill_gap_summary = eval_data.get("skill_gap_summary", {})
        questions = eval_data.get("question_breakdown", self.conversation_history)

        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "session_id": eval_data.get("session_id", "session"),
                "system_name": "AI Powered Interview Intelligence System",
            },
            "candidate": {
                "name": cand_name,
                "email": cand_email,
                "education": cand_education,
            },
            "job": {
                "role": role,
                "company": company,
            },
            "candidate_job_match": {
                "match_percentage": match_pct,
                "required_matched": req_matched,
                "required_missing": req_missing,
                "preferred_matched": pref_matched,
                "preferred_missing": pref_missing,
            },
            "interview_summary": {
                "overall_score": overall_score,
                "performance_tier": performance_tier,
                "total_questions": len(questions),
                "max_difficulty_reached": eval_data.get("max_difficulty_reached", 1),
            },
            "competency_scores": competencies,
            "category_evaluations": category_evals,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "skill_gap_summary": skill_gap_summary,
            "recommendations": recommendations,
            "question_breakdown": questions,
            # 10 Evidence-Based Intelligence Sections
            "executive_summary": eval_data.get("executive_summary", {}),
            "competency_analysis": eval_data.get("competency_analysis", []),
            "interview_journey": eval_data.get("interview_journey", []),
            "difficulty_progression": eval_data.get("difficulty_progression", {}),
            "followup_intelligence": eval_data.get("followup_intelligence", {}),
            "skill_gap_analysis": eval_data.get("skill_gap_analysis", {}),
            "strongest_responses": eval_data.get("strongest_responses", []),
            "improvement_areas": eval_data.get("improvement_areas", []),
            "action_plan": eval_data.get("action_plan", {}),
            "final_assessment": eval_data.get("final_assessment", {}),
        }

    # =============================================================
    # MARKDOWN REPORT
    # =============================================================

    def generate_markdown(
        self,
        report_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a comprehensive, evidence-based Markdown report covering all 10 intelligence sections.
        """
        data = report_data or self.build_report()

        exec_sum = data.get("executive_summary", {})
        comp_anal = data.get("competency_analysis", [])
        journey = data.get("interview_journey", [])
        diff_prog = data.get("difficulty_progression", {})
        followups = data.get("followup_intelligence", {})
        skill_gaps = data.get("skill_gap_analysis", {})
        strongest = data.get("strongest_responses", [])
        weakest = data.get("improvement_areas", [])
        plan = data.get("action_plan", {})
        final_assess = data.get("final_assessment", {})

        md = []
        md.append("# AI INTERVIEW INTELLIGENCE & PERFORMANCE REPORT")
        md.append(f"**Generated:** {data['metadata']['generated_at'][:19].replace('T', ' ')}  ")
        md.append(f"**Session ID:** `{data['metadata']['session_id']}`  \n")
        md.append("---")

        # 1. Executive Summary
        md.append("## 1. Executive Summary")
        md.append(f"| Evaluation Metric | Assessment Details |")
        md.append(f"| :--- | :--- |")
        md.append(f"| **Candidate Name** | **{data['candidate']['name']}** |")
        md.append(f"| **Target Role** | **{data['job']['role']}** ({data['job']['company']}) |")
        md.append(f"| **Overall Score** | **{data['interview_summary']['overall_score']} / 100** |")
        md.append(f"| **Assessment Tier** | **{data['interview_summary']['performance_tier']}** |")
        md.append(f"| **Hiring Verdict** | **{exec_sum.get('verdict', 'Evaluated')}** |")
        md.append(f"| **Questions Evaluated** | {data['interview_summary']['total_questions']} questions |")
        md.append(f"| **Peak Difficulty Reached** | Level {data['interview_summary']['max_difficulty_reached']} of 5 |")
        md.append("")
        if exec_sum.get("summary_text"):
            md.append(f"> **Executive Takeaway:** {exec_sum['summary_text']}\n")

        # 2. Competency Analysis with Evidence Quotes
        md.append("## 2. Core Competency Dimensions & Evidence Quotes")
        md.append("| Competency Dimension | Score | Level | Verbatim Evidence Quote | Analytical Rationale |")
        md.append("| :--- | :---: | :---: | :--- | :--- |")
        for c in comp_anal:
            quote = c.get("evidence_quote", "N/A").replace("\n", " ")
            rationale = c.get("analysis", "N/A").replace("\n", " ")
            md.append(f"| **{c.get('name')}** | {c.get('score')}% | **{c.get('level')}** | {quote} | {rationale} |")
        md.append("")

        # 3. Interview Journey Timeline
        md.append("## 3. Interview Journey Timeline")
        md.append("| # | Domain | Question | Candidate Answer Snippet | Score | Difficulty | Outcome |")
        md.append("| :-: | :--- | :--- | :--- | :-: | :-: | :--- |")
        for j in journey:
            q_clean = j.get("question", "").replace("\n", " ")
            a_snippet = j.get("answer_snippet", "").replace("\n", " ")
            md.append(
                f"| {j.get('turn')} | **{j.get('category').upper()}** | {q_clean} | {a_snippet} | "
                f"{j.get('score')}% | L{j.get('difficulty')} | `{j.get('outcome')}` |"
            )
        md.append("")

        # 4. Difficulty Progression Rationale
        md.append("## 4. Adaptive Difficulty Progression Rationale")
        md.append(f"- **Starting Difficulty:** Level {diff_prog.get('starting_difficulty', 1)}")
        md.append(f"- **Peak Difficulty Reached:** Level {diff_prog.get('peak_difficulty', 1)}")
        md.append(f"- **Progression Summary:** {diff_prog.get('progression_summary', 'Evaluated adaptively.')}")
        md.append(f"- **Performance Under Peak Scrutiny:** {diff_prog.get('peak_performance_analysis', 'Tested.')}")
        md.append("")

        # 5. Follow-up Intelligence
        md.append("## 5. Contextual Follow-up Intelligence")
        md.append(f"- **Total Follow-ups Triggered:** {followups.get('total_followups', 0)}")
        md.append(f"- **Synthesis:** {followups.get('analysis', 'Evaluated.')}")
        if followups.get("followup_items"):
            md.append("")
            md.append("| Follow-up Question | Candidate Response | Depth Rating | Depth Validated? | Takeaway |")
            md.append("| :--- | :--- | :---: | :---: | :--- |")
            for fi in followups["followup_items"]:
                ans_clip = fi.get("answer", "")[:90].replace("\n", " ") + "..."
                validated = "YES" if fi.get("validated_depth") else "NEEDS REINFORCEMENT"
                md.append(f"| {fi.get('question')} | {ans_clip} | `{fi.get('depth_level')}` | **{validated}** | {fi.get('takeaway')} |")
        md.append("")

        # 6. Skill Gap Analysis (Partitioned)
        md.append("## 6. Candidate-Job Alignment & Skill Gap Analysis")
        req = skill_gaps.get("required_skills", {})
        pref = skill_gaps.get("preferred_skills", {})
        md.append(f"**Required Skill Readiness Score:** {skill_gaps.get('gap_readiness_score', 0.0)}%\n")
        md.append("### Required Skills (Critical)")
        if req.get("matched"):
            for m in req["matched"]:
                status = m.get("status", "Matched")
                md.append(f"- :white_check_mark: **{m.get('skill')}**: {status}")
        if req.get("missing"):
            for m in req["missing"]:
                assessed = "Assessed in interview" if m.get("assessed") else "Not directly probed"
                md.append(f"- :x: **{m.get('skill')}** [{m.get('risk_level')} - {assessed}]: {m.get('remediation')}")
        md.append("")
        md.append("### Preferred Skills (Desirable)")
        if pref.get("matched"):
            for p in pref["matched"]:
                md.append(f"- :white_check_mark: **{p}**: Verified profile asset")
        if pref.get("missing"):
            for p in pref["missing"]:
                md.append(f"- :warning: **{p.get('skill')}**: {p.get('remediation')}")
        md.append("")

        # 7. Strongest Responses Spotlight
        md.append("## 7. Strongest Candidate Responses Spotlight")
        for idx, s in enumerate(strongest, start=1):
            md.append(f"### Spotlight #{idx}: Question {s.get('question_number')} [{s.get('category').upper()}] - Score: {s.get('score')}%")
            md.append(f"**Question Asked:** *\"{s.get('question')}\"*  ")
            md.append(f"**Candidate Verbatim Response:**  \n> \"{s.get('answer')}\"  ")
            md.append(f"**Why This Response Was Exemplary:** {s.get('why_strong')}  \n")

        # 8. Areas Requiring Improvement Spotlight
        md.append("## 8. Critical Areas for Improvement Spotlight")
        for idx, w in enumerate(weakest, start=1):
            md.append(f"### Growth Area #{idx}: Question {w.get('question_number')} [{w.get('category').upper()}] - Score: {w.get('score')}%")
            md.append(f"**Question Asked:** *\"{w.get('question')}\"*  ")
            md.append(f"**Candidate Response:** \"{w.get('answer')}\"  ")
            md.append(f"**Identified Deficiency:** {w.get('deficiency')}  ")
            md.append(f"**Model Response Guidance:** {w.get('model_guidance')}  \n")

        # 9. Action Plan
        md.append("## 9. Personalized 30-60-90 Day Action Plan")
        md.append("### Days 1-30: Immediate Foundational Remediation")
        for task in plan.get("days_1_30", []):
            md.append(f"1. {task}")
        md.append("")
        md.append("### Days 31-60: Architectural Depth & Production Scenarios")
        for task in plan.get("days_31_60", []):
            md.append(f"1. {task}")
        md.append("")
        md.append("### Days 61-90: Mock Interview Mastery & Advanced Scenarios")
        for task in plan.get("days_61_90", []):
            md.append(f"1. {task}")
        md.append("")

        # 10. Final Candidate Assessment
        md.append("## 10. Final Candidate Assessment & Hiring Recommendation")
        md.append(f"- **Final Hiring Verdict:** **{final_assess.get('hiring_verdict', 'Pending Review')}**")
        md.append(f"- **Role Alignment:** {final_assess.get('ideal_role_fit', data['job']['role'])}")
        md.append(f"- **Growth Trajectory:** {final_assess.get('growth_trajectory', 'Normal')}")
        md.append("- **Key Strategic Strengths:**")
        for s in final_assess.get("strengths_summary", []):
            md.append(f"  - :white_check_mark: {s}")
        md.append("- **Key Risk Factors & Diligence Points:**")
        for r in final_assess.get("risk_factors", []):
            md.append(f"  - :warning: {r}")
        md.append("")

        md.append("---")
        md.append("*AI Powered Interview Intelligence System • Comprehensive Evaluation Audit*")
        return "\n".join(md)

    # =============================================================
    # HTML REPORT
    # =============================================================

    def generate_html(
        self,
        report_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a responsive, beautifully styled HTML dashboard report.
        """
        data = report_data or self.build_report()

        exec_sum = data.get("executive_summary", {})
        comp_anal = data.get("competency_analysis", [])
        journey = data.get("interview_journey", [])
        diff_prog = data.get("difficulty_progression", {})
        followups = data.get("followup_intelligence", {})
        skill_gaps = data.get("skill_gap_analysis", {})
        strongest = data.get("strongest_responses", [])
        weakest = data.get("improvement_areas", [])
        plan = data.get("action_plan", {})
        final_assess = data.get("final_assessment", {})

        score = data["interview_summary"]["overall_score"]
        tier = data["interview_summary"]["performance_tier"]
        verdict = exec_sum.get("verdict", tier)

        # Competency cards
        comp_cards = ""
        for c in comp_anal:
            val = c.get("score", 50)
            level = c.get("level", "Moderate")
            quote = c.get("evidence_quote", "")
            anal = c.get("analysis", "")
            comp_cards += f"""
            <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:18px; margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <span style="font-weight:700; color:#1e293b; font-size:15px;">{c.get('name')}</span>
                    <span style="background:#eff6ff; color:#2563eb; font-weight:700; font-size:13px; padding:3px 10px; border-radius:999px;">{val}% ({level})</span>
                </div>
                <div style="background:#f1f5f9; border-radius:999px; height:8px; overflow:hidden; margin-bottom:10px;">
                    <div style="background:linear-gradient(90deg, #3b82f6, #2563eb); width:{val}%; height:100%;"></div>
                </div>
                <p style="font-size:13px; color:#475569; margin:4px 0 8px 0;">{anal}</p>
                <div style="background:#f8fafc; border-left:3px solid #3b82f6; padding:8px 12px; font-size:12px; color:#334155; font-style:italic; border-radius:4px;">
                    <strong>Evidence Quote:</strong> {quote}
                </div>
            </div>
            """

        # Timeline rows
        timeline_rows = ""
        for j in journey:
            outcome_bg = "#eff6ff" if "Follow-up" in j.get("outcome", "") else "#f0fdf4" if "Level" in j.get("outcome", "") else "#fef2f2" if "Skipped" in j.get("outcome", "") else "#f8fafc"
            timeline_rows += f"""
            <tr>
                <td style="font-weight:700; text-align:center;">{j.get('turn')}</td>
                <td><span style="background:#f1f5f9; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600;">{j.get('category').upper()}</span></td>
                <td style="font-size:13px; max-width:240px;">{j.get('question')}</td>
                <td style="font-size:12px; color:#475569; max-width:260px;">{j.get('answer_snippet')}</td>
                <td style="text-align:center; font-weight:700; color:#2563eb;">{j.get('score')}%</td>
                <td style="text-align:center;"><span style="background:#fef3c7; color:#92400e; padding:2px 6px; border-radius:4px; font-size:11px;">L{j.get('difficulty')}</span></td>
                <td><span style="background:{outcome_bg}; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600;">{j.get('outcome')}</span></td>
            </tr>
            """

        # Strongest spotlights
        strongest_html = ""
        for s in strongest:
            strongest_html += f"""
            <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; padding:16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="font-weight:700; color:#166534; font-size:14px;">Question {s.get('question_number')} ({s.get('category').upper()})</span>
                    <span style="font-weight:800; color:#16a34a; font-size:14px;">Score: {s.get('score')}%</span>
                </div>
                <p style="font-size:13px; color:#1e293b; margin:4px 0;"><strong>Q:</strong> <em>"{s.get('question')}"</em></p>
                <div style="background:#ffffff; border-left:3px solid #16a34a; padding:8px 12px; border-radius:4px; font-size:12px; color:#334155; margin:6px 0;">
                    "{s.get('answer')}"
                </div>
                <p style="font-size:12px; color:#166534; margin:4px 0 0 0;"><strong>Commendation:</strong> {s.get('why_strong')}</p>
            </div>
            """

        # Weakest spotlights
        weakest_html = ""
        for w in weakest:
            weakest_html += f"""
            <div style="background:#fffbeb; border:1px solid #fde68a; border-radius:10px; padding:16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                    <span style="font-weight:700; color:#92400e; font-size:14px;">Question {w.get('question_number')} ({w.get('category').upper()})</span>
                    <span style="font-weight:800; color:#d97706; font-size:14px;">Score: {w.get('score')}%</span>
                </div>
                <p style="font-size:13px; color:#1e293b; margin:4px 0;"><strong>Q:</strong> <em>"{w.get('question')}"</em></p>
                <div style="background:#ffffff; border-left:3px solid #d97706; padding:8px 12px; border-radius:4px; font-size:12px; color:#334155; margin:6px 0;">
                    "{w.get('answer')}"
                </div>
                <p style="font-size:12px; color:#b45309; margin:4px 0;"><strong>Identified Deficiency:</strong> {w.get('deficiency')}</p>
                <p style="font-size:12px; color:#15803d; margin:4px 0 0 0;"><strong>Exemplary Guidance:</strong> {w.get('model_guidance')}</p>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interview Intelligence Report - {data['candidate']['name']}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif; background: #0f172a; color: #1e293b; margin: 0; padding: 24px; line-height: 1.5; }}
        .container {{ max-width: 1040px; margin: 0 auto; background: #ffffff; border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.25); padding: 40px; }}
        .header {{ border-bottom: 2px solid #f1f5f9; padding-bottom: 24px; margin-bottom: 28px; display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 16px; }}
        .badge {{ background: #eff6ff; color: #1d4ed8; padding: 6px 14px; border-radius: 999px; font-weight: 700; font-size: 13px; letter-spacing: 0.5px; text-transform: uppercase; }}
        .score-box {{ text-align: right; }}
        .score-number {{ font-size: 52px; font-weight: 900; color: #2563eb; line-height: 1; }}
        .verdict-banner {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; border-radius: 12px; padding: 20px 24px; margin-bottom: 28px; }}
        .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px; margin-bottom: 24px; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
        .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; color: #475569; font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }}
        .section-title {{ font-size: 18px; font-weight: 800; color: #0f172a; margin: 28px 0 14px 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; display: flex; align-items: center; justify-content: space-between; }}
        @media (max-width: 768px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <span class="badge">Comprehensive Interview Intelligence Report</span>
            <h1 style="margin: 10px 0 4px 0; font-size: 30px; font-weight: 800; color: #0f172a;">{data['candidate']['name']}</h1>
            <p style="margin: 0; color: #64748b; font-size: 15px;">Target Role: <strong style="color: #1e293b;">{data['job']['role']}</strong> • {data['job']['company']}</p>
        </div>
        <div class="score-box">
            <div class="score-number">{score}%</div>
            <div style="font-weight: 700; color: #2563eb; font-size: 14px; text-transform: uppercase; margin-top: 4px;">{tier}</div>
        </div>
    </div>

    <!-- 1. Executive Summary -->
    <div class="verdict-banner">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <span style="color: #94a3b8; font-size: 13px; font-weight: 600; text-transform: uppercase;">Executive Hiring Verdict</span>
            <span style="background: #3b82f6; color: #ffffff; font-weight: 700; font-size: 12px; padding: 4px 12px; border-radius: 999px;">{verdict}</span>
        </div>
        <p style="margin: 0; font-size: 15px; line-height: 1.6; color: #e2e8f0;">
            {exec_sum.get('summary_text', 'Candidate completed the interview evaluation.')}
        </p>
        <div style="display: flex; gap: 24px; margin-top: 14px; padding-top: 12px; border-top: 1px solid #334155; font-size: 13px; color: #cbd5e1;">
            <span>Questions: <strong>{data['interview_summary']['total_questions']}</strong></span>
            <span>Peak Difficulty: <strong>Level {diff_prog.get('peak_difficulty', 1)}/5</strong></span>
            <span>Required Match: <strong>{data['candidate_job_match']['match_percentage']}%</strong></span>
        </div>
    </div>

    <!-- 2. Core Competencies -->
    <div class="section-title">
        <span>2. Core Competency Analysis & Evidence Quotes</span>
    </div>
    {comp_cards}

    <!-- 3. Journey Timeline -->
    <div class="section-title">
        <span>3. Interview Journey Timeline</span>
    </div>
    <div style="overflow-x: auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
        <table>
            <thead>
                <tr>
                    <th style="width: 30px;">#</th>
                    <th>Domain</th>
                    <th>Question</th>
                    <th>Candidate Answer Excerpt</th>
                    <th>Score</th>
                    <th>Diff</th>
                    <th>Outcome</th>
                </tr>
            </thead>
            <tbody>
                {timeline_rows}
            </tbody>
        </table>
    </div>

    <!-- 4 & 5. Difficulty Progression & Follow-up Intelligence -->
    <div class="grid-2" style="margin-top: 24px;">
        <div class="card">
            <h3 style="margin-top: 0; font-size: 16px; color: #0f172a;">4. Difficulty Progression Rationale</h3>
            <p style="font-size: 13px; color: #475569;">{diff_prog.get('progression_summary', 'Evaluated adaptively.')}</p>
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin: 10px 0; font-size: 13px;">
                <strong>Peak Scrutiny Analysis:</strong>
                <p style="margin: 4px 0 0 0; color: #334155;">{diff_prog.get('peak_performance_analysis', 'Standard performance.')}</p>
            </div>
        </div>
        <div class="card">
            <h3 style="margin-top: 0; font-size: 16px; color: #0f172a;">5. Follow-up Intelligence</h3>
            <p style="font-size: 13px; color: #475569;">{followups.get('analysis', 'Evaluated.')}</p>
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin: 10px 0; font-size: 13px;">
                <p style="margin: 0; color: #334155;">Total Contextual Probes: <strong>{followups.get('total_followups', 0)}</strong></p>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 12px;">Probes test conceptual depth when answers contain ambitious architectural or technology claims.</p>
            </div>
        </div>
    </div>

    <!-- 6. Skill Gap Analysis -->
    <div class="section-title">
        <span>6. Partitioned Skill Gap Analysis (Required vs Preferred)</span>
    </div>
    <div class="grid-2">
        <div class="card" style="border-left: 4px solid #ef4444;">
            <h3 style="margin-top: 0; font-size: 15px; color: #b91c1c;">Required Skills (Critical)</h3>
            <p style="font-size: 13px; margin: 4px 0;"><strong>Verified Matched:</strong> {', '.join([m['skill'] for m in skill_gaps.get('required_skills', {}).get('matched', [])]) or 'None'}</p>
            <p style="font-size: 13px; margin: 4px 0; color: #b91c1c;"><strong>Identified Gaps:</strong> {', '.join([m['skill'] for m in skill_gaps.get('required_skills', {}).get('missing', [])]) or 'None'}</p>
        </div>
        <div class="card" style="border-left: 4px solid #f59e0b;">
            <h3 style="margin-top: 0; font-size: 15px; color: #b45309;">Preferred Skills (Desirable)</h3>
            <p style="font-size: 13px; margin: 4px 0;"><strong>Profile Matched:</strong> {', '.join(skill_gaps.get('preferred_skills', {}).get('matched', [])) or 'None'}</p>
            <p style="font-size: 13px; margin: 4px 0; color: #b45309;"><strong>Desirable Additions:</strong> {', '.join([m['skill'] for m in skill_gaps.get('preferred_skills', {}).get('missing', [])]) or 'None'}</p>
        </div>
    </div>

    <!-- 7 & 8. Strongest vs Areas Requiring Improvement -->
    <div class="section-title">
        <span>7 & 8. Performance Spotlights: Best Responses vs Critical Gaps</span>
    </div>
    <div class="grid-2">
        <div>
            <h4 style="color: #166534; font-size: 15px; margin: 0 0 10px 0;">Top Strongest Responses</h4>
            {strongest_html}
        </div>
        <div>
            <h4 style="color: #b45309; font-size: 15px; margin: 0 0 10px 0;">Areas Requiring Improvement</h4>
            {weakest_html}
        </div>
    </div>

    <!-- 9. Personalized 30-60-90 Day Action Plan -->
    <div class="section-title">
        <span>9. Personalized 30-60-90 Day Action Plan</span>
    </div>
    <div class="grid-3">
        <div class="card" style="border-top: 4px solid #3b82f6;">
            <h4 style="margin-top: 0; color: #1d4ed8; font-size: 15px;">Days 1-30: Foundation</h4>
            <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #334155;">
                {''.join(f"<li style='margin-bottom: 8px;'>{t}</li>" for t in plan.get('days_1_30', []))}
            </ul>
        </div>
        <div class="card" style="border-top: 4px solid #8b5cf6;">
            <h4 style="margin-top: 0; color: #6d28d9; font-size: 15px;">Days 31-60: Production</h4>
            <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #334155;">
                {''.join(f"<li style='margin-bottom: 8px;'>{t}</li>" for t in plan.get('days_31_60', []))}
            </ul>
        </div>
        <div class="card" style="border-top: 4px solid #10b981;">
            <h4 style="margin-top: 0; color: #047857; font-size: 15px;">Days 61-90: Mastery</h4>
            <ul style="margin: 0; padding-left: 18px; font-size: 13px; color: #334155;">
                {''.join(f"<li style='margin-bottom: 8px;'>{t}</li>" for t in plan.get('days_61_90', []))}
            </ul>
        </div>
    </div>

    <!-- 10. Final Hiring Assessment -->
    <div class="section-title">
        <span>10. Final Candidate Assessment & Hiring Recommendation</span>
    </div>
    <div class="card" style="background: #f8fafc; border: 2px solid #e2e8f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="font-size: 16px; font-weight: 800; color: #0f172a;">Recommendation Verdict:</span>
            <span style="background: #1e293b; color: #ffffff; font-weight: 800; font-size: 14px; padding: 6px 16px; border-radius: 999px;">{final_assess.get('hiring_verdict', 'Hire')}</span>
        </div>
        <p style="font-size: 14px; color: #334155; line-height: 1.6; margin: 8px 0;">
            <strong>Growth Trajectory:</strong> {final_assess.get('growth_trajectory', 'Strong capability.')}
        </p>
        <div style="display: flex; gap: 20px; font-size: 13px; margin-top: 10px; color: #475569;">
            <span>Target Role Fit: <strong>{final_assess.get('ideal_role_fit', data['job']['role'])}</strong></span>
        </div>
    </div>

    <div style="margin-top: 36px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 20px;">
        AI Powered Interview Intelligence System • Generated automatically • Session ID: {data['metadata']['session_id']}
    </div>
</div>
</body>
</html>"""
        return html

    # =============================================================
    # SAVE REPORT FILES
    # =============================================================

    def save_report(
        self,
        output_dir: Union[str, Path],
        base_filename: str = "interview_intelligence_report",
    ) -> Dict[str, Path]:
        """
        Save Markdown and HTML reports to the specified directory.
        """
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        report_data = self.build_report()
        md_content = self.generate_markdown(report_data)
        html_content = self.generate_html(report_data)

        md_file = out_path / f"{base_filename}.md"
        html_file = out_path / f"{base_filename}.html"

        md_file.write_text(md_content, encoding="utf-8")
        html_file.write_text(html_content, encoding="utf-8")

        return {
            "markdown": md_file,
            "html": html_file,
        }
