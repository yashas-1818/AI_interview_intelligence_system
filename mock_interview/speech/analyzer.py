"""
Speech Delivery Analyzer and Session Roll-up.

Coordinates transcript metrics (words, fillers, rates) and audio-timing
metrics (duration, speaking pace, pauses).

Adheres to core principles:
1. Speech-delivery metrics are kept distinct from technical answer quality.
2. Pauses are NEVER inferred from transcript text or punctuation; if audio
   timing is missing, pause metrics are explicitly marked 'unavailable'.
3. Normal variations in pacing, accent, and natural filler usage are treated
   objectively without punitive judgements or negative scores.
4. Returns fully structured, JSON-serializable dataclasses.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Union

from mock_interview.speech.metrics import (
    calculate_duration_seconds,
    calculate_filler_rate,
    calculate_speaking_pace,
    count_words,
    extract_pause_metrics,
    find_filler_words,
    validate_and_sanitize_telemetry,
)


@dataclass
class SpeechMetricValue:
    """
    Standardized container for a single speech metric value.
    Provides clear units, status, and confidence metadata.
    """
    value: Optional[Union[int, float, str]]
    unit: str
    status: str  # 'measured' | 'estimated' | 'unavailable'
    confidence: str  # 'high' | 'low' | 'none'
    details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "unit": self.unit,
            "status": self.status,
            "confidence": self.confidence,
            "details": self.details,
        }


@dataclass
class TurnSpeechAnalytics:
    """
    Speech delivery metrics for a single interview question / turn.
    Maintains clean separation between transcript and audio-timing metrics.
    """
    turn_id: Optional[str]
    telemetry_status: str  # 'full' | 'transcript_only' | 'invalid_telemetry' | 'empty_answer'
    transcript_metrics: Dict[str, Any]
    timing_metrics: Dict[str, Any]
    speech_segments: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        serialized_transcript: Dict[str, Any] = {}
        for k, v in self.transcript_metrics.items():
            if isinstance(v, SpeechMetricValue):
                serialized_transcript[k] = v.to_dict()
            else:
                serialized_transcript[k] = v

        serialized_timing: Dict[str, Any] = {}
        for k, v in self.timing_metrics.items():
            if isinstance(v, SpeechMetricValue):
                serialized_timing[k] = v.to_dict()
            else:
                serialized_timing[k] = v

        return {
            "turn_id": self.turn_id,
            "telemetry_status": self.telemetry_status,
            "transcript_metrics": serialized_transcript,
            "timing_metrics": serialized_timing,
            "speech_segments": self.speech_segments,
        }


@dataclass
class SessionSpeechAnalytics:
    """
    Aggregated speech delivery roll-up across an entire interview session.
    """
    total_turns: int
    valid_timing_turns: int
    total_words: int
    total_duration_sec: Optional[float]
    average_speaking_pace_wpm: Optional[float]
    total_fillers: int
    average_filler_rate_pct: float
    filler_breakdown: Dict[str, int]
    most_frequent_fillers: List[Dict[str, Any]]
    pause_summary: Dict[str, Any]
    data_completeness: str  # 'full' | 'partial' | 'transcript_only' | 'no_data'
    delivery_observations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_turns": self.total_turns,
            "valid_timing_turns": self.valid_timing_turns,
            "total_words": self.total_words,
            "total_duration_sec": self.total_duration_sec,
            "average_speaking_pace_wpm": self.average_speaking_pace_wpm,
            "total_fillers": self.total_fillers,
            "average_filler_rate_pct": self.average_filler_rate_pct,
            "filler_breakdown": self.filler_breakdown,
            "most_frequent_fillers": self.most_frequent_fillers,
            "pause_summary": self.pause_summary,
            "data_completeness": self.data_completeness,
            "delivery_observations": self.delivery_observations,
        }


class SpeechDeliveryAnalyzer:
    """
    Analyzes per-turn speech responses and computes session-wide aggregates.
    """

    def __init__(self, conservative_like: bool = True):
        self.conservative_like = conservative_like

    def analyze_turn(
        self,
        transcript: Optional[str],
        telemetry: Optional[Dict[str, Any]] = None,
        turn_id: Optional[str] = None,
    ) -> TurnSpeechAnalytics:
        """
        Analyze a single candidate response.
        Safely computes transcript and timing metrics.
        """
        # 1. Transcript-derived metrics
        clean_text = transcript if isinstance(transcript, str) else ""
        word_count = count_words(clean_text)
        filler_data = find_filler_words(clean_text, conservative_like=self.conservative_like)
        filler_count = filler_data["total_count"]
        filler_rate = calculate_filler_rate(filler_count, word_count)

        transcript_metrics = {
            "word_count": SpeechMetricValue(
                value=word_count,
                unit="words",
                status="measured" if clean_text.strip() else "unavailable",
                confidence="high",
                details="Counted using token-boundary matching.",
            ),
            "filler_count": SpeechMetricValue(
                value=filler_count,
                unit="occurrences",
                status="measured" if clean_text.strip() else "unavailable",
                confidence="high",
                details="Detected from standardized hesitation lexicon.",
            ),
            "filler_rate_pct": SpeechMetricValue(
                value=filler_rate,
                unit="percentage",
                status="measured" if word_count > 0 else "unavailable",
                confidence="high" if word_count > 0 else "none",
                details="Percentage of total words identified as fillers.",
            ),
            "filler_breakdown": filler_data["breakdown"],
            "filler_by_category": filler_data["by_category"],
        }

        # 2. Audio timing metrics with safety validation
        clean_telemetry, validation_errors = validate_and_sanitize_telemetry(telemetry)
        has_errors = bool(validation_errors)

        if has_errors:
            duration_sec = None
            speaking_pace = None
            pause_data = {
                "status": "unavailable",
                "reliability": "none",
                "pause_count": None,
                "total_pause_duration_sec": None,
                "active_speech_duration_sec": None,
                "pause_events": [],
                "details": f"Invalid telemetry: {'; '.join(validation_errors)}",
            }
        else:
            duration_sec = calculate_duration_seconds(clean_telemetry)
            speaking_pace = calculate_speaking_pace(word_count, duration_sec)
            pause_data = extract_pause_metrics(clean_telemetry)

        timing_metrics = {
            "answer_duration_sec": SpeechMetricValue(
                value=duration_sec,
                unit="seconds",
                status="measured" if duration_sec is not None else "unavailable",
                confidence="high" if duration_sec is not None else "none",
                details="Derived from audio recording telemetry." if duration_sec is not None else (
                    f"Invalid telemetry: {'; '.join(validation_errors)}" if has_errors else "No valid timing telemetry provided."
                ),
            ),
            "speaking_pace_wpm": SpeechMetricValue(
                value=speaking_pace,
                unit="wpm",
                status="measured" if speaking_pace is not None else "unavailable",
                confidence="high" if speaking_pace is not None else "none",
                details="Calculated as (words / duration_sec) * 60." if speaking_pace is not None else "Requires duration >= 1.0s and valid timing.",
            ),
            "pause_count": SpeechMetricValue(
                value=pause_data.get("pause_count"),
                unit="count",
                status=pause_data["status"],
                confidence=pause_data["reliability"],
                details=pause_data["details"],
            ),
            "total_pause_duration_sec": SpeechMetricValue(
                value=pause_data.get("total_pause_duration_sec"),
                unit="seconds",
                status=pause_data["status"],
                confidence=pause_data["reliability"],
                details=pause_data["details"],
            ),
            "active_speech_duration_sec": SpeechMetricValue(
                value=pause_data.get("active_speech_duration_sec"),
                unit="seconds",
                status=pause_data["status"],
                confidence=pause_data["reliability"],
                details=pause_data["details"],
            ),
        }

        # Segments if present
        speech_segments: List[Dict[str, Any]] = []
        target_telemetry = clean_telemetry if not has_errors else telemetry
        if target_telemetry and isinstance(target_telemetry.get("speech_segments"), list):
            speech_segments = [s for s in target_telemetry["speech_segments"] if isinstance(s, dict)]

        # Determine overall telemetry status
        if not clean_text.strip():
            telemetry_status = "empty_answer"
        elif has_errors:
            telemetry_status = "invalid_telemetry"
        elif duration_sec is not None and pause_data["status"] == "measured":
            telemetry_status = "full"
        elif duration_sec is not None:
            telemetry_status = "duration_only"
        elif telemetry is not None:
            telemetry_status = "invalid_telemetry"
        else:
            telemetry_status = "transcript_only"

        return TurnSpeechAnalytics(
            turn_id=turn_id,
            telemetry_status=telemetry_status,
            transcript_metrics=transcript_metrics,
            timing_metrics=timing_metrics,
            speech_segments=speech_segments,
        )

    @staticmethod
    def _normalize_turn(item: Union[TurnSpeechAnalytics, Dict[str, Any]]) -> TurnSpeechAnalytics:
        """Safely convert a dict or TurnSpeechAnalytics into a TurnSpeechAnalytics object."""
        if isinstance(item, TurnSpeechAnalytics):
            return item

        if not isinstance(item, dict):
            return SpeechDeliveryAnalyzer().analyze_turn("")

        # Check if item is already a serialized speech analytics dict
        speech_analytics_data = item.get("speech_analytics") if "speech_analytics" in item else item
        if (
            isinstance(speech_analytics_data, dict)
            and "transcript_metrics" in speech_analytics_data
            and "timing_metrics" in speech_analytics_data
        ):
            t_metrics: Dict[str, Any] = {}
            for k, v in speech_analytics_data["transcript_metrics"].items():
                if isinstance(v, dict) and "value" in v:
                    t_metrics[k] = SpeechMetricValue(**v)
                else:
                    t_metrics[k] = v

            ti_metrics: Dict[str, Any] = {}
            for k, v in speech_analytics_data["timing_metrics"].items():
                if isinstance(v, dict) and "value" in v:
                    ti_metrics[k] = SpeechMetricValue(**v)
                else:
                    ti_metrics[k] = v

            return TurnSpeechAnalytics(
                turn_id=speech_analytics_data.get("turn_id"),
                telemetry_status=speech_analytics_data.get("telemetry_status", "transcript_only"),
                transcript_metrics=t_metrics,
                timing_metrics=ti_metrics,
                speech_segments=speech_analytics_data.get("speech_segments", []),
            )

        # Conversation history entry with 'answer' and optional 'speech_telemetry'
        return SpeechDeliveryAnalyzer().analyze_turn(
            transcript=item.get("answer", ""),
            telemetry=item.get("speech_telemetry"),
            turn_id=str(item.get("question_number")),
        )

    def aggregate_session(
        self,
        turns: List[Union[TurnSpeechAnalytics, Dict[str, Any]]],
    ) -> SessionSpeechAnalytics:
        """
        Aggregate multiple turn analytics into an interview session roll-up.
        Accepts TurnSpeechAnalytics objects, serialized analytics dicts,
        or conversation_history turns.
        """
        if not turns:
            return SessionSpeechAnalytics(
                total_turns=0,
                valid_timing_turns=0,
                total_words=0,
                total_duration_sec=None,
                average_speaking_pace_wpm=None,
                total_fillers=0,
                average_filler_rate_pct=0.0,
                filler_breakdown={},
                most_frequent_fillers=[],
                pause_summary={
                    "total_pauses": None,
                    "total_pause_duration_sec": None,
                    "status": "unavailable",
                    "details": "No interview turns to aggregate.",
                },
                data_completeness="no_data",
                delivery_observations=["No speech data recorded for this session."],
            )

        normalized_turns = [self._normalize_turn(t) for t in turns]
        total_turns = len(normalized_turns)
        total_words = 0
        total_fillers = 0
        combined_breakdown: Dict[str, int] = {}

        timed_turn_count = 0
        total_duration = 0.0
        pace_samples: List[float] = []

        pause_measured_count = 0
        total_pauses = 0
        total_pause_duration = 0.0

        for turn in normalized_turns:
            # Word & filler aggregation
            wc_metric = turn.transcript_metrics.get("word_count")
            if wc_metric and wc_metric.value is not None:
                total_words += int(wc_metric.value)

            fc_metric = turn.transcript_metrics.get("filler_count")
            if fc_metric and fc_metric.value is not None:
                total_fillers += int(fc_metric.value)

            breakdown = turn.transcript_metrics.get("filler_breakdown", {})
            if isinstance(breakdown, dict):
                for f_word, count in breakdown.items():
                    combined_breakdown[f_word] = combined_breakdown.get(f_word, 0) + count

            # Timing aggregation
            dur_metric = turn.timing_metrics.get("answer_duration_sec")
            if dur_metric and dur_metric.value is not None:
                try:
                    dur_val = float(dur_metric.value)
                    total_duration += dur_val
                    timed_turn_count += 1
                except (ValueError, TypeError):
                    pass

            pace_metric = turn.timing_metrics.get("speaking_pace_wpm")
            if pace_metric and pace_metric.value is not None:
                try:
                    pace_val = float(pace_metric.value)
                    pace_samples.append(pace_val)
                except (ValueError, TypeError):
                    pass

            # Pause aggregation
            pause_metric = turn.timing_metrics.get("pause_count")
            pause_dur_metric = turn.timing_metrics.get("total_pause_duration_sec")
            if pause_metric and pause_metric.status == "measured" and pause_metric.value is not None:
                pause_measured_count += 1
                total_pauses += int(pause_metric.value)
                if pause_dur_metric and pause_dur_metric.value is not None:
                    total_pause_duration += float(pause_dur_metric.value)

        # Average speaking pace
        avg_pace: Optional[float] = None
        if total_duration >= 1.0 and total_words > 0:
            avg_pace = round((total_words / total_duration) * 60.0, 1)
        elif pace_samples:
            avg_pace = round(sum(pace_samples) / len(pace_samples), 1)

        # Average filler rate across session
        avg_filler_rate = calculate_filler_rate(total_fillers, total_words)

        # Top fillers
        sorted_fillers = sorted(
            [{"filler": k, "count": v} for k, v in combined_breakdown.items()],
            key=lambda item: item["count"],
            reverse=True,
        )

        # Pause summary
        if pause_measured_count > 0:
            pause_summary = {
                "total_pauses": total_pauses,
                "total_pause_duration_sec": round(total_pause_duration, 2),
                "measured_turns": pause_measured_count,
                "status": "measured",
                "details": f"Measured across {pause_measured_count} turns with audio telemetry.",
            }
        else:
            pause_summary = {
                "total_pauses": None,
                "total_pause_duration_sec": None,
                "measured_turns": 0,
                "status": "unavailable",
                "details": "Audio pause telemetry was not provided; pause metrics were not inferred from text.",
            }

        # Data completeness label
        if timed_turn_count == total_turns and pause_measured_count == total_turns:
            completeness = "full"
        elif timed_turn_count > 0:
            completeness = "partial"
        else:
            completeness = "transcript_only"

        # Generate neutral, objective delivery observations
        observations = self._generate_observations(
            total_words=total_words,
            timed_turn_count=timed_turn_count,
            total_turns=total_turns,
            avg_pace=avg_pace,
            avg_filler_rate=avg_filler_rate,
            sorted_fillers=sorted_fillers,
            pause_summary=pause_summary,
        )

        return SessionSpeechAnalytics(
            total_turns=total_turns,
            valid_timing_turns=timed_turn_count,
            total_words=total_words,
            total_duration_sec=round(total_duration, 2) if timed_turn_count > 0 else None,
            average_speaking_pace_wpm=avg_pace,
            total_fillers=total_fillers,
            average_filler_rate_pct=avg_filler_rate,
            filler_breakdown=combined_breakdown,
            most_frequent_fillers=sorted_fillers[:5],
            pause_summary=pause_summary,
            data_completeness=completeness,
            delivery_observations=observations,
        )

    def _generate_observations(
        self,
        total_words: int,
        timed_turn_count: int,
        total_turns: int,
        avg_pace: Optional[float],
        avg_filler_rate: float,
        sorted_fillers: List[Dict[str, Any]],
        pause_summary: Dict[str, Any],
    ) -> List[str]:
        """
        Generate purely factual, descriptive, non-punitive observations.
        Does not penalize accents, pauses, or speaking pace variations.
        """
        obs: List[str] = []

        if total_words == 0:
            obs.append("Candidate responses contained no detectable spoken words.")
            return obs

        # Pacing observation
        if avg_pace is not None:
            if 120 <= avg_pace <= 165:
                obs.append(
                    f"Candidate spoke at an average pace of {avg_pace} WPM, which is within the standard conversational range (120–165 WPM)."
                )
            elif avg_pace < 120:
                obs.append(
                    f"Candidate spoke at a deliberate pace of {avg_pace} WPM. A slower pace often reflects deliberate structuring or technical explanation."
                )
            else:
                obs.append(
                    f"Candidate spoke at a fast pace of {avg_pace} WPM. Rapid delivery can demonstrate familiarity or enthusiasm with the subject."
                )
        else:
            obs.append("Speaking pace was unavailable because audio timing telemetry was not recorded.")

        # Filler rate observation
        if avg_filler_rate == 0.0:
            obs.append("No standard hesitation words or filler expressions were detected in the transcripts.")
        elif avg_filler_rate <= 3.0:
            obs.append(
                f"Filler usage was minimal at {avg_filler_rate}% of spoken words. Hesitation markers were infrequent."
            )
        else:
            top_words = ", ".join(f"'{f['filler']}'" for f in sorted_fillers[:3])
            obs.append(
                f"Filler word rate was {avg_filler_rate}% ({top_words}). Occasional filler words are natural during spontaneous speech and cognitive synthesis."
            )

        # Pause observation
        if pause_summary.get("status") == "measured" and pause_summary.get("total_pauses") is not None:
            p_count = pause_summary["total_pauses"]
            p_sec = pause_summary["total_pause_duration_sec"]
            obs.append(
                f"A total of {p_count} pause events ({p_sec}s total silence) were recorded across {pause_summary['measured_turns']} timed turns."
            )
        else:
            obs.append("Audio pause telemetry was not recorded; pauses were not inferred from transcript text.")

        return obs
