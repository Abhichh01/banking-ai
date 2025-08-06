"""
Enhanced card repository with AI integration for card management and security analysis.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, select, func, text
from sqlalchemy.orm import selectinload

from app.models.card import Card, CardStatus, CardType
from app.schemas.account import CardCreate, CardUpdate
from app.repositories.enhanced_base import AIEnhancedRepository
from app.core.llm_orchestrator import TaskType, TaskComplexity
# Exception imports removed for MVP
# All custom exceptions replaced with standard logging

logger = logging.getLogger(__name__)


class EnhancedCardRepository(AIEnhancedRepository[Card, CardCreate, CardUpdate]):
    """
    Enhanced card repository with AI-powered security analysis and fraud detection.
    
    Features:
    - Card security analysis and risk assessment
    - Usage pattern analysis and anomaly detection
    - Fraud detection for card transactions
    - Card recommendation engine
    - Security monitoring and alerts
    """

    async def get_cards_by_user(
        self,
        user_id: int,
        *,
        include_inactive: bool = False,
        card_type: Optional[CardType] = None,
        status: Optional[CardStatus] = None,
        use_cache: bool = True
    ) -> List[Card]:
        """Get all cards for a specific user with optional filtering."""
        cache_key = f"user_cards:{user_id}:{card_type}:{status}:{include_inactive}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Card).where(Card.user_id == user_id)

        if not include_inactive:
            query = query.where(Card.status.in_([CardStatus.ACTIVE, CardStatus.PENDING_ACTIVATION]))

        if card_type:
            query = query.where(Card.card_type == card_type)

        if status:
            query = query.where(Card.status == status)

        result = await self.db_session.execute(query)
        cards = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, cards, ttl=1800)  # 30 minutes

        return cards

    async def get_cards_by_account(
        self,
        account_id: int,
        *,
        include_inactive: bool = False,
        use_cache: bool = True
    ) -> List[Card]:
        """Get all cards linked to a specific account."""
        cache_key = f"account_cards:{account_id}:{include_inactive}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Card).where(Card.account_id == account_id)

        if not include_inactive:
            query = query.where(Card.status.in_([CardStatus.ACTIVE, CardStatus.PENDING_ACTIVATION]))

        result = await self.db_session.execute(query)
        cards = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, cards, ttl=1800)  # 30 minutes

        return cards

    async def analyze_card_security(
        self,
        card_id: Union[int, str, UUID],
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze card security using AI."""
        try:
            card = await self.get_by_id(card_id)
            if not card:
                logger.error(f"Card {card_id} not found")
                return {}

            # Get card usage data
            card_data = await self._get_card_security_data(card_id)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                card_data,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            # Cache the analysis
            cache_key = f"card_security_analysis:{card_id}:{analysis_type}"
            await self.cache_manager.set(cache_key, analysis_result, ttl=3600)  # 1 hour

            return analysis_result

        except Exception as e:
            logger.error(f"Card security analysis failed: {str(e)}")
            return {}

    async def detect_card_fraud(
        self,
        card_id: Union[int, str, UUID],
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Detect potential fraud patterns for a card."""
        try:
            # Get card transaction data
            transaction_data = await self._get_card_transaction_data(card_id, time_range)

            # Detect anomalies
            anomalies = await self.detect_anomalies(transaction_data, threshold=0.8)

            # Analyze with AI for fraud patterns
            fraud_analysis = await self.analyze_with_ai(
                {"transactions": transaction_data, "anomalies": anomalies},
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            fraud_result = {
                "card_id": str(card_id),
                "time_range": time_range,
                "anomalies_detected": len(anomalies),
                "fraud_risk_score": fraud_analysis.get("risk_score", 0.0),
                "fraud_indicators": fraud_analysis.get("fraud_indicators", []),
                "recommendations": fraud_analysis.get("recommendations", []),
                "analysis_timestamp": datetime.utcnow().isoformat()
            }

            # Cache the fraud analysis
            cache_key = f"card_fraud_analysis:{card_id}:{time_range}"
            await self.cache_manager.set(cache_key, fraud_result, ttl=1800)  # 30 minutes

            return fraud_result

        except Exception as e:
            logger.error(f"Card fraud detection failed: {str(e)}")
            return {}

    async def analyze_card_usage_patterns(
        self,
        card_id: Union[int, str, UUID],
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Analyze card usage patterns using AI."""
        try:
            # Get card usage data
            usage_data = await self._get_card_usage_data(card_id, time_range)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                usage_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            # Cache the analysis
            cache_key = f"card_usage_analysis:{card_id}:{time_range}"
            await self.cache_manager.set(cache_key, analysis_result, ttl=3600)  # 1 hour

            return analysis_result

        except Exception as e:
            logger.error(f"Card usage pattern analysis failed: {str(e)}")
            return {}

    async def get_card_recommendations(
        self,
        user_id: int,
        account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get AI-powered card recommendations for a user."""
        try:
            # Get user and account data
            user_data = await self._get_user_card_data(user_id, account_id)

            # Generate recommendations with AI
            recommendations = await self.analyze_with_ai(
                user_data,
                TaskType.FINANCIAL_RECOMMENDATION,
                TaskComplexity.MEDIUM
            )

            # Cache the recommendations
            cache_key = f"card_recommendations:{user_id}:{account_id}"
            await self.cache_manager.set(cache_key, recommendations, ttl=7200)  # 2 hours

            return recommendations

        except Exception as e:
            logger.error(f"Card recommendations failed: {str(e)}")
            return {}

    async def monitor_card_security(
        self,
        card_id: Union[int, str, UUID]
    ) -> Dict[str, Any]:
        """Monitor card security status and generate alerts."""
        try:
            card = await self.get_by_id(card_id)
            if not card:
                logger.error(f"Card {card_id} not found")
                return {}

            # Get security monitoring data
            security_data = await self._get_card_security_monitoring_data(card_id)

            # Analyze security status with AI
            security_analysis = await self.analyze_with_ai(
                security_data,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            # Generate security alerts
            alerts = await self._generate_security_alerts(card, security_analysis)

            security_result = {
                "card_id": str(card_id),
                "security_status": security_analysis.get("security_status", "unknown"),
                "risk_level": security_analysis.get("risk_level", "unknown"),
                "alerts": alerts,
                "recommendations": security_analysis.get("recommendations", []),
                "monitoring_timestamp": datetime.utcnow().isoformat()
            }

            # Cache the security monitoring result
            cache_key = f"card_security_monitoring:{card_id}"
            await self.cache_manager.set(cache_key, security_result, ttl=1800)  # 30 minutes

            return security_result

        except Exception as e:
            logger.error(f"Card security monitoring failed: {str(e)}")
            return {}

    async def bulk_update_card_status(
        self,
        card_ids: List[Union[int, str, UUID]],
        new_status: CardStatus,
        reason: Optional[str] = None
    ) -> int:
        """Bulk update card status for multiple cards."""
        try:
            # Update cards
            updated_count = await self.bulk_update(
                {"id": {"$in": card_ids}},
                {"status": new_status, "updated_at": datetime.utcnow()}
            )

            # Invalidate related caches
            await self._invalidate_card_caches(card_ids)

            logger.info(f"Bulk updated {updated_count} cards to status {new_status}")
            return updated_count

        except Exception as e:
            logger.error(f"Bulk card status update failed: {str(e)}")
            return 0

    async def get_expiring_cards(
        self,
        days_threshold: int = 30,
        user_id: Optional[int] = None
    ) -> List[Card]:
        """Get cards that are expiring within the specified days."""
        try:
            expiry_date = datetime.utcnow() + timedelta(days=days_threshold)
            
            query = select(Card).where(
                and_(
                    Card.expiry_date <= expiry_date,
                    Card.status.in_([CardStatus.ACTIVE, CardStatus.PENDING_ACTIVATION])
                )
            )

            if user_id:
                query = query.where(Card.user_id == user_id)

            result = await self.db_session.execute(query)
            expiring_cards = result.scalars().all()

            return expiring_cards

        except Exception as e:
            logger.error(f"Failed to get expiring cards: {str(e)}")
            return []

    async def get_suspicious_cards(
        self,
        risk_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get cards with suspicious activity patterns."""
        try:
            # Get all active cards
            active_cards = await self.get_multi(status=CardStatus.ACTIVE)

            suspicious_cards = []

            for card in active_cards:
                # Analyze each card for suspicious activity
                fraud_analysis = await self.detect_card_fraud(card.id, "30d")
                
                if fraud_analysis.get("fraud_risk_score", 0.0) >= risk_threshold:
                    suspicious_cards.append({
                        "card_id": str(card.id),
                        "user_id": card.user_id,
                        "account_id": card.account_id,
                        "risk_score": fraud_analysis.get("fraud_risk_score", 0.0),
                        "fraud_indicators": fraud_analysis.get("fraud_indicators", []),
                        "last_used": card.last_used,
                        "status": card.status
                    })

            return suspicious_cards

        except Exception as e:
            logger.error(f"Failed to get suspicious cards: {str(e)}")
            return []

    # ==================== Abstract Method Implementations ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for card analysis."""
        try:
            # Get user's cards
            user_cards = await self.get_cards_by_user(user_id, include_inactive=True)
            
            # Get card usage data
            card_usage_data = []
            for card in user_cards:
                usage_data = await self._get_card_usage_data(card.id, time_range or "30d")
                card_usage_data.append(usage_data)

            return {
                "user_id": user_id,
                "data_type": data_type,
                "time_range": time_range,
                "cards": [card.to_dict() for card in user_cards],
                "card_usage_data": card_usage_data,
                "total_cards": len(user_cards),
                "active_cards": len([c for c in user_cards if c.status == CardStatus.ACTIVE])
            }

        except Exception as e:
            logger.error(f"Failed to get user data for analysis: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _get_user_transactions(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user's card transactions."""
        try:
            # Get user's cards
            user_cards = await self.get_cards_by_user(user_id, include_inactive=True)
            
            # Get transactions for each card
            all_transactions = []
            for card in user_cards:
                card_transactions = await self._get_card_transaction_data(card.id, time_range)
                all_transactions.extend(card_transactions)

            return all_transactions

        except Exception as e:
            logger.error(f"Failed to get user transactions: {str(e)}")
            return []

    async def _get_user_risk_data(self, user_id: int) -> Dict[str, Any]:
        """Get user's card risk data."""
        try:
            # Get user's cards
            user_cards = await self.get_cards_by_user(user_id, include_inactive=True)
            
            # Calculate risk metrics
            total_cards = len(user_cards)
            active_cards = len([c for c in user_cards if c.status == CardStatus.ACTIVE])
            blocked_cards = len([c for c in user_cards if c.status == CardStatus.BLOCKED])
            expired_cards = len([c for c in user_cards if c.is_expired()])

            # Get recent fraud analysis
            recent_fraud_scores = []
            for card in user_cards[:5]:  # Analyze last 5 cards
                try:
                    fraud_analysis = await self.detect_card_fraud(card.id, "30d")
                    recent_fraud_scores.append(fraud_analysis.get("fraud_risk_score", 0.0))
                except Exception:
                    recent_fraud_scores.append(0.0)

            return {
                "user_id": user_id,
                "total_cards": total_cards,
                "active_cards": active_cards,
                "blocked_cards": blocked_cards,
                "expired_cards": expired_cards,
                "average_fraud_risk_score": sum(recent_fraud_scores) / len(recent_fraud_scores) if recent_fraud_scores else 0.0,
                "cards": [card.to_dict() for card in user_cards]
            }

        except Exception as e:
            logger.error(f"Failed to get user risk data: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _analyze_spending_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze spending patterns from card transactions."""
        try:
            if not transactions:
                return {"patterns": [], "total_spent": 0.0, "transaction_count": 0}

            # Calculate basic metrics
            total_spent = sum(t.get("amount", 0) for t in transactions)
            transaction_count = len(transactions)
            
            # Group by category
            category_spending = {}
            for transaction in transactions:
                category = transaction.get("category", "unknown")
                amount = transaction.get("amount", 0)
                category_spending[category] = category_spending.get(category, 0) + amount

            # Find top spending categories
            top_categories = sorted(
                category_spending.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            return {
                "patterns": {
                    "total_spent": total_spent,
                    "transaction_count": transaction_count,
                    "average_transaction": total_spent / transaction_count if transaction_count > 0 else 0,
                    "top_categories": top_categories,
                    "category_breakdown": category_spending
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze spending patterns: {str(e)}")
            return {"patterns": [], "error": str(e)}

    async def _analyze_temporal_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns from card transactions."""
        try:
            if not transactions:
                return {"temporal_patterns": [], "peak_hours": [], "peak_days": []}

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

            # Find peak hours and days
            peak_hours = sorted(hourly_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_days = sorted(daily_patterns.items(), key=lambda x: x[1], reverse=True)[:3]

            return {
                "temporal_patterns": {
                    "hourly_distribution": hourly_patterns,
                    "daily_distribution": daily_patterns,
                    "peak_hours": peak_hours,
                    "peak_days": peak_days
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze temporal patterns: {str(e)}")
            return {"temporal_patterns": [], "error": str(e)}

    async def _analyze_geographic_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze geographic patterns from card transactions."""
        try:
            if not transactions:
                return {"geographic_patterns": [], "top_locations": []}

            # Group by location
            location_patterns = {}
            
            for transaction in transactions:
                location = transaction.get("location", "unknown")
                amount = transaction.get("amount", 0)
                location_patterns[location] = location_patterns.get(location, 0) + amount

            # Find top locations
            top_locations = sorted(
                location_patterns.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]

            return {
                "geographic_patterns": {
                    "location_breakdown": location_patterns,
                    "top_locations": top_locations,
                    "total_locations": len(location_patterns)
                }
            }

        except Exception as e:
            logger.error(f"Failed to analyze geographic patterns: {str(e)}")
            return {"geographic_patterns": [], "error": str(e)}

    async def _perform_risk_analysis(
        self,
        user_data: Dict[str, Any],
        assessment_type: str
    ) -> Dict[str, Any]:
        """Perform risk analysis for card-related data."""
        try:
            cards = user_data.get("cards", [])
            
            # Calculate risk metrics
            total_cards = len(cards)
            active_cards = len([c for c in cards if c.get("status") == CardStatus.ACTIVE])
            blocked_cards = len([c for c in cards if c.get("status") == CardStatus.BLOCKED])
            expired_cards = len([c for c in cards if c.get("is_expired", False)])

            # Calculate risk score
            risk_score = 0.0
            risk_factors = []

            if blocked_cards > 0:
                risk_score += 0.3
                risk_factors.append("Blocked cards detected")

            if expired_cards > 0:
                risk_score += 0.2
                risk_factors.append("Expired cards detected")

            if total_cards > 5:
                risk_score += 0.1
                risk_factors.append("High number of cards")

            # Normalize risk score
            risk_score = min(risk_score, 1.0)

            return {
                "overall_risk_score": risk_score,
                "risk_factors": risk_factors,
                "card_metrics": {
                    "total_cards": total_cards,
                    "active_cards": active_cards,
                    "blocked_cards": blocked_cards,
                    "expired_cards": expired_cards
                }
            }

        except Exception as e:
            logger.error(f"Failed to perform risk analysis: {str(e)}")
            return {"overall_risk_score": 0.0, "risk_factors": [], "error": str(e)}

    # ==================== Helper Methods ====================

    async def _get_card_security_data(self, card_id: Union[int, str, UUID]) -> Dict[str, Any]:
        """Get card security data for analysis."""
        try:
            card = await self.get_by_id(card_id)
            if not card:
                return {"error": "Card not found"}

            # Get recent transactions
            recent_transactions = await self._get_card_transaction_data(card_id, "30d")

            return {
                "card_info": card.to_dict(),
                "recent_transactions": recent_transactions,
                "security_metrics": {
                    "failed_attempts": card.pin_retry_attempts,
                    "is_locked": card.is_locked,
                    "days_since_last_used": (datetime.utcnow() - card.last_used).days if card.last_used else None,
                    "days_until_expiry": (card.expiry_date - datetime.utcnow().date()).days if card.expiry_date else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to get card security data: {str(e)}")
            return {"error": str(e)}

    async def _get_card_transaction_data(
        self,
        card_id: Union[int, str, UUID],
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get card transaction data for analysis."""
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
            logger.error(f"Failed to get card transaction data: {str(e)}")
            return []

    async def _get_card_usage_data(
        self,
        card_id: Union[int, str, UUID],
        time_range: str
    ) -> Dict[str, Any]:
        """Get card usage data for analysis."""
        try:
            card = await self.get_by_id(card_id)
            if not card:
                return {"error": "Card not found"}

            # Get transaction data
            transactions = await self._get_card_transaction_data(card_id, time_range)

            return {
                "card_info": card.to_dict(),
                "transactions": transactions,
                "usage_metrics": {
                    "total_transactions": len(transactions),
                    "total_amount": sum(t.get("amount", 0) for t in transactions),
                    "last_used": card.last_used,
                    "days_since_last_used": (datetime.utcnow() - card.last_used).days if card.last_used else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to get card usage data: {str(e)}")
            return {"error": str(e)}

    async def _get_user_card_data(
        self,
        user_id: int,
        account_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get user card data for recommendations."""
        try:
            # Get user's cards
            if account_id:
                user_cards = await self.get_cards_by_account(account_id)
            else:
                user_cards = await self.get_cards_by_user(user_id)

            # Get usage data for each card
            card_usage_data = []
            for card in user_cards:
                usage_data = await self._get_card_usage_data(card.id, "90d")
                card_usage_data.append(usage_data)

            return {
                "user_id": user_id,
                "account_id": account_id,
                "cards": [card.to_dict() for card in user_cards],
                "card_usage_data": card_usage_data,
                "total_cards": len(user_cards),
                "active_cards": len([c for c in user_cards if c.status == CardStatus.ACTIVE])
            }

        except Exception as e:
            logger.error(f"Failed to get user card data: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _get_card_security_monitoring_data(
        self,
        card_id: Union[int, str, UUID]
    ) -> Dict[str, Any]:
        """Get card security monitoring data."""
        try:
            card = await self.get_by_id(card_id)
            if not card:
                return {"error": "Card not found"}

            # Get recent security events
            recent_transactions = await self._get_card_transaction_data(card_id, "7d")

            return {
                "card_info": card.to_dict(),
                "recent_transactions": recent_transactions,
                "security_status": {
                    "is_locked": card.is_locked,
                    "failed_attempts": card.pin_retry_attempts,
                    "is_expired": card.is_expired(),
                    "days_until_expiry": (card.expiry_date - datetime.utcnow().date()).days if card.expiry_date else None
                }
            }

        except Exception as e:
            logger.error(f"Failed to get card security monitoring data: {str(e)}")
            return {"error": str(e)}

    async def _generate_security_alerts(
        self,
        card: Card,
        security_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate security alerts based on analysis."""
        alerts = []

        try:
            # Check for expired card
            if card.is_expired():
                alerts.append({
                    "type": "expired_card",
                    "severity": "high",
                    "message": "Card has expired and should be replaced",
                    "timestamp": datetime.utcnow().isoformat()
                })

            # Check for too many failed attempts
            if card.pin_retry_attempts >= 3:
                alerts.append({
                    "type": "multiple_failed_attempts",
                    "severity": "medium",
                    "message": "Multiple failed PIN attempts detected",
                    "timestamp": datetime.utcnow().isoformat()
                })

            # Check for high risk score
            risk_score = security_analysis.get("risk_score", 0.0)
            if risk_score > 0.7:
                alerts.append({
                    "type": "high_risk_card",
                    "severity": "high",
                    "message": f"High risk score detected: {risk_score}",
                    "timestamp": datetime.utcnow().isoformat()
                })

            # Check for unusual activity
            if security_analysis.get("unusual_activity", False):
                alerts.append({
                    "type": "unusual_activity",
                    "severity": "medium",
                    "message": "Unusual card activity detected",
                    "timestamp": datetime.utcnow().isoformat()
                })

        except Exception as e:
            logger.error(f"Failed to generate security alerts: {str(e)}")

        return alerts

    async def _invalidate_card_caches(self, card_ids: List[Union[int, str, UUID]]) -> None:
        """Invalidate caches related to specific cards."""
        try:
            for card_id in card_ids:
                cache_patterns = [
                    f"card_security_analysis:{card_id}:*",
                    f"card_fraud_analysis:{card_id}:*",
                    f"card_usage_analysis:{card_id}:*",
                    f"card_security_monitoring:{card_id}"
                ]
                
                # Clear related caches
                for pattern in cache_patterns:
                    await self.cache_manager.delete(pattern)

        except Exception as e:
            logger.error(f"Failed to invalidate card caches: {str(e)}") 