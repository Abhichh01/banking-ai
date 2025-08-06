"""
Enhanced AI model repository with AI integration for AI service management and analytics.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, select, func, text, desc, or_
from sqlalchemy.orm import selectinload

from app.models.ai_models import (
    AIRecommendation, RecommendationType, RecommendationStatus,
    BehavioralPattern, BehavioralPatternType,
    FraudAlert, FraudAlertSeverity, FraudAlertStatus
)
from app.schemas.ai import (
    AIRecommendationCreate, AIRecommendationUpdate,
    BehavioralPatternCreate, BehavioralPatternUpdate,
    FraudAlertCreate, FraudAlertUpdate
)
from app.repositories.enhanced_base import AIEnhancedRepository
from app.core.llm_orchestrator import TaskType, TaskComplexity
# Exception imports removed for MVP
# All custom exceptions replaced with standard logging

logger = logging.getLogger(__name__)


class EnhancedAIModelRepository(AIEnhancedRepository[AIRecommendation, AIRecommendationCreate, AIRecommendationUpdate]):
    """
    Enhanced AI model repository with AI-powered service management and analytics.
    
    Features:
    - AI recommendation management and analytics
    - Behavioral pattern analysis and insights
    - Fraud alert management and analysis
    - Model performance monitoring
    - AI service health monitoring
    - Recommendation effectiveness tracking
    """

    def __init__(
        self,
        db_session,
        llm_orchestrator=None,
        cache_manager=None
    ):
        super().__init__(AIRecommendation, db_session, llm_orchestrator, cache_manager)

    # ==================== Enhanced CRUD Operations ====================

    async def get_recommendations_by_user(
        self,
        user_id: int,
        status: Optional[RecommendationStatus] = None,
        recommendation_type: Optional[RecommendationType] = None,
        include_expired: bool = False,
        use_cache: bool = True
    ) -> List[AIRecommendation]:
        """Get AI recommendations for a user with filtering."""
        cache_key = f"user_recommendations:{user_id}:{status.value if status else 'all'}:{recommendation_type.value if recommendation_type else 'all'}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(AIRecommendation).where(AIRecommendation.user_id == user_id)

        if status:
            query = query.where(AIRecommendation.status == status)
        if recommendation_type:
            query = query.where(AIRecommendation.recommendation_type == recommendation_type)
        if not include_expired:
            query = query.where(
                or_(
                    AIRecommendation.valid_until.is_(None),
                    AIRecommendation.valid_until > datetime.utcnow()
                )
            )

        query = query.order_by(desc(AIRecommendation.created_at))

        result = await self.db_session.execute(query)
        recommendations = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, recommendations, ttl=900)  # 15 minutes

        return recommendations

    async def get_active_recommendations(
        self,
        user_id: int,
        use_cache: bool = True
    ) -> List[AIRecommendation]:
        """Get active (non-expired) recommendations for a user."""
        return await self.get_recommendations_by_user(
            user_id, 
            status=RecommendationStatus.PENDING,
            include_expired=False,
            use_cache=use_cache
        )

    async def get_behavioral_patterns_by_user(
        self,
        user_id: int,
        pattern_type: Optional[BehavioralPatternType] = None,
        is_active: bool = True,
        use_cache: bool = True
    ) -> List[BehavioralPattern]:
        """Get behavioral patterns for a user with filtering."""
        cache_key = f"user_behavioral_patterns:{user_id}:{pattern_type.value if pattern_type else 'all'}:{is_active}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(BehavioralPattern).where(BehavioralPattern.user_id == user_id)

        if pattern_type:
            query = query.where(BehavioralPattern.pattern_type == pattern_type)
        if is_active:
            query = query.where(BehavioralPattern.is_active == True)  # noqa: E712

        query = query.order_by(desc(BehavioralPattern.detected_at))

        result = await self.db_session.execute(query)
        patterns = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, patterns, ttl=900)  # 15 minutes

        return patterns

    async def get_fraud_alerts_by_user(
        self,
        user_id: int,
        status: Optional[FraudAlertStatus] = None,
        severity: Optional[FraudAlertSeverity] = None,
        use_cache: bool = True
    ) -> List[FraudAlert]:
        """Get fraud alerts for a user with filtering."""
        cache_key = f"user_fraud_alerts:{user_id}:{status.value if status else 'all'}:{severity.value if severity else 'all'}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(FraudAlert).where(FraudAlert.user_id == user_id)

        if status:
            query = query.where(FraudAlert.status == status)
        if severity:
            query = query.where(FraudAlert.severity == severity)

        query = query.order_by(desc(FraudAlert.detected_at))

        result = await self.db_session.execute(query)
        alerts = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, alerts, ttl=900)  # 15 minutes

        return alerts

    # ==================== AI Integration Methods ====================

    async def analyze_recommendation_effectiveness(
        self,
        user_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Analyze recommendation effectiveness using AI."""
        try:
            # Get recommendation data
            recommendation_data = await self._get_recommendation_data_for_analysis(user_id, "effectiveness", time_range)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                recommendation_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.HIGH
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Recommendation effectiveness analysis failed: {str(e)}")
        return {}

    async def generate_personalized_recommendations(
        self,
        user_id: int,
        recommendation_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate personalized AI recommendations for user."""
        try:
            # Get user data
            user_data = await self._get_user_data_for_analysis(user_id, "recommendation")

            # Generate AI recommendations
            recommendations = await self.analyze_with_ai(
                user_data,
                TaskType.FINANCIAL_RECOMMENDATION,
                TaskComplexity.HIGH
            )

            return recommendations

        except Exception as e:
            logger.error(f"Personalized recommendation generation failed: {str(e)}")
        return {}

    async def analyze_behavioral_patterns(
        self,
        user_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Analyze behavioral patterns using AI."""
        try:
            # Get behavioral pattern data
            pattern_data = await self._get_behavioral_pattern_data_for_analysis(user_id, "analysis", time_range)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                pattern_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.HIGH
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Behavioral pattern analysis failed: {str(e)}")
            return {}

    # ==================== Advanced Analytics Methods ====================

    async def get_ai_analytics(
        self,
        user_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive AI analytics for user."""
        cache_key = f"ai_analytics:{user_id}:{time_range}"

        # Check cache first
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return cached

        try:
            # Get recommendations
            recommendations = await self.get_recommendations_by_user(user_id, include_expired=True)

            # Get behavioral patterns
            behavioral_patterns = await self.get_behavioral_patterns_by_user(user_id)

            # Get fraud alerts
            fraud_alerts = await self.get_fraud_alerts_by_user(user_id)

            # Calculate AI metrics
            ai_metrics = await self._calculate_ai_metrics(recommendations, behavioral_patterns, fraud_alerts)

            # Analyze patterns
            pattern_analysis = await self._analyze_patterns(recommendations, behavioral_patterns, fraud_alerts)

            # Generate AI insights
            ai_insights = await self.analyze_recommendation_effectiveness(user_id, time_range)

            analytics_result = {
                "user_id": user_id,
                "time_range": time_range,
                "ai_metrics": ai_metrics,
                "pattern_analysis": pattern_analysis,
                "ai_insights": ai_insights,
                "generated_at": datetime.utcnow().isoformat()
            }

            # Cache the result
            await self.cache_manager.set(cache_key, analytics_result, ttl=3600)  # 1 hour

            return analytics_result

        except Exception as e:
            logger.error(f"AI analytics failed: {str(e)}")
            return {}

    async def get_recommendation_performance(
        self,
        user_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Get recommendation performance metrics."""
        try:
            # Get AI analytics
            analytics = await self.get_ai_analytics(user_id, time_range)

            # Calculate performance metrics
            performance_metrics = await self._calculate_recommendation_performance_metrics(analytics)

            return {
                "user_id": user_id,
                "time_range": time_range,
                "performance_metrics": performance_metrics,
                "recommendations": analytics.get("ai_insights", {}).get("recommendations", [])
            }

        except Exception as e:
            logger.error(f"Recommendation performance analysis failed: {str(e)}")
            return {}

    async def get_behavioral_insights(
        self,
        user_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Get behavioral insights and analysis."""
        try:
            # Get behavioral patterns
            patterns = await self.get_behavioral_patterns_by_user(user_id)

            # Analyze patterns with AI
            pattern_analysis = await self.analyze_behavioral_patterns(user_id, time_range)

            # Calculate behavioral metrics
            behavioral_metrics = await self._calculate_behavioral_metrics(patterns)

            return {
                "user_id": user_id,
                "time_range": time_range,
                "behavioral_metrics": behavioral_metrics,
                "pattern_analysis": pattern_analysis,
                "insights": await self._generate_behavioral_insights(patterns, behavioral_metrics)
            }

        except Exception as e:
            logger.error(f"Behavioral insights analysis failed: {str(e)}")
            return {}

    # ==================== Implementation of Abstract Methods ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for AI analysis."""
        try:
            # Get recommendations
            recommendations = await self.get_recommendations_by_user(user_id, include_expired=True)

            # Get behavioral patterns
            behavioral_patterns = await self.get_behavioral_patterns_by_user(user_id)

            # Get fraud alerts
            fraud_alerts = await self.get_fraud_alerts_by_user(user_id)

            return {
                "recommendations": [rec.to_dict() for rec in recommendations],
                "behavioral_patterns": [pattern.to_dict() for pattern in behavioral_patterns],
                "fraud_alerts": [alert.to_dict() for alert in fraud_alerts],
                "data_type": data_type,
                "time_range": time_range
            }

        except Exception as e:
            logger.error(f"Failed to get user data for analysis: {str(e)}")
            raise

    async def _get_user_transactions(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user transactions for analysis."""
        try:
            # This would typically query transactions for the user
            # For now, return empty list as transaction relationship needs to be implemented
            return []

        except Exception as e:
            logger.error(f"Failed to get user transactions: {str(e)}")
            raise

    async def _get_user_risk_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data for risk assessment."""
        try:
            # Get fraud alerts
            fraud_alerts = await self.get_fraud_alerts_by_user(user_id)

            # Get behavioral patterns
            behavioral_patterns = await self.get_behavioral_patterns_by_user(user_id)

            return {
                "fraud_alerts": [alert.to_dict() for alert in fraud_alerts],
                "behavioral_patterns": [pattern.to_dict() for pattern in behavioral_patterns],
                "risk_indicators": await self._calculate_ai_risk_indicators(user_id)
            }

        except Exception as e:
            logger.error(f"Failed to get user risk data: {str(e)}")
            raise

    async def _analyze_spending_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze spending patterns from transactions."""
        try:
            if not transactions:
                return {}

            # Group by category
            category_spending = {}
            for transaction in transactions:
                category = transaction.get("transaction_category", "Other")
                amount = float(transaction.get("amount", 0))
                category_spending[category] = category_spending.get(category, 0) + amount

            # Calculate statistics
            amounts = [float(t.get("amount", 0)) for t in transactions]
            total_spending = sum(amounts)
            avg_transaction = total_spending / len(transactions) if transactions else 0

            return {
                "total_spending": total_spending,
                "average_transaction": avg_transaction,
                "category_breakdown": category_spending,
                "transaction_count": len(transactions),
                "spending_frequency": len(transactions) / 30  # transactions per day
            }

        except Exception as e:
            logger.error(f"Failed to analyze spending patterns: {str(e)}")
            raise

    async def _analyze_temporal_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns from transactions."""
        try:
            if not transactions:
                return {}

            # Group by hour of day
            hourly_patterns = {}
            for transaction in transactions:
                transaction_date = transaction.get("transaction_date")
                if transaction_date:
                    hour = datetime.fromisoformat(transaction_date).hour
                    hourly_patterns[hour] = hourly_patterns.get(hour, 0) + 1

            # Group by day of week
            daily_patterns = {}
            for transaction in transactions:
                transaction_date = transaction.get("transaction_date")
                if transaction_date:
                    day = datetime.fromisoformat(transaction_date).strftime("%A")
                    daily_patterns[day] = daily_patterns.get(day, 0) + 1

            return {
                "hourly_patterns": hourly_patterns,
                "daily_patterns": daily_patterns,
                "peak_hours": sorted(hourly_patterns.items(), key=lambda x: x[1], reverse=True)[:3],
                "peak_days": sorted(daily_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
            }

        except Exception as e:
            logger.error(f"Failed to analyze temporal patterns: {str(e)}")
            raise

    async def _analyze_geographic_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze geographic patterns from transactions."""
        try:
            if not transactions:
                return {}

            # Group by location
            location_patterns = {}
            for transaction in transactions:
                location_city = transaction.get("location_city", "Unknown")
                location_country = transaction.get("location_country", "Unknown")
                location_key = f"{location_city}, {location_country}"
                location_patterns[location_key] = location_patterns.get(location_key, 0) + 1

            return {
                "location_patterns": location_patterns,
                "most_frequent_locations": sorted(location_patterns.items(), key=lambda x: x[1], reverse=True)[:5],
                "total_locations": len(location_patterns)
            }

        except Exception as e:
            logger.error(f"Failed to analyze geographic patterns: {str(e)}")
            raise

    async def _perform_risk_analysis(
        self,
        user_data: Dict[str, Any],
        assessment_type: str
    ) -> Dict[str, Any]:
        """Perform risk analysis on user data."""
        try:
            risk_factors = []
            overall_risk_score = 0.0

            # Analyze fraud alerts
            fraud_alerts = user_data.get("fraud_alerts", [])
            if fraud_alerts:
                high_severity_alerts = [alert for alert in fraud_alerts if alert.get("severity") in ["high", "critical"]]
                if high_severity_alerts:
                    risk_factors.append({
                        "type": "high_severity_fraud_alerts",
                        "description": f"Found {len(high_severity_alerts)} high severity fraud alerts",
                        "risk_score": 0.4
                    })
                    overall_risk_score += 0.4

            # Analyze behavioral patterns
            behavioral_patterns = user_data.get("behavioral_patterns", [])
            if behavioral_patterns:
                suspicious_patterns = [pattern for pattern in behavioral_patterns if pattern.get("confidence_score", 0) > 0.8]
                if suspicious_patterns:
                    risk_factors.append({
                        "type": "suspicious_behavioral_patterns",
                        "description": f"Found {len(suspicious_patterns)} high-confidence suspicious patterns",
                        "risk_score": 0.3
                    })
                    overall_risk_score += 0.3

            return {
                "overall_risk_score": min(overall_risk_score, 1.0),
                "risk_factors": risk_factors,
                "assessment_type": assessment_type
            }

        except Exception as e:
            logger.error(f"Failed to perform risk analysis: {str(e)}")
            raise

    # ==================== AI Model-Specific Methods ====================

    async def _get_recommendation_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get recommendation data for AI analysis."""
        try:
            # Get recommendations
            recommendations = await self.get_recommendations_by_user(user_id, include_expired=True)

            # Get user data
            user_data = await self._get_user_data_for_analysis(user_id, data_type, time_range)

            return {
                "recommendations": [rec.to_dict() for rec in recommendations],
                "user_data": user_data,
                "data_type": data_type,
                "time_range": time_range
            }

        except Exception as e:
            logger.error(f"Failed to get recommendation data for analysis: {str(e)}")
            raise

    async def _get_behavioral_pattern_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get behavioral pattern data for AI analysis."""
        try:
            # Get behavioral patterns
            patterns = await self.get_behavioral_patterns_by_user(user_id)

            # Get user data
            user_data = await self._get_user_data_for_analysis(user_id, data_type, time_range)

            return {
                "behavioral_patterns": [pattern.to_dict() for pattern in patterns],
                "user_data": user_data,
                "data_type": data_type,
                "time_range": time_range
            }

        except Exception as e:
            logger.error(f"Failed to get behavioral pattern data for analysis: {str(e)}")
            raise

    async def _calculate_ai_metrics(
        self,
        recommendations: List[AIRecommendation],
        behavioral_patterns: List[BehavioralPattern],
        fraud_alerts: List[FraudAlert]
    ) -> Dict[str, Any]:
        """Calculate AI metrics."""
        try:
            # Recommendation metrics
            total_recommendations = len(recommendations)
            active_recommendations = len([r for r in recommendations if r.is_active])
            accepted_recommendations = len([r for r in recommendations if r.status == RecommendationStatus.ACCEPTED])
            avg_confidence = sum(r.confidence_score or 0 for r in recommendations) / total_recommendations if total_recommendations > 0 else 0

            # Behavioral pattern metrics
            total_patterns = len(behavioral_patterns)
            active_patterns = len([p for p in behavioral_patterns if p.is_active])
            high_confidence_patterns = len([p for p in behavioral_patterns if p.confidence_score and p.confidence_score > 0.8])

            # Fraud alert metrics
            total_alerts = len(fraud_alerts)
            open_alerts = len([a for a in fraud_alerts if a.status == FraudAlertStatus.OPEN])
            high_severity_alerts = len([a for a in fraud_alerts if a.severity in [FraudAlertSeverity.HIGH, FraudAlertSeverity.CRITICAL]])

            return {
                "recommendation_metrics": {
                    "total_recommendations": total_recommendations,
                    "active_recommendations": active_recommendations,
                    "accepted_recommendations": accepted_recommendations,
                    "acceptance_rate": accepted_recommendations / total_recommendations if total_recommendations > 0 else 0,
                    "average_confidence": avg_confidence
                },
                "behavioral_metrics": {
                    "total_patterns": total_patterns,
                    "active_patterns": active_patterns,
                    "high_confidence_patterns": high_confidence_patterns,
                    "pattern_confidence_rate": high_confidence_patterns / total_patterns if total_patterns > 0 else 0
                },
                "fraud_metrics": {
                    "total_alerts": total_alerts,
                    "open_alerts": open_alerts,
                    "high_severity_alerts": high_severity_alerts,
                    "alert_resolution_rate": (total_alerts - open_alerts) / total_alerts if total_alerts > 0 else 0
                }
            }

        except Exception as e:
            logger.error(f"Failed to calculate AI metrics: {str(e)}")
            raise

    async def _analyze_patterns(
        self,
        recommendations: List[AIRecommendation],
        behavioral_patterns: List[BehavioralPattern],
        fraud_alerts: List[FraudAlert]
    ) -> Dict[str, Any]:
        """Analyze patterns across AI models."""
        try:
            # Analyze recommendation patterns
            recommendation_analysis = await self._analyze_recommendation_patterns(recommendations)

            # Analyze behavioral patterns
            behavioral_analysis = await self._analyze_behavioral_pattern_analysis(behavioral_patterns)

            # Analyze fraud patterns
            fraud_analysis = await self._analyze_fraud_patterns(fraud_alerts)

            return {
                "recommendation_analysis": recommendation_analysis,
                "behavioral_analysis": behavioral_analysis,
                "fraud_analysis": fraud_analysis
            }

        except Exception as e:
            logger.error(f"Failed to analyze patterns: {str(e)}")
            raise

    async def _analyze_recommendation_patterns(
        self,
        recommendations: List[AIRecommendation]
    ) -> Dict[str, Any]:
        """Analyze recommendation patterns."""
        try:
            if not recommendations:
                return {}

            # Group by recommendation type
            type_distribution = {}
            for recommendation in recommendations:
                rec_type = recommendation.recommendation_type.value
                type_distribution[rec_type] = type_distribution.get(rec_type, 0) + 1

            # Group by status
            status_distribution = {}
            for recommendation in recommendations:
                status = recommendation.status.value
                status_distribution[status] = status_distribution.get(status, 0) + 1

            # Calculate confidence distribution
            confidence_scores = [r.confidence_score or 0 for r in recommendations]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            return {
                "total_recommendations": len(recommendations),
                "type_distribution": type_distribution,
                "status_distribution": status_distribution,
                "average_confidence": avg_confidence,
                "high_confidence_recommendations": len([r for r in recommendations if r.confidence_score and r.confidence_score > 0.8])
            }

        except Exception as e:
            logger.error(f"Failed to analyze recommendation patterns: {str(e)}")
            raise

    async def _analyze_behavioral_pattern_analysis(
        self,
        patterns: List[BehavioralPattern]
    ) -> Dict[str, Any]:
        """Analyze behavioral pattern analysis."""
        try:
            if not patterns:
                return {}

            # Group by pattern type
            type_distribution = {}
            for pattern in patterns:
                pattern_type = pattern.pattern_type.value
                type_distribution[pattern_type] = type_distribution.get(pattern_type, 0) + 1

            # Calculate confidence distribution
            confidence_scores = [p.confidence_score or 0 for p in patterns]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            return {
                "total_patterns": len(patterns),
                "active_patterns": len([p for p in patterns if p.is_active]),
                "type_distribution": type_distribution,
                "average_confidence": avg_confidence,
                "high_confidence_patterns": len([p for p in patterns if p.confidence_score and p.confidence_score > 0.8])
            }

        except Exception as e:
            logger.error(f"Failed to analyze behavioral pattern analysis: {str(e)}")
            raise

    async def _analyze_fraud_patterns(
        self,
        alerts: List[FraudAlert]
    ) -> Dict[str, Any]:
        """Analyze fraud patterns."""
        try:
            if not alerts:
                return {}

            # Group by severity
            severity_distribution = {}
            for alert in alerts:
                severity = alert.severity.value
                severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

            # Group by status
            status_distribution = {}
            for alert in alerts:
                status = alert.status.value
                status_distribution[status] = status_distribution.get(status, 0) + 1

            return {
                "total_alerts": len(alerts),
                "open_alerts": len([a for a in alerts if a.status == FraudAlertStatus.OPEN]),
                "severity_distribution": severity_distribution,
                "status_distribution": status_distribution,
                "high_severity_alerts": len([a for a in alerts if a.severity in [FraudAlertSeverity.HIGH, FraudAlertSeverity.CRITICAL]])
            }

        except Exception as e:
            logger.error(f"Failed to analyze fraud patterns: {str(e)}")
            raise

    async def _calculate_recommendation_performance_metrics(
        self,
        analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate recommendation performance metrics."""
        try:
            ai_metrics = analytics.get("ai_metrics", {})
            recommendation_metrics = ai_metrics.get("recommendation_metrics", {})

            # Calculate performance indicators
            total_recommendations = recommendation_metrics.get("total_recommendations", 0)
            accepted_recommendations = recommendation_metrics.get("accepted_recommendations", 0)
            acceptance_rate = recommendation_metrics.get("acceptance_rate", 0)
            avg_confidence = recommendation_metrics.get("average_confidence", 0)

            # Performance score (0-100)
            performance_score = 0
            if acceptance_rate > 0.7:
                performance_score += 40  # High acceptance rate
            if avg_confidence > 0.8:
                performance_score += 30  # High confidence
            if total_recommendations > 10:
                performance_score += 30  # Good recommendation volume

            return {
                "performance_score": min(performance_score, 100),
                "acceptance_health": "high" if acceptance_rate > 0.7 else "medium" if acceptance_rate > 0.5 else "low",
                "confidence_health": "high" if avg_confidence > 0.8 else "medium" if avg_confidence > 0.6 else "low",
                "volume_health": "high" if total_recommendations > 20 else "medium" if total_recommendations > 10 else "low"
            }

        except Exception as e:
            logger.error(f"Failed to calculate recommendation performance metrics: {str(e)}")
            raise

    async def _calculate_behavioral_metrics(
        self,
        patterns: List[BehavioralPattern]
    ) -> Dict[str, Any]:
        """Calculate behavioral metrics."""
        try:
            if not patterns:
                return {}

            total_patterns = len(patterns)
            active_patterns = len([p for p in patterns if p.is_active])
            confidence_scores = [p.confidence_score or 0 for p in patterns]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            # Group by pattern type
            type_distribution = {}
            for pattern in patterns:
                pattern_type = pattern.pattern_type.value
                type_distribution[pattern_type] = type_distribution.get(pattern_type, 0) + 1

            return {
                "total_patterns": total_patterns,
                "active_patterns": active_patterns,
                "average_confidence": avg_confidence,
                "high_confidence_patterns": len([p for p in patterns if p.confidence_score and p.confidence_score > 0.8]),
                "type_distribution": type_distribution,
                "pattern_activity_rate": active_patterns / total_patterns if total_patterns > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to calculate behavioral metrics: {str(e)}")
            raise

    async def _calculate_ai_risk_indicators(self, user_id: int) -> Dict[str, Any]:
        """Calculate AI risk indicators for user."""
        try:
            # Get fraud alerts
            fraud_alerts = await self.get_fraud_alerts_by_user(user_id)
            high_severity_alerts = [alert for alert in fraud_alerts if alert.severity in [FraudAlertSeverity.HIGH, FraudAlertSeverity.CRITICAL]]

            # Get behavioral patterns
            behavioral_patterns = await self.get_behavioral_patterns_by_user(user_id)
            suspicious_patterns = [pattern for pattern in behavioral_patterns if pattern.confidence_score and pattern.confidence_score > 0.8]

            return {
                "high_severity_fraud_alerts": len(high_severity_alerts),
                "suspicious_behavioral_patterns": len(suspicious_patterns),
                "total_risk_indicators": len(high_severity_alerts) + len(suspicious_patterns)
            }

        except Exception as e:
            logger.error(f"Failed to calculate AI risk indicators: {str(e)}")
            raise

    async def _generate_behavioral_insights(
        self,
        patterns: List[BehavioralPattern],
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate behavioral insights."""
        try:
            insights = []

            total_patterns = metrics.get("total_patterns", 0)
            high_confidence_patterns = metrics.get("high_confidence_patterns", 0)
            activity_rate = metrics.get("pattern_activity_rate", 0)

            if high_confidence_patterns > total_patterns * 0.7:
                insights.append("Strong behavioral patterns detected with high confidence")
            elif high_confidence_patterns < total_patterns * 0.3:
                insights.append("Limited high-confidence behavioral patterns detected")

            if activity_rate > 0.8:
                insights.append("High pattern activity indicates consistent behavior")
            elif activity_rate < 0.3:
                insights.append("Low pattern activity suggests changing behavior patterns")

            return insights

        except Exception as e:
            logger.error(f"Failed to generate behavioral insights: {str(e)}")
            return [] 