"""
Enhanced fraud alert repository with AI integration for fraud detection and alert management.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, select, func, text, desc
from sqlalchemy.orm import selectinload

from app.models.fraud_alert import FraudAlert, FraudAlertType, FraudAlertStatus, FraudAlertSeverity
from app.schemas.ai import FraudAlertCreate, FraudAlertUpdate
from app.repositories.enhanced_base import AIEnhancedRepository
from app.core.llm_orchestrator import TaskType, TaskComplexity
from app.core.exceptions import FraudDetectionError, AlertProcessingError

logger = logging.getLogger(__name__)


class EnhancedFraudAlertRepository(AIEnhancedRepository[FraudAlert, FraudAlertCreate, FraudAlertUpdate]):
    """
    Enhanced fraud alert repository with AI-powered fraud detection and alert management.
    
    Features:
    - Real-time fraud detection and alert generation
    - AI-powered risk assessment and scoring
    - Alert correlation and pattern analysis
    - Automated alert prioritization
    - Fraud trend analysis and reporting
    """

    async def get_alerts_by_user(
        self,
        user_id: int,
        *,
        status: Optional[FraudAlertStatus] = None,
        severity: Optional[FraudAlertSeverity] = None,
        time_range: str = "30d",
        use_cache: bool = True
    ) -> List[FraudAlert]:
        """Get fraud alerts for a specific user with optional filtering."""
        cache_key = f"user_fraud_alerts:{user_id}:{status}:{severity}:{time_range}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(FraudAlert).where(FraudAlert.user_id == user_id)

        if status:
            query = query.where(FraudAlert.status == status)

        if severity:
            query = query.where(FraudAlert.severity == severity)

        # Add time range filter
        if time_range:
            start_date = datetime.utcnow() - timedelta(days=int(time_range[:-1]))
            query = query.where(FraudAlert.created_at >= start_date)

        query = query.order_by(desc(FraudAlert.created_at))

        result = await self.db_session.execute(query)
        alerts = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, alerts, ttl=900)  # 15 minutes

        return alerts

    async def get_alerts_by_account(
        self,
        account_id: int,
        *,
        status: Optional[FraudAlertStatus] = None,
        time_range: str = "30d",
        use_cache: bool = True
    ) -> List[FraudAlert]:
        """Get fraud alerts for a specific account."""
        cache_key = f"account_fraud_alerts:{account_id}:{status}:{time_range}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(FraudAlert).where(FraudAlert.account_id == account_id)

        if status:
            query = query.where(FraudAlert.status == status)

        if time_range:
            start_date = datetime.utcnow() - timedelta(days=int(time_range[:-1]))
            query = query.where(FraudAlert.created_at >= start_date)

        query = query.order_by(desc(FraudAlert.created_at))

        result = await self.db_session.execute(query)
        alerts = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, alerts, ttl=900)  # 15 minutes

        return alerts

    async def analyze_fraud_patterns(
        self,
        user_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Analyze fraud patterns for a user using AI."""
        try:
            # Get user's fraud alerts
            alerts = await self.get_alerts_by_user(user_id, time_range=time_range)

            # Get related transaction data
            transaction_data = await self._get_user_transaction_data(user_id, time_range)

            # Analyze patterns with AI
            pattern_data = {
                "alerts": [alert.to_dict() for alert in alerts],
                "transactions": transaction_data,
                "user_id": user_id,
                "time_range": time_range
            }

            analysis_result = await self.analyze_with_ai(
                pattern_data,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            # Cache the analysis
            cache_key = f"fraud_pattern_analysis:{user_id}:{time_range}"
            await self.cache_manager.set(cache_key, analysis_result, ttl=3600)  # 1 hour

            return analysis_result

        except Exception as e:
            logger.error(f"Fraud pattern analysis failed: {str(e)}")
            raise FraudDetectionError(f"Fraud pattern analysis failed: {str(e)}")

    async def detect_fraud_anomalies(
        self,
        user_id: int,
        threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Detect fraud anomalies for a user."""
        try:
            # Get user's recent activity
            activity_data = await self._get_user_activity_data(user_id, "30d")

            # Detect anomalies using AI
            anomalies = await self.detect_anomalies(activity_data, threshold)

            # Analyze anomalies for fraud indicators
            fraud_analysis = await self.analyze_with_ai(
                {"activity_data": activity_data, "anomalies": anomalies},
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            return fraud_analysis.get("fraud_indicators", [])

        except Exception as e:
            logger.error(f"Fraud anomaly detection failed: {str(e)}")
            raise FraudDetectionError(f"Fraud anomaly detection failed: {str(e)}")

    async def generate_fraud_alert(
        self,
        alert_data: Dict[str, Any],
        auto_analyze: bool = True
    ) -> FraudAlert:
        """Generate a new fraud alert with AI analysis."""
        try:
            # Create the alert
            alert = await self.create(alert_data)

            if auto_analyze:
                # Perform AI analysis on the alert
                analysis_result = await self.analyze_alert_with_ai(alert.alert_id)

                # Update alert with AI insights
                await self.update(alert, {
                    "ai_reasoning": analysis_result.get("reasoning", {}),
                    "risk_score": analysis_result.get("risk_score", alert.risk_score),
                    "confidence": analysis_result.get("confidence", alert.confidence)
                })

            return alert

        except Exception as e:
            logger.error(f"Fraud alert generation failed: {str(e)}")
            raise AlertProcessingError(f"Fraud alert generation failed: {str(e)}")

    async def analyze_alert_with_ai(
        self,
        alert_id: Union[int, str, UUID]
    ) -> Dict[str, Any]:
        """Analyze a fraud alert using AI."""
        try:
            alert = await self.get_by_id(alert_id)
            if not alert:
                raise AlertProcessingError(f"Alert {alert_id} not found")

            # Get related data for analysis
            alert_context = await self._get_alert_context_data(alert_id)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                alert_context,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            # Cache the analysis
            cache_key = f"alert_ai_analysis:{alert_id}"
            await self.cache_manager.set(cache_key, analysis_result, ttl=1800)  # 30 minutes

            return analysis_result

        except Exception as e:
            logger.error(f"Alert AI analysis failed: {str(e)}")
            raise AlertProcessingError(f"Alert AI analysis failed: {str(e)}")

    async def correlate_alerts(
        self,
        alert_id: Union[int, str, UUID]
    ) -> List[Dict[str, Any]]:
        """Find related alerts and correlate patterns."""
        try:
            alert = await self.get_by_id(alert_id)
            if not alert:
                raise AlertProcessingError(f"Alert {alert_id} not found")

            # Get related alerts
            related_alerts = await self._get_related_alerts(alert)

            # Analyze correlations with AI
            correlation_data = {
                "primary_alert": alert.to_dict(),
                "related_alerts": [a.to_dict() for a in related_alerts],
                "correlation_metrics": await self._calculate_correlation_metrics(alert, related_alerts)
            }

            correlation_analysis = await self.analyze_with_ai(
                correlation_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.HIGH
            )

            return correlation_analysis.get("correlations", [])

        except Exception as e:
            logger.error(f"Alert correlation failed: {str(e)}")
            raise AlertProcessingError(f"Alert correlation failed: {str(e)}")

    async def get_fraud_trends(
        self,
        time_range: str = "90d",
        alert_type: Optional[FraudAlertType] = None
    ) -> Dict[str, Any]:
        """Get fraud trends and statistics."""
        try:
            # Get alerts for the time range
            start_date = datetime.utcnow() - timedelta(days=int(time_range[:-1]))
            
            query = select(FraudAlert).where(FraudAlert.created_at >= start_date)
            
            if alert_type:
                query = query.where(FraudAlert.alert_type == alert_type)

            result = await self.db_session.execute(query)
            alerts = result.scalars().all()

            # Analyze trends with AI
            trend_data = {
                "alerts": [alert.to_dict() for alert in alerts],
                "time_range": time_range,
                "alert_type": alert_type,
                "total_alerts": len(alerts),
                "severity_distribution": await self._calculate_severity_distribution(alerts),
                "type_distribution": await self._calculate_type_distribution(alerts)
            }

            trend_analysis = await self.analyze_with_ai(
                trend_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return trend_analysis

        except Exception as e:
            logger.error(f"Fraud trend analysis failed: {str(e)}")
            raise FraudDetectionError(f"Fraud trend analysis failed: {str(e)}")

    async def prioritize_alerts(
        self,
        alert_ids: List[Union[int, str, UUID]]
    ) -> List[Dict[str, Any]]:
        """Prioritize alerts using AI analysis."""
        try:
            prioritized_alerts = []

            for alert_id in alert_ids:
                alert = await self.get_by_id(alert_id)
                if not alert:
                    continue

                # Analyze alert priority
                priority_analysis = await self.analyze_with_ai(
                    alert.to_dict(),
                    TaskType.RISK_ASSESSMENT,
                    TaskComplexity.MEDIUM
                )

                prioritized_alerts.append({
                    "alert_id": str(alert_id),
                    "priority_score": priority_analysis.get("priority_score", 0.0),
                    "urgency_level": priority_analysis.get("urgency_level", "medium"),
                    "recommended_actions": priority_analysis.get("recommended_actions", []),
                    "risk_factors": priority_analysis.get("risk_factors", [])
                })

            # Sort by priority score
            prioritized_alerts.sort(key=lambda x: x["priority_score"], reverse=True)

            return prioritized_alerts

        except Exception as e:
            logger.error(f"Alert prioritization failed: {str(e)}")
            raise AlertProcessingError(f"Alert prioritization failed: {str(e)}")

    async def bulk_update_alert_status(
        self,
        alert_ids: List[Union[int, str, UUID]],
        new_status: FraudAlertStatus,
        investigator: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """Bulk update alert status for multiple alerts."""
        try:
            update_data = {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }

            if investigator:
                update_data["investigated_by"] = investigator

            if notes:
                update_data["investigation_notes"] = notes

            # Update alerts
            updated_count = await self.bulk_update(
                {"alert_id": {"$in": alert_ids}},
                update_data
            )

            # Invalidate related caches
            await self._invalidate_alert_caches(alert_ids)

            logger.info(f"Bulk updated {updated_count} alerts to status {new_status}")
            return updated_count

        except Exception as e:
            logger.error(f"Bulk alert status update failed: {str(e)}")
            raise AlertProcessingError(f"Bulk alert status update failed: {str(e)}")

    async def get_high_risk_alerts(
        self,
        risk_threshold: float = 0.7,
        time_range: str = "7d"
    ) -> List[FraudAlert]:
        """Get high-risk fraud alerts."""
        try:
            start_date = datetime.utcnow() - timedelta(days=int(time_range[:-1]))
            
            query = select(FraudAlert).where(
                and_(
                    FraudAlert.risk_score >= risk_threshold,
                    FraudAlert.created_at >= start_date,
                    FraudAlert.status.in_([FraudAlertStatus.ACTIVE, FraudAlertStatus.INVESTIGATING])
                )
            )

            query = query.order_by(desc(FraudAlert.risk_score))

            result = await self.db_session.execute(query)
            high_risk_alerts = result.scalars().all()

            return high_risk_alerts

        except Exception as e:
            logger.error(f"Failed to get high-risk alerts: {str(e)}")
            raise FraudDetectionError(f"Failed to get high-risk alerts: {str(e)}")

    async def get_fraud_statistics(
        self,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive fraud statistics."""
        try:
            start_date = datetime.utcnow() - timedelta(days=int(time_range[:-1]))
            
            # Get all alerts in time range
            query = select(FraudAlert).where(FraudAlert.created_at >= start_date)
            result = await self.db_session.execute(query)
            alerts = result.scalars().all()

            # Calculate statistics
            total_alerts = len(alerts)
            confirmed_fraud = len([a for a in alerts if a.is_confirmed_fraud])
            false_positives = len([a for a in alerts if a.is_false_positive])
            pending_investigation = len([a for a in alerts if a.status == FraudAlertStatus.ACTIVE])

            # Calculate average risk score
            risk_scores = [a.risk_score for a in alerts if a.risk_score is not None]
            avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

            # Get severity distribution
            severity_distribution = await self._calculate_severity_distribution(alerts)

            # Get type distribution
            type_distribution = await self._calculate_type_distribution(alerts)

            statistics = {
                "time_range": time_range,
                "total_alerts": total_alerts,
                "confirmed_fraud": confirmed_fraud,
                "false_positives": false_positives,
                "pending_investigation": pending_investigation,
                "average_risk_score": avg_risk_score,
                "fraud_rate": (confirmed_fraud / total_alerts * 100) if total_alerts > 0 else 0.0,
                "false_positive_rate": (false_positives / total_alerts * 100) if total_alerts > 0 else 0.0,
                "severity_distribution": severity_distribution,
                "type_distribution": type_distribution
            }

            return statistics

        except Exception as e:
            logger.error(f"Failed to get fraud statistics: {str(e)}")
            raise FraudDetectionError(f"Failed to get fraud statistics: {str(e)}")

    # ==================== Abstract Method Implementations ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for fraud analysis."""
        try:
            # Get user's fraud alerts
            alerts = await self.get_alerts_by_user(user_id, time_range=time_range or "30d")
            
            # Get user's transaction data
            transaction_data = await self._get_user_transaction_data(user_id, time_range or "30d")

            return {
                "user_id": user_id,
                "data_type": data_type,
                "time_range": time_range,
                "fraud_alerts": [alert.to_dict() for alert in alerts],
                "transactions": transaction_data,
                "total_alerts": len(alerts),
                "confirmed_fraud": len([a for a in alerts if a.is_confirmed_fraud]),
                "false_positives": len([a for a in alerts if a.is_false_positive])
            }

        except Exception as e:
            logger.error(f"Failed to get user data for analysis: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _get_user_transactions(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user's transaction data for fraud analysis."""
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
        """Get user's fraud risk data."""
        try:
            # Get user's fraud alerts
            alerts = await self.get_alerts_by_user(user_id, time_range="90d")
            
            # Calculate risk metrics
            total_alerts = len(alerts)
            confirmed_fraud = len([a for a in alerts if a.is_confirmed_fraud])
            false_positives = len([a for a in alerts if a.is_false_positive])
            high_risk_alerts = len([a for a in alerts if a.severity in [FraudAlertSeverity.HIGH, FraudAlertSeverity.CRITICAL]])

            # Calculate average risk score
            risk_scores = [a.risk_score for a in alerts if a.risk_score is not None]
            avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

            return {
                "user_id": user_id,
                "total_alerts": total_alerts,
                "confirmed_fraud": confirmed_fraud,
                "false_positives": false_positives,
                "high_risk_alerts": high_risk_alerts,
                "average_risk_score": avg_risk_score,
                "fraud_rate": (confirmed_fraud / total_alerts * 100) if total_alerts > 0 else 0.0,
                "alerts": [alert.to_dict() for alert in alerts]
            }

        except Exception as e:
            logger.error(f"Failed to get user risk data: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _analyze_spending_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze spending patterns for fraud detection."""
        try:
            if not transactions:
                return {"patterns": [], "fraud_indicators": []}

            # Calculate basic metrics
            total_amount = sum(t.get("amount", 0) for t in transactions)
            transaction_count = len(transactions)
            
            # Group by category and location
            category_patterns = {}
            location_patterns = {}
            
            for transaction in transactions:
                category = transaction.get("category", "unknown")
                location = transaction.get("location", "unknown")
                amount = transaction.get("amount", 0)
                
                category_patterns[category] = category_patterns.get(category, 0) + amount
                location_patterns[location] = location_patterns.get(location, 0) + amount

            # Detect potential fraud indicators
            fraud_indicators = []
            
            # Check for unusual amounts
            if total_amount > 10000:  # High amount threshold
                fraud_indicators.append("high_transaction_amount")
            
            # Check for unusual locations
            if len(location_patterns) > 10:  # Many different locations
                fraud_indicators.append("multiple_locations")

            return {
                "patterns": {
                    "total_amount": total_amount,
                    "transaction_count": transaction_count,
                    "average_transaction": total_amount / transaction_count if transaction_count > 0 else 0,
                    "category_patterns": category_patterns,
                    "location_patterns": location_patterns
                },
                "fraud_indicators": fraud_indicators
            }

        except Exception as e:
            logger.error(f"Failed to analyze spending patterns: {str(e)}")
            return {"patterns": [], "fraud_indicators": [], "error": str(e)}

    async def _analyze_temporal_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns for fraud detection."""
        try:
            if not transactions:
                return {"temporal_patterns": [], "fraud_indicators": []}

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

            # Detect temporal fraud indicators
            fraud_indicators = []
            
            # Check for unusual hours (late night transactions)
            late_night_transactions = sum(hourly_patterns.get(hour, 0) for hour in [22, 23, 0, 1, 2, 3, 4, 5])
            if late_night_transactions > len(transactions) * 0.3:  # More than 30% at night
                fraud_indicators.append("unusual_timing")

            return {
                "temporal_patterns": {
                    "hourly_distribution": hourly_patterns,
                    "daily_distribution": daily_patterns,
                    "late_night_transactions": late_night_transactions
                },
                "fraud_indicators": fraud_indicators
            }

        except Exception as e:
            logger.error(f"Failed to analyze temporal patterns: {str(e)}")
            return {"temporal_patterns": [], "fraud_indicators": [], "error": str(e)}

    async def _analyze_geographic_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze geographic patterns for fraud detection."""
        try:
            if not transactions:
                return {"geographic_patterns": [], "fraud_indicators": []}

            # Group by location
            location_patterns = {}
            
            for transaction in transactions:
                location = transaction.get("location", "unknown")
                amount = transaction.get("amount", 0)
                location_patterns[location] = location_patterns.get(location, 0) + amount

            # Detect geographic fraud indicators
            fraud_indicators = []
            
            # Check for multiple locations
            if len(location_patterns) > 5:  # Many different locations
                fraud_indicators.append("multiple_locations")
            
            # Check for unusual locations
            unusual_locations = [loc for loc in location_patterns.keys() if "unknown" in loc.lower()]
            if unusual_locations:
                fraud_indicators.append("unusual_locations")

            return {
                "geographic_patterns": {
                    "location_breakdown": location_patterns,
                    "total_locations": len(location_patterns),
                    "unusual_locations": unusual_locations
                },
                "fraud_indicators": fraud_indicators
            }

        except Exception as e:
            logger.error(f"Failed to analyze geographic patterns: {str(e)}")
            return {"geographic_patterns": [], "fraud_indicators": [], "error": str(e)}

    async def _perform_risk_analysis(
        self,
        user_data: Dict[str, Any],
        assessment_type: str
    ) -> Dict[str, Any]:
        """Perform risk analysis for fraud-related data."""
        try:
            alerts = user_data.get("fraud_alerts", [])
            
            # Calculate risk metrics
            total_alerts = len(alerts)
            confirmed_fraud = len([a for a in alerts if a.get("is_confirmed_fraud", False)])
            false_positives = len([a for a in alerts if a.get("is_false_positive", False)])
            high_risk_alerts = len([a for a in alerts if a.get("severity") in ["high", "critical"]])

            # Calculate risk score
            risk_score = 0.0
            risk_factors = []

            if confirmed_fraud > 0:
                risk_score += 0.4
                risk_factors.append("Confirmed fraud detected")

            if high_risk_alerts > 0:
                risk_score += 0.3
                risk_factors.append("High-risk alerts present")

            if total_alerts > 5:
                risk_score += 0.2
                risk_factors.append("Multiple fraud alerts")

            # Normalize risk score
            risk_score = min(risk_score, 1.0)

            return {
                "overall_risk_score": risk_score,
                "risk_factors": risk_factors,
                "fraud_metrics": {
                    "total_alerts": total_alerts,
                    "confirmed_fraud": confirmed_fraud,
                    "false_positives": false_positives,
                    "high_risk_alerts": high_risk_alerts
                }
            }

        except Exception as e:
            logger.error(f"Failed to perform risk analysis: {str(e)}")
            return {"overall_risk_score": 0.0, "risk_factors": [], "error": str(e)}

    # ==================== Helper Methods ====================

    async def _get_user_activity_data(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user activity data for fraud analysis."""
        try:
            # Get user's transactions and alerts
            transactions = await self._get_user_transaction_data(user_id, time_range)
            alerts = await self.get_alerts_by_user(user_id, time_range=time_range)

            # Combine into activity data
            activity_data = []
            
            # Add transactions
            for transaction in transactions:
                activity_data.append({
                    "type": "transaction",
                    "data": transaction,
                    "timestamp": transaction.get("timestamp")
                })

            # Add alerts
            for alert in alerts:
                activity_data.append({
                    "type": "alert",
                    "data": alert.to_dict(),
                    "timestamp": alert.created_at
                })

            return activity_data

        except Exception as e:
            logger.error(f"Failed to get user activity data: {str(e)}")
            return []

    async def _get_user_transaction_data(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user's transaction data."""
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
            logger.error(f"Failed to get user transaction data: {str(e)}")
            return []

    async def _get_alert_context_data(
        self,
        alert_id: Union[int, str, UUID]
    ) -> Dict[str, Any]:
        """Get context data for alert analysis."""
        try:
            alert = await self.get_by_id(alert_id)
            if not alert:
                return {"error": "Alert not found"}

            # Get related data
            related_alerts = await self._get_related_alerts(alert)
            user_transactions = await self._get_user_transaction_data(alert.user_id, "30d")

            return {
                "alert": alert.to_dict(),
                "related_alerts": [a.to_dict() for a in related_alerts],
                "user_transactions": user_transactions,
                "user_id": alert.user_id,
                "account_id": alert.account_id
            }

        except Exception as e:
            logger.error(f"Failed to get alert context data: {str(e)}")
            return {"error": str(e)}

    async def _get_related_alerts(
        self,
        alert: FraudAlert
    ) -> List[FraudAlert]:
        """Get alerts related to the given alert."""
        try:
            # Get alerts for the same user within a time window
            time_window = alert.created_at - timedelta(days=7)
            
            query = select(FraudAlert).where(
                and_(
                    FraudAlert.user_id == alert.user_id,
                    FraudAlert.alert_id != alert.alert_id,
                    FraudAlert.created_at >= time_window
                )
            )

            result = await self.db_session.execute(query)
            related_alerts = result.scalars().all()

            return related_alerts

        except Exception as e:
            logger.error(f"Failed to get related alerts: {str(e)}")
            return []

    async def _calculate_correlation_metrics(
        self,
        primary_alert: FraudAlert,
        related_alerts: List[FraudAlert]
    ) -> Dict[str, Any]:
        """Calculate correlation metrics between alerts."""
        try:
            if not related_alerts:
                return {"correlation_score": 0.0, "shared_indicators": []}

            # Calculate correlation score based on shared characteristics
            shared_indicators = []
            correlation_score = 0.0

            for related_alert in related_alerts:
                # Check for shared alert types
                if primary_alert.alert_type == related_alert.alert_type:
                    correlation_score += 0.3
                    shared_indicators.append("same_alert_type")

                # Check for similar risk scores
                if abs(primary_alert.risk_score - related_alert.risk_score) < 0.2:
                    correlation_score += 0.2
                    shared_indicators.append("similar_risk_score")

                # Check for temporal proximity
                time_diff = abs((primary_alert.created_at - related_alert.created_at).total_seconds())
                if time_diff < 3600:  # Within 1 hour
                    correlation_score += 0.3
                    shared_indicators.append("temporal_proximity")

            # Normalize correlation score
            correlation_score = min(correlation_score, 1.0)

            return {
                "correlation_score": correlation_score,
                "shared_indicators": list(set(shared_indicators)),
                "related_alert_count": len(related_alerts)
            }

        except Exception as e:
            logger.error(f"Failed to calculate correlation metrics: {str(e)}")
            return {"correlation_score": 0.0, "shared_indicators": [], "error": str(e)}

    async def _calculate_severity_distribution(
        self,
        alerts: List[FraudAlert]
    ) -> Dict[str, int]:
        """Calculate severity distribution for alerts."""
        try:
            distribution = {
                "low": 0,
                "medium": 0,
                "high": 0,
                "critical": 0
            }

            for alert in alerts:
                severity = alert.severity.value if alert.severity else "unknown"
                distribution[severity] = distribution.get(severity, 0) + 1

            return distribution

        except Exception as e:
            logger.error(f"Failed to calculate severity distribution: {str(e)}")
            return {"low": 0, "medium": 0, "high": 0, "critical": 0}

    async def _calculate_type_distribution(
        self,
        alerts: List[FraudAlert]
    ) -> Dict[str, int]:
        """Calculate alert type distribution."""
        try:
            distribution = {}

            for alert in alerts:
                alert_type = alert.alert_type.value if alert.alert_type else "unknown"
                distribution[alert_type] = distribution.get(alert_type, 0) + 1

            return distribution

        except Exception as e:
            logger.error(f"Failed to calculate type distribution: {str(e)}")
            return {}

    async def _invalidate_alert_caches(self, alert_ids: List[Union[int, str, UUID]]) -> None:
        """Invalidate caches related to specific alerts."""
        try:
            for alert_id in alert_ids:
                cache_patterns = [
                    f"alert_ai_analysis:{alert_id}",
                    f"user_fraud_alerts:*",
                    f"account_fraud_alerts:*",
                    f"fraud_pattern_analysis:*"
                ]
                
                # Clear related caches
                for pattern in cache_patterns:
                    await self.cache_manager.delete(pattern)

        except Exception as e:
            logger.error(f"Failed to invalidate alert caches: {str(e)}") 