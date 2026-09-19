from typing import Any, Dict, List, Optional, Union
import statistics

from mock_interview.interview.answer_analyzer import analyze_answer


class InterviewEvaluator:
    """
    Evaluates completed mock interview sessions.

    Consumes:
    - ConversationState (or state dict)
    - CandidateProfile
    - JobProfile
    - MatchReport

    Produces:
    - Core competency scores (Technical, Communication, Relevance, Completeness, Problem Solving, Overall)
    - Category-by-category breakdown
    - Strengths and weaknesses
    - Skill gap performance analysis
    - Concrete preparation recommendations
    - Question-by-question evidence breakdown
    """

    def __init__(
        self,
        candidate_profile: Any = None,
        job_profile: Any = None,
        match_report: Optional[Dict[str, Any]] = None,
    ):
        self.candidate_profile = candidate_profile
        self.job_profile = job_profile
        self.match_report = match_report or {}

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

    @staticmethod
    def _level_to_score(level: str) -> float:
        mapping = {
            "excellent": 95.0,
            "very_high": 95.0,
            "high": 85.0,
            "strong": 85.0,
            "good": 75.0,
            "medium": 65.0,
            "moderate": 65.0,
            "acceptable": 65.0,
            "low": 45.0,
            "minimal": 40.0,
            "very_short": 35.0,
            "short": 55.0,
            "needs_improvement": 40.0,
            "weak": 35.0,
            "very_low": 20.0,
            "none": 15.0,
            "empty": 0.0,
        }
        return mapping.get(str(level).strip().lower(), 50.0)

    # =============================================================
    # MAIN EVALUATION METHOD
    # =============================================================

    def evaluate(
        self,
        state: Union[Any, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Evaluate a completed interview session.
        Accepts either ConversationState or serialized state dict.
        """
        state_dict = self._to_dict(state)

        candidate_name = state_dict.get(
            "candidate_name",
            self._to_dict(self.candidate_profile).get("name", "Candidate"),
        )
        role = state_dict.get(
            "role",
            self._to_dict(self.job_profile).get("role_title", "Interview Candidate"),
        )
        session_id = state_dict.get("session_id", "session")
        completed_categories = state_dict.get("completed_categories", [])
        max_difficulty_reached = state_dict.get("current_difficulty", 1)
        conversation_history = state_dict.get("conversation_history", [])

        # ---------------------------------------------------------
        # Process every turn in conversation history
        # ---------------------------------------------------------
        evaluated_turns: List[Dict[str, Any]] = []
        category_scores: Dict[str, List[float]] = {}
        all_topics_mentioned: set = set()

        for idx, turn in enumerate(conversation_history, start=1):
            question = turn.get("question", "")
            answer = turn.get("answer", "")
            category = turn.get("category", "general")
            active_category = turn.get("active_category", category)
            difficulty = turn.get("difficulty", 1)

            # Retrieve existing assessment or analyze on the fly
            assessment = turn.get("assessment")
            if not assessment or not isinstance(assessment, dict):
                assessment = analyze_answer(
                    question=question,
                    answer=answer,
                )

            score = float(assessment.get("score", 50.0))
            quality = assessment.get("quality", "moderate")
            tech_depth = assessment.get("technical_depth_level", "low")
            clarity = assessment.get("clarity_level", "good")
            relevance = assessment.get("relevance", {}).get("level", "medium")
            completeness = assessment.get("completeness_level", "medium")
            vagueness = assessment.get("vagueness_level", "low")

            answer_topics = assessment.get("answer_topics", {})
            turn_topics = answer_topics.get("topics", [])
            for t in turn_topics:
                all_topics_mentioned.add(t)

            is_skipped = (
                turn.get("skipped", False)
                or answer.strip() == "[Skipped]"
                or answer.strip().lower() in (":skip", "skip")
            )

            evaluated_turns.append(
                {
                    "question_number": idx,
                    "question": question,
                    "answer": answer,
                    "category": category,
                    "active_category": active_category,
                    "difficulty": difficulty,
                    "score": round(score, 2),
                    "quality": "skipped" if is_skipped else quality,
                    "technical_depth": "skipped" if is_skipped else tech_depth,
                    "clarity": "skipped" if is_skipped else clarity,
                    "relevance": relevance,
                    "completeness": completeness,
                    "vagueness": vagueness,
                    "topics": turn_topics,
                    "needs_followup": assessment.get("needs_followup", False),
                    "skipped": is_skipped,
                    "decision": turn.get("decision", {}),
                }
            )

            # Group scores under active interview category
            target_cat = active_category if active_category != "follow_up" else category
            category_scores.setdefault(target_cat, []).append(score)

        total_questions = len(evaluated_turns)

        # ---------------------------------------------------------
        # Compute Category Averages
        # ---------------------------------------------------------
        category_evaluations: Dict[str, Dict[str, Any]] = {}
        for cat, scores in category_scores.items():
            avg_score = statistics.mean(scores) if scores else 0.0
            category_evaluations[cat] = {
                "question_count": len(scores),
                "average_score": round(avg_score, 1),
                "performance": (
                    "Strong" if avg_score >= 75
                    else "Moderate" if avg_score >= 55
                    else "Needs Improvement"
                ),
            }

        # ---------------------------------------------------------
        # Core Competency Dimension Scoring (0 - 100)
        # ---------------------------------------------------------

        # 1. Technical Knowledge
        tech_scores = []
        for turn in evaluated_turns:
            if turn["active_category"] in ("technical", "project", "role_specific", "skill_gap") and not turn.get("skipped"):
                tech_scores.append(turn["score"])
        if not tech_scores:
            tech_scores = [t["score"] for t in evaluated_turns if not t.get("skipped")] or [50.0]

        tech_depth_bonus = 0.0
        high_depth_count = sum(1 for t in evaluated_turns if t["technical_depth"] in ("high", "medium"))
        if high_depth_count > 0:
            tech_depth_bonus = min(10.0, (high_depth_count / max(1, total_questions)) * 15.0)

        # Higher difficulty bonus (if candidate handled difficulty >= 3)
        diff_bonus = min(5.0, (max_difficulty_reached - 1) * 1.5)
        technical_knowledge = min(100.0, statistics.mean(tech_scores) + tech_depth_bonus + diff_bonus)

        # 2. System Architecture & Project Execution
        arch_scores = [
            t["score"] for t in evaluated_turns
            if t["active_category"] in ("project", "role_specific") and not t.get("skipped")
        ]
        system_architecture = statistics.mean(arch_scores) if arch_scores else technical_knowledge * 0.95

        # 3. Problem Solving & Critical Thinking
        ps_scores = []
        for turn in evaluated_turns:
            if turn["active_category"] in ("situational", "behavioral", "project") and not turn.get("skipped"):
                ps_scores.append(turn["score"])
        if not ps_scores:
            ps_scores = [t["score"] for t in evaluated_turns if not t.get("skipped")] or [60.0]
        problem_solving = statistics.mean(ps_scores)

        # 4. Communication & Articulation
        comm_scores = []
        for turn in evaluated_turns:
            if turn.get("skipped"):
                continue
            clarity_val = self._level_to_score(turn["clarity"])
            vagueness_val = 100.0 - self._level_to_score(turn["vagueness"])
            comm_scores.append((clarity_val * 0.6) + (vagueness_val * 0.4))
        communication = statistics.mean(comm_scores) if comm_scores else 65.0

        # 5. Relevance & Completeness
        rel_scores = [self._level_to_score(t["relevance"]) for t in evaluated_turns if not t.get("skipped")] or [70.0]
        relevance = statistics.mean(rel_scores)
        comp_scores = [self._level_to_score(t["completeness"]) for t in evaluated_turns if not t.get("skipped")] or [60.0]
        completeness = statistics.mean(comp_scores)

        # 6. Behavioral & Situational Judgment
        behav_scores = [
            t["score"] for t in evaluated_turns
            if t["active_category"] in ("behavioral", "situational") and not t.get("skipped")
        ]
        behavioral_judgment = statistics.mean(behav_scores) if behav_scores else 70.0

        # Overall Score
        overall_score = (
            (technical_knowledge * 0.30)
            + (system_architecture * 0.15)
            + (problem_solving * 0.20)
            + (completeness * 0.10)
            + (relevance * 0.10)
            + (communication * 0.15)
        )
        overall_score = round(max(0.0, min(100.0, overall_score)), 1)

        # Performance Tier
        if overall_score >= 80.0:
            performance_tier = "Advanced / Recommended"
        elif overall_score >= 65.0:
            performance_tier = "Proficient / Solid Candidate"
        elif overall_score >= 50.0:
            performance_tier = "Developing / Promising"
        else:
            performance_tier = "Needs Substantial Preparation"

        # ---------------------------------------------------------
        # Identify Strengths
        # ---------------------------------------------------------
        strengths: List[str] = []
        for cat, data in category_evaluations.items():
            if data["average_score"] >= 70.0:
                strengths.append(f"Demonstrated solid competence in {cat.replace('_', ' ')} (Score: {data['average_score']}%)")

        if communication >= 75.0:
            strengths.append("Clear communication with minimal filler phrases and good structural clarity")
        if technical_knowledge >= 75.0:
            strengths.append("Strong technical explanations with meaningful depth and concept application")
        if max_difficulty_reached >= 3:
            strengths.append(f"Successfully reached and handled elevated difficulty level {max_difficulty_reached}")

        matched_skills = self.match_report.get("required_skills", {}).get("matched", [])
        if matched_skills:
            strengths.append(f"Verified job-matched skills: {', '.join(matched_skills)}")

        if not strengths:
            strengths.append("Demonstrated willingness to engage adaptively with all interview questions")

        # ---------------------------------------------------------
        # Identify Weaknesses & Improvement Areas
        # ---------------------------------------------------------
        weaknesses: List[str] = []
        for cat, data in category_evaluations.items():
            if data["average_score"] < 60.0:
                weaknesses.append(f"Lower score in {cat.replace('_', ' ')} questions ({data['average_score']}%)")

        vague_count = sum(1 for t in evaluated_turns if t["vagueness"] in ("high", "medium") and not t.get("skipped"))
        if vague_count >= 2:
            weaknesses.append(f"Provided vague or general explanations in {vague_count} responses")

        low_depth_count = sum(1 for t in evaluated_turns if t["technical_depth"] in ("minimal", "low") and not t.get("skipped"))
        if low_depth_count >= 2:
            weaknesses.append("Several technical answers lacked concrete implementation details or metric evidence")

        skipped_count = sum(1 for t in evaluated_turns if t.get("skipped"))
        if skipped_count > 0:
            weaknesses.append(f"Skipped {skipped_count} question(s) without providing reasoning or partial solution structure")

        # ---------------------------------------------------------
        # Skill Gap Analysis
        # ---------------------------------------------------------
        missing_required = self.match_report.get("required_skills", {}).get("missing", [])
        missing_preferred = self.match_report.get("preferred_skills", {}).get("missing", [])

        skill_gap_eval = category_evaluations.get("skill_gap")
        gap_performance_note = ""
        if skill_gap_eval:
            gap_performance_note = f"Candidate scored {skill_gap_eval['average_score']}% when questioned on identified gap areas."

        skill_gap_summary = {
            "missing_required_skills": missing_required,
            "missing_preferred_skills": missing_preferred,
            "gap_interview_performance": gap_performance_note,
            "status": (
                "Critical Gaps Present" if missing_required
                else "Preferred Skill Gaps" if missing_preferred
                else "Fully Matched"
            ),
        }

        # ---------------------------------------------------------
        # Concrete Recommendations
        # ---------------------------------------------------------
        recommendations: List[str] = []
        if missing_required:
            recommendations.append(
                f"Build hands-on production experience with missing required skills: {', '.join(missing_required)}."
            )
        if missing_preferred:
            recommendations.append(
                f"Familiarize with role-preferred technologies such as: {', '.join(missing_preferred)}."
            )
        if low_depth_count >= 2:
            recommendations.append(
                "When discussing projects, include specific metrics (e.g. latency, accuracy, scale) and architectural tradeoffs."
            )
        if completeness < 70.0:
            recommendations.append(
                "Use the STAR method (Situation, Task, Action, Result) for behavioral and situational questions."
            )
        if not recommendations:
            recommendations.append("Continue building end-to-end projects and maintaining deep architectural awareness.")

        # =========================================================
        # 10 EVIDENCE-BASED INTELLIGENCE SECTIONS
        # =========================================================

        # Helper: Extract best verbatim quote for given categories
        def _get_evidence_quote(categories: List[str]) -> str:
            candidates = [
                t for t in evaluated_turns
                if t["active_category"] in categories and len(t.get("answer", "")) >= 20 and not t.get("skipped")
            ]
            if not candidates:
                # Fallback to any valid turn
                candidates = [t for t in evaluated_turns if len(t.get("answer", "")) >= 20 and not t.get("skipped")]
            if not candidates:
                return "Candidate provided concise or general responses in this domain."
            best = max(candidates, key=lambda x: x["score"])
            ans = best["answer"].strip()
            return f'"{ans[:160]}..."' if len(ans) > 160 else f'"{ans}"'

        # SECTION 1: EXECUTIVE SUMMARY
        verdict_title = (
            "Strong Candidate - Highly Recommended" if overall_score >= 80.0
            else "Solid Candidate - Recommended with Focused Development" if overall_score >= 65.0
            else "Developing Candidate - Foundational Gaps Present" if overall_score >= 50.0
            else "Needs Substantial Preparation Before Re-interview"
        )

        executive_summary = {
            "candidate_name": candidate_name,
            "role": role,
            "overall_score": overall_score,
            "performance_tier": performance_tier,
            "verdict": verdict_title,
            "total_questions": total_questions,
            "max_difficulty_reached": max_difficulty_reached,
            "completed_domains": len(completed_categories),
            "summary_text": (
                f"{candidate_name} completed a comprehensive {total_questions}-question adaptive technical interview for the {role} role, "
                f"achieving an overall interview score of {overall_score:.1f}/100 and reaching Difficulty Level {max_difficulty_reached}. "
                f"The candidate demonstrated strong capability in {', '.join(strengths[:2]) if strengths else 'core technical domains'}, "
                f"while showing opportunities for growth in {', '.join(weaknesses[:2]) if weaknesses else 'production-level system validation'}. "
                f"Overall assessment indicates {candidate_name} is {verdict_title.lower()}."
            ),
        }

        # SECTION 2: COMPETENCY ANALYSIS WITH EVIDENCE QUOTES
        def _competency_level(score: float) -> str:
            if score >= 80: return "Strong"
            if score >= 65: return "Proficient"
            if score >= 50: return "Developing"
            return "Needs Improvement"

        competency_analysis = [
            {
                "name": "Technical Knowledge",
                "score": round(technical_knowledge, 1),
                "level": _competency_level(technical_knowledge),
                "evidence_quote": _get_evidence_quote(["technical", "skill_gap"]),
                "analysis": (
                    f"Candidate scored {technical_knowledge:.1f}%. Demonstrated consistent grasp of core tools and libraries, "
                    f"handling technical queries with {'high' if technical_knowledge >= 75 else 'moderate'} concept retention."
                ),
            },
            {
                "name": "System Architecture & Project Execution",
                "score": round(system_architecture, 1),
                "level": _competency_level(system_architecture),
                "evidence_quote": _get_evidence_quote(["project", "role_specific"]),
                "analysis": (
                    f"Candidate scored {system_architecture:.1f}%. Articulated project architectures and deployment pipelines "
                    f"with {'clear structural separation and service awareness' if system_architecture >= 70 else 'standard high-level explanations'}."
                ),
            },
            {
                "name": "Problem Solving & Critical Thinking",
                "score": round(problem_solving, 1),
                "level": _competency_level(problem_solving),
                "evidence_quote": _get_evidence_quote(["situational", "project"]),
                "analysis": (
                    f"Candidate scored {problem_solving:.1f}%. Approached debugging and scaling scenarios with "
                    f"{'structured root-cause isolation' if problem_solving >= 70 else 'general troubleshooting steps'}."
                ),
            },
            {
                "name": "Communication & Articulation",
                "score": round(communication, 1),
                "level": _competency_level(communication),
                "evidence_quote": _get_evidence_quote(["introduction", "closing", "behavioral"]),
                "analysis": (
                    f"Candidate scored {communication:.1f}%. Maintained {'high clarity with structured points' if communication >= 75 else 'acceptable clarity with occasional ambiguity'}."
                ),
            },
            {
                "name": "Behavioral & Situational Judgment",
                "score": round(behavioral_judgment, 1),
                "level": _competency_level(behavioral_judgment),
                "evidence_quote": _get_evidence_quote(["behavioral", "situational"]),
                "analysis": (
                    f"Candidate scored {behavioral_judgment:.1f}%. Displayed {'collaborative and analytical mindset' if behavioral_judgment >= 70 else 'baseline workplace judgment'}."
                ),
            },
        ]

        # SECTION 3: INTERVIEW JOURNEY TIMELINE
        interview_journey = []
        for t in evaluated_turns:
            dec = t.get("decision", {})
            act = dec.get("action", "next")
            if t.get("skipped"):
                outcome = "Question Skipped"
            elif act in ("follow_up", "clarify"):
                outcome = "Contextual Follow-up Probed"
            elif act == "increase_difficulty":
                outcome = f"Promoted to Level {t['difficulty']}"
            elif dec.get("complete_category"):
                outcome = "Domain Completed -> Advanced"
            else:
                outcome = "Evaluated & Advanced"

            ans = t["answer"].strip()
            snippet = ans if len(ans) <= 120 else ans[:117] + "..."

            interview_journey.append({
                "turn": t["question_number"],
                "category": t["category"],
                "active_category": t["active_category"],
                "difficulty": t["difficulty"],
                "question": t["question"],
                "answer_snippet": snippet,
                "score": t["score"],
                "quality": t["quality"],
                "outcome": outcome,
            })

        # SECTION 4: DIFFICULTY PROGRESSION RATIONALE
        difficulty_events = []
        prev_diff = 1
        for t in evaluated_turns:
            cur_diff = t["difficulty"]
            if cur_diff != prev_diff or t["question_number"] == 1:
                difficulty_events.append({
                    "turn": t["question_number"],
                    "difficulty": cur_diff,
                    "reason": f"Adapted to Level {cur_diff} based on response quality ({t['quality'].upper()})",
                })
                prev_diff = cur_diff

        peak_turns = [t for t in evaluated_turns if t["difficulty"] == max_difficulty_reached and not t.get("skipped")]
        peak_avg_score = statistics.mean([t["score"] for t in peak_turns]) if peak_turns else 60.0

        difficulty_progression = {
            "starting_difficulty": 1,
            "peak_difficulty": max_difficulty_reached,
            "progression_summary": f"Interview initiated at Level 1 and adaptively scaled to Level {max_difficulty_reached} based on performance.",
            "progression_events": difficulty_events,
            "peak_performance_analysis": (
                f"At peak Difficulty Level {max_difficulty_reached}, the candidate scored an average of {peak_avg_score:.1f}%, demonstrating "
                f"{'solid technical resilience under scrutiny.' if peak_avg_score >= 70 else 'acceptable conceptual familiarity with room for deeper mastery.'}"
            ),
        }

        # SECTION 5: FOLLOW-UP INTELLIGENCE
        followup_turns = [t for t in evaluated_turns if t["category"] == "follow_up" or t["active_category"] == "follow_up"]
        followup_intelligence = {
            "total_followups": len(followup_turns),
            "analysis": (
                f"Interviewer probed {len(followup_turns)} contextual follow-up questions to test candidate technical depth."
                if followup_turns else "Candidate answers were comprehensive; single-probe evaluations satisfied requirements."
            ),
            "followup_items": [
                {
                    "question": ft["question"],
                    "answer": ft["answer"],
                    "depth_level": ft["technical_depth"],
                    "score": ft["score"],
                    "validated_depth": ft["score"] >= 65.0,
                    "takeaway": "Candidate successfully validated architectural depth under targeted follow-up." if ft["score"] >= 65.0 else "Follow-up revealed conceptual gaps requiring reinforcement."
                }
                for ft in followup_turns
            ],
        }

        # SECTION 6: SKILL GAP ANALYSIS (REQUIRED VS PREFERRED PARTITIONED)
        skill_gap_analysis = {
            "required_skills": {
                "matched": [
                    {
                        "skill": s,
                        "verified": any(s.lower() in t["question"].lower() or s.lower() in t["answer"].lower() for t in evaluated_turns),
                        "status": "Verified in Live Interview" if any(s.lower() in t["answer"].lower() for t in evaluated_turns) else "Matched from Profile",
                    }
                    for s in matched_skills
                ],
                "missing": [
                    {
                        "skill": s,
                        "assessed_in_interview": any(s.lower() in t["question"].lower() for t in evaluated_turns),
                        "risk_level": "High - Required Technical Skill",
                        "remediation": f"Complete hands-on projects and tutorials to gain verifiable production competency in {s}.",
                    }
                    for s in missing_required
                ],
            },
            "preferred_skills": {
                "matched": self.match_report.get("preferred_skills", {}).get("matched", []),
                "missing": [
                    {
                        "skill": s,
                        "risk_level": "Moderate - Desirable Skill",
                        "remediation": f"Build awareness of {s} architecture patterns and deployment integration.",
                    }
                    for s in missing_preferred
                ],
            },
            "gap_readiness_score": round(
                (len(matched_skills) / max(1, (len(matched_skills) + len(missing_required)))) * 100.0, 1
            ),
        }

        # SECTION 7: STRONGEST RESPONSES (TOP 2-3 SPOTLIGHT)
        valid_for_strongest = [t for t in evaluated_turns if not t.get("skipped") and len(t.get("answer", "")) >= 25]
        sorted_strongest = sorted(valid_for_strongest, key=lambda x: x["score"], reverse=True)
        strongest_responses = []
        for t in sorted_strongest[:3]:
            strongest_responses.append({
                "question_number": t["question_number"],
                "category": t["category"],
                "question": t["question"],
                "answer": t["answer"],
                "score": t["score"],
                "why_strong": (
                    f"Clear structured articulation, strong technical relevance ({t['relevance'].capitalize()}), "
                    f"and concrete coverage of key topics: {', '.join(t.get('topics', [])) or 'the core concept'}."
                ),
            })

        # SECTION 8: AREAS REQUIRING IMPROVEMENT (BOTTOM 2-3 SPOTLIGHT)
        sorted_weakest = sorted(evaluated_turns, key=lambda x: x["score"])
        improvement_areas = []
        for t in sorted_weakest[:3]:
            if t.get("skipped"):
                critique = "Candidate skipped this question. Even under uncertainty, articulating problem decomposition or baseline principles is preferred."
                guidance = "Acknowledge the boundary of your current knowledge, explain how you would research or test the solution, and state the foundational concepts."
            else:
                critique = "Response lacked quantitative metrics, concrete architectural tradeoffs, or deep implementation specifics."
                guidance = "Anchor the response with a concrete production example, outline specific tools/libraries utilized, and quantify outcomes."

            improvement_areas.append({
                "question_number": t["question_number"],
                "category": t["category"],
                "question": t["question"],
                "answer": t["answer"],
                "score": t["score"],
                "deficiency": critique,
                "model_guidance": guidance,
            })

        # SECTION 9: PERSONALIZED 30-60-90 DAY ACTION PLAN
        action_plan = {
            "days_1_30": [
                f"Address critical missing required skill gaps: {', '.join(missing_required) if missing_required else 'Deepen knowledge of async Python and high-throughput data processing'}.",
                "Formalize behavioral STAR stories (Situation, Task, Action, Result) with quantitative engineering impact.",
                "Refine project walkthroughs to focus on individual contribution and specific design trade-offs.",
            ],
            "days_31_60": [
                f"Gain practical familiarity with preferred technologies: {', '.join(missing_preferred) if missing_preferred else 'Containerized deployments and CI/CD pipelines'}.",
                "Build end-to-end prototype implementing microservice boundaries, caching, and latency telemetry.",
                "Practice whiteboarding and explaining edge-case handling under production failure conditions.",
            ],
            "days_61_90": [
                "Conduct timed mock interview drills with adaptive follow-up questions.",
                "Synthesize end-to-end system architecture designs for complex, multi-model production environments.",
                "Finalize resume and portfolio highlighting verified interview strengths.",
            ],
        }

        # SECTION 10: FINAL CANDIDATE ASSESSMENT & HIRING RECOMMENDATION
        final_assessment = {
            "hiring_verdict": (
                "Strong Hire" if overall_score >= 82.0
                else "Hire" if overall_score >= 70.0
                else "Leaning Hire / Needs Specific Verification" if overall_score >= 55.0
                else "Do Not Advance at this Time"
            ),
            "strengths_summary": strengths[:4],
            "risk_factors": weaknesses[:3] if weaknesses else ["Candidate needs deeper production scale evidence"],
            "ideal_role_fit": role,
            "growth_trajectory": (
                "Demonstrates rapid learning capacity and strong technical foundation; well-positioned for immediate engineering impact."
                if overall_score >= 65.0
                else "Has foundational capability; requires guided mentorship and hands-on production exposure."
            ),
        }

        # ---------------------------------------------------------
        # Final Structured Result
        # ---------------------------------------------------------
        return {
            "session_id": session_id,
            "candidate_name": candidate_name,
            "role": role,
            "total_questions": total_questions,
            "max_difficulty_reached": max_difficulty_reached,
            "completed_categories": completed_categories,
            "overall_score": overall_score,
            "performance_tier": performance_tier,
            "competency_scores": {
                "technical_knowledge": round(technical_knowledge, 1),
                "system_architecture": round(system_architecture, 1),
                "communication": round(communication, 1),
                "relevance": round(relevance, 1),
                "completeness": round(completeness, 1),
                "problem_solving": round(problem_solving, 1),
                "behavioral_judgment": round(behavioral_judgment, 1),
            },
            "category_evaluations": category_evaluations,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "skill_gap_summary": skill_gap_summary,
            "recommendations": recommendations,
            "topics_covered": sorted(list(all_topics_mentioned)),
            "question_breakdown": evaluated_turns,
            # 10 Evidence-Based Intelligence Sections
            "executive_summary": executive_summary,
            "competency_analysis": competency_analysis,
            "interview_journey": interview_journey,
            "difficulty_progression": difficulty_progression,
            "followup_intelligence": followup_intelligence,
            "skill_gap_analysis": skill_gap_analysis,
            "strongest_responses": strongest_responses,
            "improvement_areas": improvement_areas,
            "action_plan": action_plan,
            "final_assessment": final_assessment,
        }
