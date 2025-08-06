"""
Enhanced AI recommendation repository with AI integration for personalized banking recommendations.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, or_, select, func, text, desc
from sqlalchemy.orm import selectinload

from app.models.ai_recommendation import AIRecommendation, RecommendationType, RecommendationStatus, RecommendationPriority
from app.schemas.ai import AIRecommendationCreate, AIRecommendationUpdate
from app.repositories.enhanced_base import AIEnhancedRepository
from app.core.llm_orchestrator import TaskType, TaskComplexity

logger = logging.getLogger(__name__)


class EnhancedAIRecommendationRepository(AIEnhancedRepository[AIRecommendation, AIRecommendationCreate, AIRecommendationUpdate]):
    """
    Enhanced AI recommendation repository with AI-powered personalization and recommendation generation.
    
    Features:
    - AI-powered recommendation generation
    - Personalized recommendation engine
    - Recommendation performance analysis
    - User feedback analysis and learning
    - Recommendation optimization and A/B testing
    """

    async def get_recommendations_by_user(
        self,
        user_id: int,
        *,
        status: Optional[RecommendationStatus] = None,
        recommendation_type: Optional[RecommendationType] = None,
        priority: Optional[RecommendationPriority] = None,
        include_expired: bool = False,
        use_cache: bool = True
    ) -> List[AIRecommendation]:
        """Get AI recommendations for a specific user with optional filtering."""
        cache_key = f"user_recommendations:{user_id}:{status}:{recommendation_type}:{priority}:{include_expired}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(AIRecommendation).where(AIRecommendation.user_id == user_id)

        if status:
            query = query.where(AIRecommendation.status == status)

        if recommendation_type:
            query = query.where(AIRecommendation.recommendation_type == recommendation_type)

        if priority:
            query = query.where(AIRecommendation.priority == priority)

        if not include_expired:
            query = query.where(
                or_(
                    AIRecommendation.expiry_date.is_(None),
                    AIRecommendation.expiry_date >= date.today()
                )
            )

        query = query.order_by(desc(AIRecommendation.confidence_score))

        result = await self.db_session.execute(query)
        recommendations = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, recommendations, ttl=1800)  # 30 minutes

        return recommendations

    async def generate_personalized_recommendations(
        self,
        user_id: int,
        recommendation_types: Optional[List[RecommendationType]] = None,
        max_recommendations: int = 5
    ) -> List[AIRecommendation]:
        """Generate personalized recommendations for a user using AI."""
        try:
            # Get user data for analysis
            user_data = await self._get_user_recommendation_data(user_id)

            # Generate recommendations with AI
            recommendation_data = await self.analyze_with_ai(
                user_data,
                TaskType.FINANCIAL_RECOMMENDATION,
                TaskComplexity.HIGH
            )

            # Create recommendations based on AI analysis
            recommendations = []
            for rec_data in recommendation_data.get("recommendations", [])[:max_recommendations]:
                recommendation = await self.create({
                    "user_id": user_id,
                    "recommendation_type": rec_data.get("type", RecommendationType.PRODUCT),
                    "title": rec_data.get("title", "Personalized Recommendation"),
                    "description": rec_data.get("description", ""),
                    "reasoning": rec_data.get("reasoning", ""),
                    "confidence_score": rec_data.get("confidence_score", 0.5),
                    "priority": rec_data.get("priority", RecommendationPriority.MEDIUM),
                    "estimated_benefit": rec_data.get("estimated_benefit", ""),
                    "estimated_monetary_value": rec_data.get("estimated_monetary_value"),
                    "call_to_action": rec_data.get("call_to_action", ""),
                    "expiry_date": date.today() + timedelta(days=30)  # 30 days expiry
                })
                recommendations.append(recommendation)

            # Cache the recommendations
            cache_key = f"personalized_recommendations:{user_id}"
            await self.cache_manager.set(cache_key, recommendations, ttl=3600)  # 1 hour

            return recommendations

        except Exception as e:
            logger.error(f"Personalized recommendation generation failed: {str(e)}")
            logger.error(f"Error: {{f"Personalized recommendation generation failed: {str(e}}")
        return {}

    async def analyze_recommendation_performance(
        self,
        user_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Analyze recommendation performance for a user."""
        try:
            # Get user's recommendations
            recommendations = await self.get_recommendations_by_user(
                user_id, 
                time_range=time_range,
                include_expired=True
            )

            # Calculate performance metrics
            total_recommendations = len(recommendations)
            accepted_recommendations = len([r for r in recommendations if r.status == RecommendationStatus.ACCEPTED])
            declined_recommendations = len([r for r in recommendations if r.status == RecommendationStatus.DECLINED])
            implemented_recommendations = len([r for r in recommendations if r.status == RecommendationStatus.IMPLEMENTED])

            # Calculate average feedback rating
            feedback_ratings = [r.feedback_rating for r in recommendations if r.feedback_rating is not None]
            avg_feedback_rating = sum(feedback_ratings) / len(feedback_ratings) if feedback_ratings else 0.0

            # Analyze with AI
            performance_data = {
                "recommendations": [rec.to_dict() for rec in recommendations],
                "metrics": {
                    "total_recommendations": total_recommendations,
                    "accepted_recommendations": accepted_recommendations,
                    "declined_recommendations": declined_recommendations,
                    "implemented_recommendations": implemented_recommendations,
                    "acceptance_rate": (accepted_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0.0,
                    "average_feedback_rating": avg_feedback_rating
                }
            }

            analysis_result = await self.analyze_with_ai(
                performance_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Recommendation performance analysis failed: {str(e)}")
            logger.error(f"Error: {{f"Recommendation performance analysis failed: {str(e}}")
        return None

    async def optimize_recommendations(
        self,
        user_id: int,
        optimization_type: str = "performance"
    ) -> Dict[str, Any]:
        """Optimize recommendations based on user behavior and feedback."""
        try:
            # Get user's recommendation history
            user_data = await self._get_user_recommendation_data(user_id)

            # Analyze optimization opportunities
            optimization_data = {
                "user_data": user_data,
                "optimization_type": optimization_type,
                "current_performance": await self.analyze_recommendation_performance(user_id)
            }

            # Get optimization suggestions from AI
            optimization_result = await self.analyze_with_ai(
                optimization_data,
                TaskType.FINANCIAL_RECOMMENDATION,
                TaskComplexity.HIGH
            )

            return optimization_result

        except Exception as e:
            logger.error(f"Recommendation optimization failed: {str(e)}")
            logger.error(f"Error: {{f"Recommendation optimization failed: {str(e}}")
        return None

    async def analyze_user_preferences(
        self,
        user_id: int,
        time_range: str = "180d"
    ) -> Dict[str, Any]:
        """Analyze user preferences based on recommendation interactions."""
        try:
            # Get user's recommendation history
            recommendations = await self.get_recommendations_by_user(
                user_id,
                time_range=time_range,
                include_expired=True
            )

            # Analyze preferences with AI
            preference_data = {
                "recommendations": [rec.to_dict() for rec in recommendations],
                "user_id": user_id,
                "time_range": time_range
            }

            preference_analysis = await self.analyze_with_ai(
                preference_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            # Cache the analysis
            cache_key = f"user_preferences:{user_id}:{time_range}"
            await self.cache_manager.set(cache_key, preference_analysis, ttl=7200)  # 2 hours

            return preference_analysis

        except Exception as e:
            logger.error(f"User preference analysis failed: {str(e)}")
            logger.error(f"Error: {{f"User preference analysis failed: {str(e}}")
        return None

    async def get_recommendation_trends(
        self,
        time_range: str = "90d",
        recommendation_type: Optional[RecommendationType] = None
    ) -> Dict[str, Any]:
        """Get recommendation trends and statistics."""
        try:
            # Get recommendations for the time range
            start_date = datetime.utcnow() - timedelta(days=int(time_range[:-1]))
            
            query = select(AIRecommendation).where(AIRecommendation.created_at >= start_date)
            
            if recommendation_type:
                query = query.where(AIRecommendation.recommendation_type == recommendation_type)

            result = await self.db_session.execute(query)
            recommendations = result.scalars().all()

            # Analyze trends with AI
            trend_data = {
                "recommendations": [rec.to_dict() for rec in recommendations],
                "time_range": time_range,
                "recommendation_type": recommendation_type,
                "total_recommendations": len(recommendations),
                "type_distribution": await self._calculate_type_distribution(recommendations),
                "status_distribution": await self._calculate_status_distribution(recommendations)
            }

            trend_analysis = await self.analyze_with_ai(
                trend_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return trend_analysis

        except Exception as e:
            logger.error(f"Recommendation trend analysis failed: {str(e)}")
            logger.error(f"Error: {{f"Recommendation trend analysis failed: {str(e}}")
        return None

    async def update_recommendation_feedback(
        self,
        recommendation_id: Union[int, str, UUID],
        feedback: str,
        rating: int,
        status: Optional[RecommendationStatus] = None
    ) -> AIRecommendation:
        """Update recommendation with user feedback."""
        try:
            recommendation = await self.get_by_id(recommendation_id)
            if not recommendation:
                logger.error(f"Error: {{f"Recommendation {recommendation_id} not found"}}")
        return None

            # Update feedback
            update_data = {
                "user_feedback": feedback,
                "feedback_rating": rating,
                "feedback_timestamp": datetime.utcnow()
            }

            if status:
                update_data["status"] = status

            updated_recommendation = await self.update(recommendation, update_data)

            # Analyze feedback for learning
            await self._analyze_feedback_for_learning(recommendation_id, feedback, rating)

            return updated_recommendation

        except Exception as e:
            logger.error(f"Recommendation feedback update failed: {str(e)}")
            logger.error(f"Error: {{f"Recommendation feedback update failed: {str(e}}")
        return None

    async def get_high_priority_recommendations(
        self,
        user_id: int,
        priority: RecommendationPriority = RecommendationPriority.HIGH
    ) -> List[AIRecommendation]:
        """Get high-priority recommendations for a user."""
        try:
            recommendations = await self.get_recommendations_by_user(
                user_id,
                priority=priority,
                status=RecommendationStatus.ACTIVE
            )

            # Sort by confidence score
            recommendations.sort(key=lambda x: x.confidence_score, reverse=True)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get high-priority recommendations: {str(e)}")
            logger.error(f"Error: {{f"Failed to get high-priority recommendations: {str(e}}")
        return None

    async def bulk_update_recommendation_status(
        self,
        recommendation_ids: List[Union[int, str, UUID]],
        new_status: RecommendationStatus,
        reason: Optional[str] = None
    ) -> int:
        """Bulk update recommendation status."""
        try:
            update_data = {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }

            if reason:
                update_data["user_feedback"] = reason

            # Update recommendations
            updated_count = await self.bulk_update(
                {"recommendation_id": {"$in": recommendation_ids}},
                update_data
            )

            # Invalidate related caches
            await self._invalidate_recommendation_caches(recommendation_ids)

            logger.info(f"Bulk updated {updated_count} recommendations to status {new_status}")
            return updated_count

        except Exception as e:
            logger.error(f"Bulk recommendation status update failed: {str(e)}")
            logger.error(f"Error: {{f"Bulk recommendation status update failed: {str(e}}")
        return None

    async def get_expiring_recommendations(
        self,
        user_id: int,
        days_threshold: int = 7
    ) -> List[AIRecommendation]:
        """Get recommendations that are expiring soon."""
        try:
            expiry_date = date.today() + timedelta(days=days_threshold)
            
            query = select(AIRecommendation).where(
                and_(
                    AIRecommendation.user_id == user_id,
                    AIRecommendation.expiry_date <= expiry_date,
                    AIRecommendation.status == RecommendationStatus.ACTIVE
                )
            )

            result = await self.db_session.execute(query)
            expiring_recommendations = result.scalars().all()

            return expiring_recommendations

        except Exception as e:
            logger.error(f"Failed to get expiring recommendations: {str(e)}")
            logger.error(f"Error: {{f"Failed to get expiring recommendations: {str(e}}")
        return None

    # ==================== Abstract Method Implementations ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for recommendation analysis."""
        try:
            # Get user's recommendations
            recommendations = await self.get_recommendations_by_user(
                user_id,
                time_range=time_range or "90d",
                include_expired=True
            )
            
            # Get user's transaction data
            transaction_data = await self._get_user_transaction_data(user_id, time_range or "90d")

            return {
                "user_id": user_id,
                "data_type": data_type,
                "time_range": time_range,
                "recommendations": [rec.to_dict() for rec in recommendations],
                "transactions": transaction_data,
                "total_recommendations": len(recommendations),
                "accepted_recommendations": len([r for r in recommendations if r.status == RecommendationStatus.ACCEPTED]),
                "declined_recommendations": len([r for r in recommendations if r.status == RecommendationStatus.DECLINED])
            }

        except Exception as e:
            logger.error(f"Failed to get user data for analysis: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _get_user_transactions(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user's transaction data for recommendation analysis."""
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

    async def _get_user_risk_data(self, user_id: int) -> Dict[str, Any]:
        """Get user's recommendation risk data."""
        try:
            # Get user's recommendations
            recommendations = await self.get_recommendations_by_user(user_id, include_expired=True)
            
            # Calculate risk metrics
            total_recommendations = len(recommendations)
            accepted_recommendations = len([r for r in recommendations if r.status == RecommendationStatus.ACCEPTED])
            declined_recommendations = len([r for r in recommendations if r.status == RecommendationStatus.DECLINED])
            high_priority_recommendations = len([r for r in recommendations if r.priority == RecommendationPriority.HIGH])

            # Calculate average confidence score
            confidence_scores = [r.confidence_score for r in recommendations if r.confidence_score is not None]
            avg_confidence_score = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0

            return {
                "user_id": user_id,
                "total_recommendations": total_recommendations,
                "accepted_recommendations": accepted_recommendations,
                "declined_recommendations": declined_recommendations,
                "high_priority_recommendations": high_priority_recommendations,
                "average_confidence_score": avg_confidence_score,
                "acceptance_rate": (accepted_recommendations / total_recommendations * 100) if total_recommendations > 0 else 0.0,
                "recommendations": [rec.to_dict() for rec in recommendations]
            }

        except Exception as e:
            logger.error(f"Failed to get user risk data: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _analyze_spending_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze spending patterns for recommendations."""
        try:
            if not transactions:
                return {"patterns": [], "recommendation_opportunities": []}

            # Calculate basic metrics
            total_amount = sum(t.get("amount", 0) for t in transactions)
            transaction_count = len(transactions)
            
            # Group by category
            category_patterns = {}
            for transaction in transactions:
                category = transaction.get("category", "unknown")
                amount = transaction.get("amount", 0)
                category_patterns[category] = category_patterns.get(category, 0) + amount

            # Find recommendation opportunities
            recommendation_opportunities = []
            
            # Check for high spending categories
            for category, amount in category_patterns.items():
                if amount > total_amount * 0.3:  # More than 30% of spending
                    recommendation_opportunities.append({
                        "type": "spending_optimization",
                        "category": category,
                        "amount": amount,
                        "percentage": (amount / total_amount * 100)
                    })

            return {
                "patterns": {
                    "total_amount": total_amount,
                    "transaction_count": transaction_count,
                    "average_transaction": total_amount / transaction_count if transaction_count > 0 else 0,
                    "category_patterns": category_patterns
                },
                "recommendation_opportunities": recommendation_opportunities
            }

        except Exception as e:
            logger.error(f"Failed to analyze spending patterns: {str(e)}")
            return {"patterns": [], "recommendation_opportunities": [], "error": str(e)}

    async def _analyze_temporal_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns for recommendations."""
        try:
            if not transactions:
                return {"temporal_patterns": [], "recommendation_opportunities": []}

            # Group by hour and day
            hourly_patterns = {}
            daily_patterns = {}
            
            for transaction in transactions:
                timestamp = transaction.get("timestamp")
                if timestamp:
                    hour = timestamp.hour
                    day = timestamp.strftime("%A")
                    
                    hourly_patterns[hour] = hourly_patterns.get(hour, 0) + 1
                    daily_patterns[day] = daily_patterns.get(day, 0) + 1

            # Find recommendation opportunities
            recommendation_opportunities = []
            
            # Check for peak spending times
            peak_hours = sorted(hourly_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
            if peak_hours:
                recommendation_opportunities.append({
                    "type": "timing_optimization",
                    "peak_hours": peak_hours,
                    "suggestion": "Consider scheduling payments during off-peak hours"
                })

            return {
                "temporal_patterns": {
                    "hourly_distribution": hourly_patterns,
                    "daily_distribution": daily_patterns,
                    "peak_hours": peak_hours
                },
                "recommendation_opportunities": recommendation_opportunities
            }

        except Exception as e:
            logger.error(f"Failed to analyze temporal patterns: {str(e)}")
            return {"temporal_patterns": [], "recommendation_opportunities": [], "error": str(e)}

    async def _analyze_geographic_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze geographic patterns for recommendations."""
        try:
            if not transactions:
                return {"geographic_patterns": [], "recommendation_opportunities": []}

            # Group by location
            location_patterns = {}
            
            for transaction in transactions:
                location = transaction.get("location", "unknown")
                amount = transaction.get("amount", 0)
                location_patterns[location] = location_patterns.get(location, 0) + amount

            # Find recommendation opportunities
            recommendation_opportunities = []
            
            # Check for location-based opportunities
            if len(location_patterns) > 5:  # Multiple locations
                recommendation_opportunities.append({
                    "type": "location_optimization",
                    "locations": list(location_patterns.keys()),
                    "suggestion": "Consider location-based rewards or services"
                })

            return {
                "geographic_patterns": {
                    "location_breakdown": location_patterns,
                    "total_locations": len(location_patterns)
                },
                "recommendation_opportunities": recommendation_opportunities
            }

        except Exception as e:
            logger.error(f"Failed to analyze geographic patterns: {str(e)}")
            return {"geographic_patterns": [], "recommendation_opportunities": [], "error": str(e)}

    async def _perform_risk_analysis(
        self,
        user_data: Dict[str, Any],
        assessment_type: str
    ) -> Dict[str, Any]:
        """Perform risk analysis for recommendation-related data."""
        try:
            recommendations = user_data.get("recommendations", [])
            
            # Calculate risk metrics
            total_recommendations = len(recommendations)
            accepted_recommendations = len([r for r in recommendations if r.get("status") == RecommendationStatus.ACCEPTED])
            declined_recommendations = len([r for r in recommendations if r.get("status") == RecommendationStatus.DECLINED])
            high_priority_recommendations = len([r for r in recommendations if r.get("priority") == RecommendationPriority.HIGH])

            # Calculate risk score
            risk_score = 0.0
            risk_factors = []

            if declined_recommendations > accepted_recommendations:
                risk_score += 0.3
                risk_factors.append("High recommendation rejection rate")

            if high_priority_recommendations > 3:
                risk_score += 0.2
                risk_factors.append("Multiple high-priority recommendations")

            if total_recommendations > 10:
                risk_score += 0.1
                risk_factors.append("High number of recommendations")

            # Normalize risk score
            risk_score = min(risk_score, 1.0)

            return {
                "overall_risk_score": risk_score,
                "risk_factors": risk_factors,
                "recommendation_metrics": {
                    "total_recommendations": total_recommendations,
                    "accepted_recommendations": accepted_recommendations,
                    "declined_recommendations": declined_recommendations,
                    "high_priority_recommendations": high_priority_recommendations
                }
            }

        except Exception as e:
            logger.error(f"Failed to perform risk analysis: {str(e)}")
            return {"overall_risk_score": 0.0, "risk_factors": [], "error": str(e)}

    # ==================== Helper Methods ====================

    async def _get_user_recommendation_data(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive user data for recommendation generation."""
        try:
            # Get user's recommendations
            recommendations = await self.get_recommendations_by_user(user_id, include_expired=True)
            
            # Get user's transaction data
            transactions = await self._get_user_transaction_data(user_id, "90d")

            # Get user preferences
            preferences = await self.analyze_user_preferences(user_id, "180d")

            return {
                "user_id": user_id,
                "recommendations": [rec.to_dict() for rec in recommendations],
                "transactions": transactions,
                "preferences": preferences,
                "total_recommendations": len(recommendations),
                "accepted_recommendations": len([r for r in recommendations if r.status == RecommendationStatus.ACCEPTED]),
                "declined_recommendations": len([r for r in recommendations if r.status == RecommendationStatus.DECLINED])
            }

        except Exception as e:
            logger.error(f"Failed to get user recommendation data: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _analyze_feedback_for_learning(
        self,
        recommendation_id: Union[int, str, UUID],
        feedback: str,
        rating: int
    ) -> None:
        """Analyze user feedback for learning and improvement."""
        try:
            # Get the recommendation
            recommendation = await self.get_by_id(recommendation_id)
            if not recommendation:
                return

            # Analyze feedback with AI
            feedback_data = {
                "recommendation": recommendation.to_dict(),
                "feedback": feedback,
                "rating": rating
            }

            feedback_analysis = await self.analyze_with_ai(
                feedback_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            # Store feedback analysis for future learning
            # This could be stored in a separate table or used to update recommendation models
            logger.info(f"Feedback analysis completed for recommendation {recommendation_id}")

        except Exception as e:
            logger.error(f"Failed to analyze feedback for learning: {str(e)}")

    async def _calculate_type_distribution(
        self,
        recommendations: List[AIRecommendation]
    ) -> Dict[str, int]:
        """Calculate recommendation type distribution."""
        try:
            distribution = {}

            for recommendation in recommendations:
                rec_type = recommendation.recommendation_type.value if recommendation.recommendation_type else "unknown"
                distribution[rec_type] = distribution.get(rec_type, 0) + 1

            return distribution

        except Exception as e:
            logger.error(f"Failed to calculate type distribution: {str(e)}")
            return {}

    async def _calculate_status_distribution(
        self,
        recommendations: List[AIRecommendation]
    ) -> Dict[str, int]:
        """Calculate recommendation status distribution."""
        try:
            distribution = {}

            for recommendation in recommendations:
                status = recommendation.status.value if recommendation.status else "unknown"
                distribution[status] = distribution.get(status, 0) + 1

            return distribution

        except Exception as e:
            logger.error(f"Failed to calculate status distribution: {str(e)}")
            return {}

    async def _invalidate_recommendation_caches(self, recommendation_ids: List[Union[int, str, UUID]]) -> None:
        """Invalidate caches related to specific recommendations."""
        try:
            for recommendation_id in recommendation_ids:
                cache_patterns = [
                    f"user_recommendations:*",
                    f"personalized_recommendations:*",
                    f"user_preferences:*"
                ]
                
                # Clear related caches
                for pattern in cache_patterns:
                    await self.cache_manager.delete(pattern)

        except Exception as e:
            logger.error(f"Failed to invalidate recommendation caches: {str(e)}") 