"""
Enhanced behavioral pattern repository with AI integration for customer behavior analysis.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, select, func, text, desc
from sqlalchemy.orm import selectinload

from app.models.behavioral_pattern import BehavioralPattern, BehavioralPatternType
from app.schemas.behavioral import BehavioralPatternCreate, BehavioralPatternUpdate
from app.repositories.enhanced_base import AIEnhancedRepository
from app.core.llm_orchestrator import TaskType, TaskComplexity
from app.core.exceptions import BehavioralAnalysisError, PatternDetectionError

logger = logging.getLogger(__name__)


class EnhancedBehavioralPatternRepository(AIEnhancedRepository[BehavioralPattern, BehavioralPatternCreate, BehavioralPatternUpdate]):
    """
    Enhanced behavioral pattern repository with AI-powered behavior analysis and pattern detection.
    
    Features:
    - AI-powered behavioral pattern detection
    - Spending habit analysis and insights
    - Risk behavior identification
    - Seasonal pattern analysis
    - Behavioral bias detection
    - Pattern-based recommendations
    """

    async def get_patterns_by_user(
        self,
        user_id: int,
        *,
        pattern_type: Optional[BehavioralPatternType] = None,
        include_expired: bool = False,
        use_cache: bool = True
    ) -> List[BehavioralPattern]:
        """Get behavioral patterns for a specific user with optional filtering."""
        cache_key = f"user_behavioral_patterns:{user_id}:{pattern_type}:{include_expired}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(BehavioralPattern).where(BehavioralPattern.user_id == user_id)

        if pattern_type:
            query = query.where(BehavioralPattern.pattern_type == pattern_type)

        if not include_expired:
            query = query.where(BehavioralPattern.next_analysis_date >= date.today())

        query = query.order_by(desc(BehavioralPattern.confidence_score))

        result = await self.db_session.execute(query)
        patterns = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, patterns, ttl=3600)  # 1 hour

        return patterns

    async def analyze_behavioral_patterns(
        self,
        user_id: int,
        time_range: str = "90d",
        pattern_types: Optional[List[BehavioralPatternType]] = None
    ) -> Dict[str, Any]:
        """Analyze behavioral patterns for a user using AI."""
        try:
            # Get user's transaction data
            transaction_data = await self._get_user_transaction_data(user_id, time_range)

            # Get existing patterns
            existing_patterns = await self.get_patterns_by_user(user_id, include_expired=True)

            # Analyze patterns with AI
            pattern_data = {
                "user_id": user_id,
                "time_range": time_range,
                "transactions": transaction_data,
                "existing_patterns": [pattern.to_dict() for pattern in existing_patterns],
                "pattern_types": pattern_types
            }

            analysis_result = await self.analyze_with_ai(
                pattern_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.HIGH
            )

            # Cache the analysis
            cache_key = f"behavioral_pattern_analysis:{user_id}:{time_range}"
            await self.cache_manager.set(cache_key, analysis_result, ttl=7200)  # 2 hours

            return analysis_result

        except Exception as e:
            logger.error(f"Behavioral pattern analysis failed: {str(e)}")
            raise BehavioralAnalysisError(f"Behavioral pattern analysis failed: {str(e)}")

    async def detect_spending_patterns(
        self,
        user_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Detect spending patterns for a user."""
        try:
            # Get user's transaction data
            transaction_data = await self._get_user_transaction_data(user_id, time_range)

            # Analyze spending patterns with AI
            spending_analysis = await self.analyze_with_ai(
                {"transactions": transaction_data, "user_id": user_id, "time_range": time_range},
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            # Create or update behavioral pattern
            pattern_data = {
                "user_id": user_id,
                "pattern_type": BehavioralPatternType.SPENDING_HABIT,
                "analysis_period_start": datetime.utcnow().date() - timedelta(days=int(time_range[:-1])),
                "analysis_period_end": datetime.utcnow().date(),
                "spending_categories": spending_analysis.get("category_breakdown", {}),
                "monthly_average_spending": spending_analysis.get("monthly_average", 0.0),
                "spending_volatility": spending_analysis.get("volatility", 0.0),
                "spending_trends": spending_analysis.get("trends", {}),
                "ai_insights": spending_analysis.get("insights", {}),
                "recommendations": spending_analysis.get("recommendations", []),
                "confidence_score": spending_analysis.get("confidence_score", 0.5),
                "next_analysis_date": datetime.utcnow().date() + timedelta(days=30)
            }

            # Check if pattern already exists
            existing_patterns = await self.get_patterns_by_user(
                user_id, 
                pattern_type=BehavioralPatternType.SPENDING_HABIT
            )

            if existing_patterns:
                # Update existing pattern
                pattern = existing_patterns[0]
                updated_pattern = await self.update(pattern, pattern_data)
                return updated_pattern.to_dict()
            else:
                # Create new pattern
                new_pattern = await self.create(pattern_data)
                return new_pattern.to_dict()

        except Exception as e:
            logger.error(f"Spending pattern detection failed: {str(e)}")
            raise PatternDetectionError(f"Spending pattern detection failed: {str(e)}")

    async def detect_risk_patterns(
        self,
        user_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Detect risk-related behavioral patterns."""
        try:
            # Get user's transaction and activity data
            transaction_data = await self._get_user_transaction_data(user_id, time_range)
            risk_data = await self._get_user_risk_data(user_id, time_range)

            # Analyze risk patterns with AI
            risk_analysis = await self.analyze_with_ai(
                {
                    "transactions": transaction_data,
                    "risk_data": risk_data,
                    "user_id": user_id,
                    "time_range": time_range
                },
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            # Create or update risk pattern
            pattern_data = {
                "user_id": user_id,
                "pattern_type": BehavioralPatternType.RISK_BEHAVIOR,
                "analysis_period_start": datetime.utcnow().date() - timedelta(days=int(time_range[:-1])),
                "analysis_period_end": datetime.utcnow().date(),
                "risk_indicators": risk_analysis.get("risk_indicators", {}),
                "behavioral_biases": risk_analysis.get("behavioral_biases", {}),
                "unusual_patterns": risk_analysis.get("unusual_patterns", {}),
                "ai_insights": risk_analysis.get("insights", {}),
                "recommendations": risk_analysis.get("recommendations", []),
                "confidence_score": risk_analysis.get("confidence_score", 0.5),
                "next_analysis_date": datetime.utcnow().date() + timedelta(days=30)
            }

            # Check if pattern already exists
            existing_patterns = await self.get_patterns_by_user(
                user_id, 
                pattern_type=BehavioralPatternType.RISK_BEHAVIOR
            )

            if existing_patterns:
                # Update existing pattern
                pattern = existing_patterns[0]
                updated_pattern = await self.update(pattern, pattern_data)
                return updated_pattern.to_dict()
            else:
                # Create new pattern
                new_pattern = await self.create(pattern_data)
                return new_pattern.to_dict()

        except Exception as e:
            logger.error(f"Risk pattern detection failed: {str(e)}")
            raise PatternDetectionError(f"Risk pattern detection failed: {str(e)}")

    async def analyze_seasonal_patterns(
        self,
        user_id: int,
        time_range: str = "365d"
    ) -> Dict[str, Any]:
        """Analyze seasonal behavioral patterns."""
        try:
            # Get user's transaction data for a longer period
            transaction_data = await self._get_user_transaction_data(user_id, time_range)

            # Analyze seasonal patterns with AI
            seasonal_analysis = await self.analyze_with_ai(
                {
                    "transactions": transaction_data,
                    "user_id": user_id,
                    "time_range": time_range,
                    "analysis_type": "seasonal"
                },
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.HIGH
            )

            # Create or update seasonal pattern
            pattern_data = {
                "user_id": user_id,
                "pattern_type": BehavioralPatternType.TRANSACTION_TIMING,
                "analysis_period_start": datetime.utcnow().date() - timedelta(days=int(time_range[:-1])),
                "analysis_period_end": datetime.utcnow().date(),
                "seasonal_patterns": seasonal_analysis.get("seasonal_patterns", {}),
                "spending_trends": seasonal_analysis.get("trends", {}),
                "ai_insights": seasonal_analysis.get("insights", {}),
                "recommendations": seasonal_analysis.get("recommendations", []),
                "confidence_score": seasonal_analysis.get("confidence_score", 0.5),
                "next_analysis_date": datetime.utcnow().date() + timedelta(days=90)  # Longer interval for seasonal
            }

            # Check if pattern already exists
            existing_patterns = await self.get_patterns_by_user(
                user_id, 
                pattern_type=BehavioralPatternType.TRANSACTION_TIMING
            )

            if existing_patterns:
                # Update existing pattern
                pattern = existing_patterns[0]
                updated_pattern = await self.update(pattern, pattern_data)
                return updated_pattern.to_dict()
            else:
                # Create new pattern
                new_pattern = await self.create(pattern_data)
                return new_pattern.to_dict()

        except Exception as e:
            logger.error(f"Seasonal pattern analysis failed: {str(e)}")
            raise BehavioralAnalysisError(f"Seasonal pattern analysis failed: {str(e)}")

    async def detect_behavioral_biases(
        self,
        user_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Detect cognitive and behavioral biases in user behavior."""
        try:
            # Get user's transaction and decision data
            transaction_data = await self._get_user_transaction_data(user_id, time_range)
            decision_data = await self._get_user_decision_data(user_id, time_range)

            # Analyze behavioral biases with AI
            bias_analysis = await self.analyze_with_ai(
                {
                    "transactions": transaction_data,
                    "decisions": decision_data,
                    "user_id": user_id,
                    "time_range": time_range,
                    "analysis_type": "behavioral_biases"
                },
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.HIGH
            )

            return bias_analysis

        except Exception as e:
            logger.error(f"Behavioral bias detection failed: {str(e)}")
            raise BehavioralAnalysisError(f"Behavioral bias detection failed: {str(e)}")

    async def get_pattern_insights(
        self,
        user_id: int,
        pattern_type: Optional[BehavioralPatternType] = None
    ) -> Dict[str, Any]:
        """Get AI-generated insights from behavioral patterns."""
        try:
            # Get user's patterns
            patterns = await self.get_patterns_by_user(user_id, pattern_type=pattern_type)

            if not patterns:
                return {"insights": [], "recommendations": [], "error": "No patterns found"}

            # Analyze patterns for insights
            pattern_data = {
                "patterns": [pattern.to_dict() for pattern in patterns],
                "user_id": user_id,
                "pattern_type": pattern_type
            }

            insights_analysis = await self.analyze_with_ai(
                pattern_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return insights_analysis

        except Exception as e:
            logger.error(f"Pattern insights analysis failed: {str(e)}")
            raise BehavioralAnalysisError(f"Pattern insights analysis failed: {str(e)}")

    async def get_pattern_trends(
        self,
        time_range: str = "90d",
        pattern_type: Optional[BehavioralPatternType] = None
    ) -> Dict[str, Any]:
        """Get behavioral pattern trends across users."""
        try:
            # Get patterns for the time range
            start_date = datetime.utcnow() - timedelta(days=int(time_range[:-1]))
            
            query = select(BehavioralPattern).where(BehavioralPattern.created_at >= start_date)
            
            if pattern_type:
                query = query.where(BehavioralPattern.pattern_type == pattern_type)

            result = await self.db_session.execute(query)
            patterns = result.scalars().all()

            # Analyze trends with AI
            trend_data = {
                "patterns": [pattern.to_dict() for pattern in patterns],
                "time_range": time_range,
                "pattern_type": pattern_type,
                "total_patterns": len(patterns),
                "type_distribution": await self._calculate_type_distribution(patterns)
            }

            trend_analysis = await self.analyze_with_ai(
                trend_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return trend_analysis

        except Exception as e:
            logger.error(f"Pattern trend analysis failed: {str(e)}")
            raise BehavioralAnalysisError(f"Pattern trend analysis failed: {str(e)}")

    async def bulk_update_pattern_analysis(
        self,
        user_ids: List[int],
        pattern_type: BehavioralPatternType,
        time_range: str = "90d"
    ) -> int:
        """Bulk update pattern analysis for multiple users."""
        try:
            updated_count = 0

            for user_id in user_ids:
                try:
                    if pattern_type == BehavioralPatternType.SPENDING_HABIT:
                        await self.detect_spending_patterns(user_id, time_range)
                    elif pattern_type == BehavioralPatternType.RISK_BEHAVIOR:
                        await self.detect_risk_patterns(user_id, time_range)
                    elif pattern_type == BehavioralPatternType.TRANSACTION_TIMING:
                        await self.analyze_seasonal_patterns(user_id, time_range)
                    
                    updated_count += 1

                except Exception as e:
                    logger.error(f"Failed to update pattern for user {user_id}: {str(e)}")
                    continue

            logger.info(f"Bulk updated {updated_count} pattern analyses")
            return updated_count

        except Exception as e:
            logger.error(f"Bulk pattern analysis update failed: {str(e)}")
            raise BehavioralAnalysisError(f"Bulk pattern analysis update failed: {str(e)}")

    async def get_high_confidence_patterns(
        self,
        confidence_threshold: float = 0.8,
        pattern_type: Optional[BehavioralPatternType] = None
    ) -> List[BehavioralPattern]:
        """Get patterns with high confidence scores."""
        try:
            query = select(BehavioralPattern).where(
                BehavioralPattern.confidence_score >= confidence_threshold
            )

            if pattern_type:
                query = query.where(BehavioralPattern.pattern_type == pattern_type)

            query = query.order_by(desc(BehavioralPattern.confidence_score))

            result = await self.db_session.execute(query)
            high_confidence_patterns = result.scalars().all()

            return high_confidence_patterns

        except Exception as e:
            logger.error(f"Failed to get high-confidence patterns: {str(e)}")
            raise BehavioralAnalysisError(f"Failed to get high-confidence patterns: {str(e)}")

    # ==================== Abstract Method Implementations ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for behavioral analysis."""
        try:
            # Get user's behavioral patterns
            patterns = await self.get_patterns_by_user(user_id, include_expired=True)
            
            # Get user's transaction data
            transaction_data = await self._get_user_transaction_data(user_id, time_range or "90d")

            return {
                "user_id": user_id,
                "data_type": data_type,
                "time_range": time_range,
                "behavioral_patterns": [pattern.to_dict() for pattern in patterns],
                "transactions": transaction_data,
                "total_patterns": len(patterns),
                "pattern_types": list(set([p.pattern_type.value for p in patterns if p.pattern_type]))
            }

        except Exception as e:
            logger.error(f"Failed to get user data for analysis: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _get_user_transactions(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user's transaction data for behavioral analysis."""
        try:
            # This would typically query the transaction repository
            # For now, return mock data
            return [
                {
                    "id": "1",
                    "amount": 100.0,
                    "category": "groceries",
                    "timestamp": datetime.utcnow(),
                    "location": "New York",
                    "status": "completed"
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get user transactions: {str(e)}")
            return []

    async def _get_user_risk_data(
        self,
        user_id: int,
        time_range: str
    ) -> Dict[str, Any]:
        """Get user's risk data for behavioral analysis."""
        try:
            # This would typically query risk-related data
            # For now, return mock data
            return {
                "risk_score": 0.3,
                "risk_factors": ["high_transaction_frequency", "multiple_locations"],
                "fraud_alerts": 2,
                "suspicious_activities": 1
            }

        except Exception as e:
            logger.error(f"Failed to get user risk data: {str(e)}")
            return {"error": str(e)}

    async def _get_user_decision_data(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user's decision data for behavioral bias analysis."""
        try:
            # This would typically query decision-related data
            # For now, return mock data
            return [
                {
                    "decision_type": "product_selection",
                    "choice": "premium_card",
                    "timestamp": datetime.utcnow(),
                    "context": "card_upgrade_offer"
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get user decision data: {str(e)}")
            return []

    async def _get_user_risk_data(self, user_id: int) -> Dict[str, Any]:
        """Get user's behavioral risk data."""
        try:
            # Get user's behavioral patterns
            patterns = await self.get_patterns_by_user(user_id, include_expired=True)
            
            # Calculate risk metrics
            total_patterns = len(patterns)
            risk_patterns = len([p for p in patterns if p.pattern_type == BehavioralPatternType.RISK_BEHAVIOR])
            high_confidence_patterns = len([p for p in patterns if p.confidence_score >= 0.8])

            # Calculate average confidence score
            confidence_scores = [p.confidence_score for p in patterns if p.confidence_score is not None]
            avg_confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

            return {
                "user_id": user_id,
                "total_patterns": total_patterns,
                "risk_patterns": risk_patterns,
                "high_confidence_patterns": high_confidence_patterns,
                "average_confidence_score": avg_confidence_score,
                "patterns": [pattern.to_dict() for pattern in patterns]
            }

        except Exception as e:
            logger.error(f"Failed to get user risk data: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _analyze_spending_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze spending patterns for behavioral analysis."""
        try:
            if not transactions:
                return {"patterns": [], "insights": [], "recommendations": []}

            # Calculate basic metrics
            total_amount = sum(t.get("amount", 0) for t in transactions)
            transaction_count = len(transactions)
            
            # Group by category and time
            category_patterns = {}
            temporal_patterns = {}
            
            for transaction in transactions:
                category = transaction.get("category", "unknown")
                amount = transaction.get("amount", 0)
                timestamp = transaction.get("timestamp")
                
                category_patterns[category] = category_patterns.get(category, 0) + amount
                
                if timestamp:
                    hour = timestamp.hour
                    temporal_patterns[hour] = temporal_patterns.get(hour, 0) + 1

            # Find behavioral insights
            insights = []
            
            # Check for spending concentration
            if len(category_patterns) < 5:
                insights.append("Concentrated spending in few categories")
            
            # Check for temporal patterns
            peak_hours = sorted(temporal_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
            if peak_hours:
                insights.append(f"Peak spending hours: {peak_hours}")

            return {
                "patterns": {
                    "total_amount": total_amount,
                    "transaction_count": transaction_count,
                    "category_patterns": category_patterns,
                    "temporal_patterns": temporal_patterns
                },
                "insights": insights,
                "recommendations": [
                    "Consider diversifying spending categories",
                    "Monitor peak spending times"
                ]
            }

        except Exception as e:
            logger.error(f"Failed to analyze spending patterns: {str(e)}")
            return {"patterns": [], "insights": [], "recommendations": [], "error": str(e)}

    async def _analyze_temporal_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns for behavioral analysis."""
        try:
            if not transactions:
                return {"temporal_patterns": [], "seasonal_insights": []}

            # Group by hour, day, and month
            hourly_patterns = {}
            daily_patterns = {}
            monthly_patterns = {}
            
            for transaction in transactions:
                timestamp = transaction.get("timestamp")
                if timestamp:
                    hour = timestamp.hour
                    day = timestamp.strftime("%A")
                    month = timestamp.strftime("%B")
                    
                    hourly_patterns[hour] = hourly_patterns.get(hour, 0) + 1
                    daily_patterns[day] = daily_patterns.get(day, 0) + 1
                    monthly_patterns[month] = monthly_patterns.get(month, 0) + 1

            # Find seasonal insights
            seasonal_insights = []
            
            # Check for weekly patterns
            if daily_patterns:
                peak_day = max(daily_patterns.items(), key=lambda x: x[1])
                seasonal_insights.append(f"Peak spending day: {peak_day[0]}")

            # Check for monthly patterns
            if monthly_patterns:
                peak_month = max(monthly_patterns.items(), key=lambda x: x[1])
                seasonal_insights.append(f"Peak spending month: {peak_month[0]}")

            return {
                "temporal_patterns": {
                    "hourly_distribution": hourly_patterns,
                    "daily_distribution": daily_patterns,
                    "monthly_distribution": monthly_patterns
                },
                "seasonal_insights": seasonal_insights
            }

        except Exception as e:
            logger.error(f"Failed to analyze temporal patterns: {str(e)}")
            return {"temporal_patterns": [], "seasonal_insights": [], "error": str(e)}

    async def _analyze_geographic_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze geographic patterns for behavioral analysis."""
        try:
            if not transactions:
                return {"geographic_patterns": [], "location_insights": []}

            # Group by location
            location_patterns = {}
            
            for transaction in transactions:
                location = transaction.get("location", "unknown")
                amount = transaction.get("amount", 0)
                location_patterns[location] = location_patterns.get(location, 0) + amount

            # Find location insights
            location_insights = []
            
            # Check for location diversity
            if len(location_patterns) > 10:
                location_insights.append("High location diversity in spending")
            elif len(location_patterns) < 3:
                location_insights.append("Concentrated spending in few locations")

            # Check for unusual locations
            unusual_locations = [loc for loc in location_patterns.keys() if "unknown" in loc.lower()]
            if unusual_locations:
                location_insights.append("Unusual spending locations detected")

            return {
                "geographic_patterns": {
                    "location_breakdown": location_patterns,
                    "total_locations": len(location_patterns),
                    "unusual_locations": unusual_locations
                },
                "location_insights": location_insights
            }

        except Exception as e:
            logger.error(f"Failed to analyze geographic patterns: {str(e)}")
            return {"geographic_patterns": [], "location_insights": [], "error": str(e)}

    async def _perform_risk_analysis(
        self,
        user_data: Dict[str, Any],
        assessment_type: str
    ) -> Dict[str, Any]:
        """Perform risk analysis for behavioral data."""
        try:
            patterns = user_data.get("behavioral_patterns", [])
            
            # Calculate risk metrics
            total_patterns = len(patterns)
            risk_patterns = len([p for p in patterns if p.get("pattern_type") == "risk_behavior"])
            high_confidence_patterns = len([p for p in patterns if p.get("confidence_score", 0) >= 0.8])

            # Calculate risk score
            risk_score = 0.0
            risk_factors = []

            if risk_patterns > 0:
                risk_score += 0.4
                risk_factors.append("Risk behavior patterns detected")

            if high_confidence_patterns < total_patterns * 0.5:
                risk_score += 0.2
                risk_factors.append("Low confidence in behavioral patterns")

            if total_patterns > 10:
                risk_score += 0.1
                risk_factors.append("Complex behavioral patterns")

            # Normalize risk score
            risk_score = min(risk_score, 1.0)

            return {
                "overall_risk_score": risk_score,
                "risk_factors": risk_factors,
                "behavioral_metrics": {
                    "total_patterns": total_patterns,
                    "risk_patterns": risk_patterns,
                    "high_confidence_patterns": high_confidence_patterns
                }
            }

        except Exception as e:
            logger.error(f"Failed to perform risk analysis: {str(e)}")
            return {"overall_risk_score": 0.0, "risk_factors": [], "error": str(e)}

    # ==================== Helper Methods ====================

    async def _calculate_type_distribution(
        self,
        patterns: List[BehavioralPattern]
    ) -> Dict[str, int]:
        """Calculate pattern type distribution."""
        try:
            distribution = {}

            for pattern in patterns:
                pattern_type = pattern.pattern_type.value if pattern.pattern_type else "unknown"
                distribution[pattern_type] = distribution.get(pattern_type, 0) + 1

            return distribution

        except Exception as e:
            logger.error(f"Failed to calculate type distribution: {str(e)}")
            return {} 