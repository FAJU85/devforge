#!/usr/bin/env python3
"""
LoadTestAnalyzer Agent - Phase 8.6.1
Analyzes load test results and identifies performance patterns
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .tools import LoadTestTools

logger = logging.getLogger(__name__)


class LoadTestAnalyzer:
    """
    Analyzes load test results to identify:
    - Performance bottlenecks
    - Latency patterns
    - Error trends
    - Capacity constraints
    """

    def __init__(self):
        self.tools = LoadTestTools()
        self.logger = logger
        self.conversation_history: List[Dict[str, str]] = []
        self.analysis_id: Optional[str] = None

    async def fetch_test_results(self, test_id: str) -> Dict[str, Any]:
        """Fetch load test results"""
        try:
            self.logger.info(f"Fetching results for test: {test_id}")

            metrics = await self.tools.get_load_test_results(test_id)

            message = (
                f"Loaded test {test_id}: {metrics.total_requests} requests, "
                f"{metrics.successful} successful, {metrics.error_rate:.2f}% error rate"
            )
            self._add_to_history("assistant", message)

            return metrics.dict()

        except Exception as e:
            self.logger.error(f"Error fetching results: {e}")
            self._add_to_history("assistant", f"Error fetching results: {str(e)}")
            raise

    async def analyze_latency_patterns(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze latency patterns in metrics"""
        try:
            self.logger.info("Analyzing latency patterns")

            analysis = await self.tools.analyze_latency(metrics)

            self._add_to_history(
                "assistant",
                f"Latency analysis: avg={metrics.get('avg_latency_ms')}ms, "
                f"p95={metrics.get('p95_latency_ms')}ms, p99={metrics.get('p99_latency_ms')}ms"
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Error analyzing latency: {e}")
            self._add_to_history("assistant", f"Error analyzing latency: {str(e)}")
            raise

    async def find_bottlenecks(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Identify performance bottlenecks"""
        try:
            self.logger.info("Identifying bottlenecks")

            bottleneck_analysis = await self.tools.identify_bottlenecks(metrics)

            bottleneck_count = len(bottleneck_analysis.bottlenecks)
            message = f"Identified {bottleneck_count} bottlenecks"

            for bottleneck in bottleneck_analysis.bottlenecks:
                message += f"\n- [{bottleneck['severity']}] {bottleneck['type']}"

            self._add_to_history("assistant", message)

            return {
                "bottlenecks": [b.dict() for b in bottleneck_analysis.bottlenecks],
                "severity_levels": bottleneck_analysis.severity_levels
            }

        except Exception as e:
            self.logger.error(f"Error identifying bottlenecks: {e}")
            self._add_to_history("assistant", f"Error identifying bottlenecks: {str(e)}")
            raise

    async def compare_test_runs(self, run1_id: str, run2_id: str) -> Dict[str, Any]:
        """Compare two test runs"""
        try:
            self.logger.info(f"Comparing runs: {run1_id} vs {run2_id}")

            comparison = await self.tools.compare_runs(run1_id, run2_id)

            improvement = comparison.get("improvement", {})
            message = (
                f"Comparison results:\n"
                f"- Latency: {improvement.get('latency_reduction_percent', 0):.1f}% reduction\n"
                f"- Throughput: {improvement.get('throughput_increase_percent', 0):.1f}% increase\n"
                f"- Errors: {improvement.get('error_rate_reduction_percent', 0):.1f}% reduction"
            )

            self._add_to_history("assistant", message)

            return comparison

        except Exception as e:
            self.logger.error(f"Error comparing runs: {e}")
            self._add_to_history("assistant", f"Error comparing runs: {str(e)}")
            raise

    async def generate_analysis_report(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        try:
            self.logger.info("Generating analysis report")

            report = await self.tools.generate_report(analysis_data)

            self._add_to_history(
                "assistant",
                f"Generated report {report['report_id']}"
            )

            return report

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            self._add_to_history("assistant", f"Error generating report: {str(e)}")
            raise

    async def execute_analysis(self, test_id: str) -> Dict[str, Any]:
        """Execute complete load test analysis workflow"""
        try:
            self.analysis_id = f"analysis_{datetime.utcnow().timestamp()}"
            self.logger.info(f"Starting analysis: {self.analysis_id}")

            self._add_to_history("user", f"Analyze load test results for {test_id}")

            # Step 1: Fetch results
            metrics = await self.fetch_test_results(test_id)

            # Step 2: Analyze latency
            latency_analysis = await self.analyze_latency_patterns(metrics)

            # Step 3: Identify bottlenecks
            bottleneck_analysis = await self.find_bottlenecks(metrics)

            # Step 4: Generate report
            full_analysis = {
                "metrics": metrics,
                "latency_analysis": latency_analysis,
                "bottleneck_analysis": bottleneck_analysis
            }

            report = await self.generate_analysis_report(full_analysis)

            result = {
                "analysis_id": self.analysis_id,
                "test_id": test_id,
                "status": "completed",
                "metrics": metrics,
                "latency_analysis": latency_analysis,
                "bottleneck_analysis": bottleneck_analysis,
                "report": report,
                "conversation_history": self.conversation_history
            }

            self.logger.info(f"Analysis {self.analysis_id} completed")

            return result

        except Exception as e:
            self.logger.error(f"Analysis execution failed: {e}")
            return {
                "analysis_id": self.analysis_id,
                "status": "failed",
                "error": str(e),
                "conversation_history": self.conversation_history
            }

    def _add_to_history(self, role: str, message: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get full conversation history"""
        return self.conversation_history

    def reset(self):
        """Reset agent state"""
        self.conversation_history = []
        self.analysis_id = None
