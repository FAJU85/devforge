#!/usr/bin/env python3
"""
PerformanceAdvisor Agent - Phase 8.6.1
Recommends performance optimizations based on analysis
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from .tools import PerformanceTools

logger = logging.getLogger(__name__)


class PerformanceAdvisor:
    """
    Provides performance optimization recommendations:
    - Caching strategies
    - Database indexing
    - Query optimization
    - Scaling decisions
    """

    def __init__(self):
        self.tools = PerformanceTools()
        self.logger = logger
        self.conversation_history: List[Dict[str, str]] = []
        self.recommendation_id: Optional[str] = None

    async def analyze_caching_opportunities(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze caching opportunities"""
        try:
            self.logger.info(f"Analyzing caching for {len(queries)} queries")

            recommendations = await self.tools.analyze_cache_strategy(queries)

            message = f"Identified {len(recommendations)} caching opportunities"
            self._add_to_history("assistant", message)

            return [r.dict() for r in recommendations]

        except Exception as e:
            self.logger.error(f"Error analyzing cache strategy: {e}")
            self._add_to_history("assistant", f"Error analyzing caching: {str(e)}")
            raise

    async def analyze_indexing_opportunities(self, slow_queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze database indexing opportunities"""
        try:
            self.logger.info(f"Analyzing indexing for {len(slow_queries)} slow queries")

            recommendations = await self.tools.suggest_indexes(slow_queries)

            message = f"Suggested {len(recommendations)} index improvements"
            self._add_to_history("assistant", message)

            return [r.dict() for r in recommendations]

        except Exception as e:
            self.logger.error(f"Error suggesting indexes: {e}")
            self._add_to_history("assistant", f"Error analyzing indexing: {str(e)}")
            raise

    async def review_query_performance(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Review and optimize query patterns"""
        try:
            self.logger.info(f"Reviewing {len(queries)} query patterns")

            analysis = await self.tools.review_query_patterns(queries)

            message = (
                f"Reviewed {analysis['total_queries_analyzed']} queries, "
                f"found {analysis['optimization_opportunities']} optimization opportunities, "
                f"estimated improvement: {analysis['estimated_total_improvement']:.1f}%"
            )
            self._add_to_history("assistant", message)

            return analysis

        except Exception as e:
            self.logger.error(f"Error reviewing queries: {e}")
            self._add_to_history("assistant", f"Error reviewing queries: {str(e)}")
            raise

    async def evaluate_scaling_needs(
        self,
        metrics: Dict[str, Any],
        projected_load: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate scaling requirements"""
        try:
            self.logger.info("Evaluating scaling needs")

            recommendation = await self.tools.recommend_scaling(metrics, projected_load)

            self._add_to_history(
                "assistant",
                f"Scaling recommendation: {recommendation.recommendation} "
                f"(Priority: {recommendation.priority})"
            )

            return recommendation.dict()

        except Exception as e:
            self.logger.error(f"Error recommending scaling: {e}")
            self._add_to_history("assistant", f"Error evaluating scaling: {str(e)}")
            raise

    async def prioritize_recommendations(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Prioritize recommendations by impact and complexity"""
        try:
            self.logger.info(f"Prioritizing {len(recommendations)} recommendations")

            # Sort by priority and estimated improvement
            priority_scores = {
                "critical": 4,
                "high": 3,
                "medium": 2,
                "low": 1
            }

            complexity_multipliers = {
                "low": 1.0,
                "medium": 0.7,
                "high": 0.5
            }

            scored_recommendations = []
            for rec in recommendations:
                priority_score = priority_scores.get(rec.get("priority", "low"), 1)
                complexity_multiplier = complexity_multipliers.get(
                    rec.get("implementation_complexity", "medium"),
                    0.7
                )
                improvement = rec.get("estimated_improvement", 0)

                # Score = (priority * improvement) / complexity
                score = (priority_score * improvement) * complexity_multiplier

                scored_recommendations.append({
                    **rec,
                    "score": score
                })

            # Sort by score descending
            sorted_recs = sorted(scored_recommendations, key=lambda x: x["score"], reverse=True)

            message = f"Prioritized {len(sorted_recs)} recommendations by impact/complexity"
            self._add_to_history("assistant", message)

            return sorted_recs

        except Exception as e:
            self.logger.error(f"Error prioritizing recommendations: {e}")
            self._add_to_history("assistant", f"Error prioritizing: {str(e)}")
            raise

    async def execute_analysis(
        self,
        metrics: Dict[str, Any],
        queries: List[Dict[str, Any]],
        projected_load: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute complete performance analysis and recommendations"""
        try:
            self.recommendation_id = f"perf_rec_{datetime.utcnow().timestamp()}"
            self.logger.info(f"Starting performance analysis: {self.recommendation_id}")

            self._add_to_history("user", "Analyze performance and provide optimization recommendations")

            # Step 1: Cache analysis
            caching_recs = await self.analyze_caching_opportunities(queries)

            # Step 2: Indexing analysis
            slow_queries = [q for q in queries if q.get("execution_time_ms", 0) > 100]
            indexing_recs = await self.analyze_indexing_opportunities(slow_queries)

            # Step 3: Query pattern review
            query_analysis = await self.review_query_performance(queries)

            # Step 4: Scaling evaluation
            scaling_rec = await self.evaluate_scaling_needs(metrics, projected_load)

            # Step 5: Combine and prioritize all recommendations
            all_recommendations = caching_recs + indexing_recs
            if scaling_rec.get("priority") in ["critical", "high"]:
                all_recommendations.append(scaling_rec)

            prioritized = await self.prioritize_recommendations(all_recommendations)

            result = {
                "recommendation_id": self.recommendation_id,
                "status": "completed",
                "analysis": {
                    "caching_analysis": caching_recs,
                    "indexing_analysis": indexing_recs,
                    "query_analysis": query_analysis,
                    "scaling_recommendation": scaling_rec
                },
                "prioritized_recommendations": prioritized,
                "total_estimated_improvement": sum(
                    r.get("estimated_improvement", 0) for r in prioritized
                ) / len(prioritized) if prioritized else 0,
                "conversation_history": self.conversation_history
            }

            self.logger.info(f"Performance analysis {self.recommendation_id} completed")

            return result

        except Exception as e:
            self.logger.error(f"Analysis execution failed: {e}")
            return {
                "recommendation_id": self.recommendation_id,
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
        self.recommendation_id = None
