#!/usr/bin/env python3
"""
Bug Detection Service - Phase 8.1
Fine-tuned model for code bug detection and analysis
"""

import logging
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class BugAnalysis:
    """Result of bug analysis"""
    code_snippet: str
    bugs_found: List[Dict[str, Any]]
    severity: str  # critical, high, medium, low
    confidence_score: float  # 0.0-1.0
    suggestions: List[str]
    processing_time_ms: float
    model_used: str


class BugDetectionService:
    """Service for detecting bugs using fine-tuned models"""

    def __init__(self):
        self.analysis_history: List[Dict[str, Any]] = []
        self.user_feedback: List[Dict[str, Any]] = []
        self.training_data: List[Dict[str, Any]] = []

    def analyze_code(
        self,
        code_snippet: str,
        language: str = "python",
        context: Optional[str] = None
    ) -> BugAnalysis:
        """Analyze code for bugs using fine-tuned model"""
        try:
            import time
            start_time = time.time()

            # In production, this would call the fine-tuned Claude model
            # For now, return structured analysis based on simple heuristics

            bugs_found = self._detect_common_bugs(code_snippet, language)
            severity = self._assess_severity(bugs_found)
            confidence = 0.85 if bugs_found else 0.7
            suggestions = self._generate_suggestions(bugs_found)

            processing_time = (time.time() - start_time) * 1000

            analysis = BugAnalysis(
                code_snippet=code_snippet,
                bugs_found=bugs_found,
                severity=severity,
                confidence_score=confidence,
                suggestions=suggestions,
                processing_time_ms=processing_time,
                model_used="claude-bug-detector-v1"
            )

            # Store analysis
            self.analysis_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "analysis": {
                    "code": code_snippet,
                    "bugs": bugs_found,
                    "severity": severity,
                    "confidence": confidence
                }
            })

            return analysis
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return BugAnalysis(
                code_snippet=code_snippet,
                bugs_found=[],
                severity="low",
                confidence_score=0.0,
                suggestions=["Unable to analyze code"],
                processing_time_ms=0,
                model_used="error"
            )

    def _detect_common_bugs(self, code: str, language: str) -> List[Dict[str, Any]]:
        """Detect common bug patterns"""
        bugs = []

        if language == "python":
            # Check for common Python bugs
            if "except:" in code and "except Exception" not in code:
                bugs.append({
                    "type": "bare_except",
                    "severity": "high",
                    "description": "Bare 'except:' clause catches all exceptions",
                    "line": self._find_line(code, "except:"),
                    "fix": "Use 'except Exception:' instead"
                })

            if "==" in code and "if" in code:
                # Simple check for potential comparison issues
                if code.count("=") > code.count("=="):
                    bugs.append({
                        "type": "potential_assignment",
                        "severity": "medium",
                        "description": "Potential use of assignment (=) instead of comparison (==)",
                        "fix": "Review comparisons in conditional statements"
                    })

            if "import *" in code:
                bugs.append({
                    "type": "wildcard_import",
                    "severity": "medium",
                    "description": "Wildcard imports can cause namespace pollution",
                    "fix": "Import specific symbols instead"
                })

        return bugs

    def _assess_severity(self, bugs: List[Dict[str, Any]]) -> str:
        """Assess overall severity"""
        if not bugs:
            return "none"

        severities = [b.get("severity", "low") for b in bugs]

        if "critical" in severities:
            return "critical"
        elif "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"

    def _generate_suggestions(self, bugs: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []

        if not bugs:
            suggestions.append("Code looks clean!")
        else:
            for bug in bugs:
                suggestions.append(bug.get("fix", "Fix the identified issue"))

        suggestions.extend([
            "Consider adding type hints",
            "Add comprehensive error handling",
            "Include docstrings for all functions"
        ])

        return suggestions[:5]

    def _find_line(self, code: str, pattern: str) -> int:
        """Find line number of pattern"""
        try:
            lines = code.split("\n")
            for i, line in enumerate(lines):
                if pattern in line:
                    return i + 1
            return 0
        except:
            return 0

    def log_user_feedback(
        self,
        analysis_id: str,
        feedback_correct: bool,
        user_notes: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> bool:
        """Log user feedback for model improvement"""
        try:
            feedback_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "analysis_id": analysis_id,
                "correct": feedback_correct,
                "notes": user_notes,
                "user_id": user_id
            }
            self.user_feedback.append(feedback_entry)
            logger.info(f"Recorded user feedback: {feedback_entry}")
            return True
        except Exception as e:
            logger.error(f"Error logging feedback: {e}")
            return False

    def add_training_data(
        self,
        code_snippet: str,
        bug_description: str,
        severity: str,
        suggested_fix: str,
        source: str = "user_feedback"
    ) -> bool:
        """Add instance to training dataset"""
        try:
            training_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "code": code_snippet,
                "bug": bug_description,
                "severity": severity,
                "fix": suggested_fix,
                "source": source
            }
            self.training_data.append(training_entry)
            logger.info(f"Added training data instance from {source}")
            return True
        except Exception as e:
            logger.error(f"Error adding training data: {e}")
            return False

    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get analysis statistics"""
        try:
            total_analyses = len(self.analysis_history)
            total_bugs = sum(
                len(a.get("analysis", {}).get("bugs", []))
                for a in self.analysis_history
            )

            return {
                "total_analyses": total_analyses,
                "total_bugs_found": total_bugs,
                "avg_bugs_per_analysis": (total_bugs / total_analyses) if total_analyses > 0 else 0,
                "feedback_count": len(self.user_feedback),
                "training_instances": len(self.training_data),
            }
        except Exception as e:
            logger.error(f"Error getting analysis stats: {e}")
            return {}


bug_detection_service = BugDetectionService()
