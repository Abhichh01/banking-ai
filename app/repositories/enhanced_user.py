"""
Enhanced User Repository with AI integration and behavioral analysis.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from uuid import UUID

from sqlalchemy import and_, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.behavioral_pattern import BehavioralPattern
from app.repositories.enhanced_base import AIEnhancedRepository
from app.schemas.user import UserCreate, UserUpdate
from app.core.llm_orchestrator import TaskType, TaskComplexity
from app.core.exceptions import RepositoryError, AIAnalysisError

logger = logging.getLogger(__name__)


class EnhancedUserRepository(AIEnhancedRepository[User, UserCreate, UserUpdate]):
    """
    Enhanced user repository with AI integration and behavioral analysis.
    
    Features:
    - User profile analysis
    - Behavioral pattern detection
    - Risk assessment
    - Customer segmentation
    """

    def __init__(
        self,
        db_session: AsyncSession,
        llm_orchestrator=None,
        cache_manager=None
    ):
        super().__init__(User, db_session, llm_orchestrator, cache_manager)

    # ==================== Enhanced CRUD Operations ====================

    async def get_by_email(
        self,
        email: str,
        include_inactive: bool = False,
        load_relationships: bool = True,
        use_cache: bool = True
    ) -> Optional[User]:
        """Get a user by email with caching."""
        cache_key = f"user_email:{email}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(User).where(User.email == email)

        if not include_inactive:
            query = query.where(User.is_active == True)  # noqa: E712

        if load_relationships:
            query = query.options(
                selectinload(User.accounts),
                selectinload(User.cards)
            )

        result = await self.db_session.execute(query)
        user = result.scalars().first()

        if user and use_cache:
            await self.cache_manager.set(cache_key, user, ttl=1800)  # 30 minutes

        return user

    async def get_by_customer_number(
        self,
        customer_number: str,
        include_inactive: bool = False,
        load_relationships: bool = True,
        use_cache: bool = True
    ) -> Optional[User]:
        """Get a user by customer number with caching."""
        cache_key = f"user_customer:{customer_number}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(User).where(User.customer_number == customer_number)

        if not include_inactive:
            query = query.where(User.is_active == True)  # noqa: E712

        if load_relationships:
            query = query.options(
                selectinload(User.accounts),
                selectinload(User.cards)
            )

        result = await self.db_session.execute(query)
        user = result.scalars().first()

        if user and use_cache:
            await self.cache_manager.set(cache_key, user, ttl=1800)  # 30 minutes

        return user

    async def get_with_accounts(
        self,
        user_id: int,
        include_inactive: bool = False,
        use_cache: bool = True
    ) -> Optional[User]:
        """Get user with all accounts loaded."""
        cache_key = f"user_with_accounts:{user_id}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(User).where(User.id == user_id)

        if not include_inactive:
            query = query.where(User.is_active == True)  # noqa: E712

        query = query.options(selectinload(User.accounts))

        result = await self.db_session.execute(query)
        user = result.scalars().first()

        if user and use_cache:
            await self.cache_manager.set(cache_key, user, ttl=900)  # 15 minutes

        return user

    async def get_with_cards(
        self,
        user_id: int,
        include_inactive: bool = False,
        use_cache: bool = True
    ) -> Optional[User]:
        """Get user with all cards loaded."""
        cache_key = f"user_with_cards:{user_id}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(User).where(User.id == user_id)

        if not include_inactive:
            query = query.where(User.is_active == True)  # noqa: E712

        query = query.options(selectinload(User.cards))

        result = await self.db_session.execute(query)
        user = result.scalars().first()

        if user and use_cache:
            await self.cache_manager.set(cache_key, user, ttl=900)  # 15 minutes

        return user

    # ==================== AI Integration Methods ====================

    async def analyze_user_behavior(
        self,
        user_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Analyze user behavior using AI."""
        try:
            # Get user data
            user_data = await self._get_user_data_for_analysis(user_id, "behavioral", time_range)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                user_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.HIGH
            )

            return analysis_result

        except Exception as e:
            logger.error(f"User behavior analysis failed: {str(e)}")
            raise AIAnalysisError(f"User behavior analysis failed: {str(e)}")

    async def assess_user_risk(
        self,
        user_id: int,
        assessment_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Assess user risk profile."""
        try:
            # Get user risk data
            user_data = await self._get_user_risk_data(user_id)

            # Perform risk assessment
            risk_assessment = await self.get_risk_assessment(user_id, assessment_type)

            return risk_assessment

        except Exception as e:
            logger.error(f"User risk assessment failed: {str(e)}")
            raise AIAnalysisError(f"User risk assessment failed: {str(e)}")

    async def generate_user_recommendations(
        self,
        user_id: int,
        recommendation_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate personalized recommendations for user."""
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
            logger.error(f"User recommendation generation failed: {str(e)}")
            raise AIAnalysisError(f"User recommendation generation failed: {str(e)}")

    # ==================== Advanced Analytics Methods ====================

    async def get_user_analytics(
        self,
        user_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive user analytics."""
        cache_key = f"user_analytics:{user_id}:{time_range}"

        # Check cache first
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return cached

        try:
            # Get user profile
            user = await self.get_by_id(user_id)
            if not user:
                raise RepositoryError(f"User {user_id} not found")

            # Get user transactions
            transactions = await self._get_user_transactions(user_id, time_range)

            # Get account balances
            accounts_query = select(Account).where(Account.user_id == user_id)
            accounts_result = await self.db_session.execute(accounts_query)
            accounts = accounts_result.scalars().all()

            # Calculate basic metrics
            total_balance = sum(float(account.balance) for account in accounts)
            total_transactions = len(transactions)
            total_spending = sum(float(t.get("amount", 0)) for t in transactions if t.get("transaction_type") == "DEBIT")

            # Generate AI insights
            ai_insights = await self.analyze_user_behavior(user_id, time_range)

            analytics_result = {
                "user_id": user_id,
                "time_range": time_range,
                "profile": {
                    "customer_number": user.customer_number,
                    "name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "risk_profile": user.risk_profile,
                    "customer_segment": user.customer_segment
                },
                "financial_summary": {
                    "total_balance": total_balance,
                    "total_transactions": total_transactions,
                    "total_spending": total_spending,
                    "account_count": len(accounts)
                },
                "ai_insights": ai_insights,
                "generated_at": datetime.utcnow().isoformat()
            }

            # Cache the result
            await self.cache_manager.set(cache_key, analytics_result, ttl=3600)  # 1 hour

            return analytics_result

        except Exception as e:
            logger.error(f"User analytics failed: {str(e)}")
            raise RepositoryError(f"User analytics failed: {str(e)}")

    async def get_customer_segmentation(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """Get customer segmentation analysis."""
        try:
            # Get user analytics
            analytics = await self.get_user_analytics(user_id)

            # Determine segment based on behavior
            segment = await self._determine_customer_segment(analytics)

            return {
                "user_id": user_id,
                "current_segment": segment,
                "segment_factors": analytics.get("ai_insights", {}).get("segment_factors", []),
                "upgrade_potential": analytics.get("ai_insights", {}).get("upgrade_potential", False)
            }

        except Exception as e:
            logger.error(f"Customer segmentation failed: {str(e)}")
            raise RepositoryError(f"Customer segmentation failed: {str(e)}")

    # ==================== Implementation of Abstract Methods ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for AI analysis."""
        try:
            # Get user profile
            user = await self.get_by_id(user_id)
            if not user:
                raise RepositoryError(f"User {user_id} not found")

            # Get user transactions
            transactions = await self._get_user_transactions(user_id, time_range or "30d")

            # Get account information
            accounts_query = select(Account).where(Account.user_id == user_id)
            accounts_result = await self.db_session.execute(accounts_query)
            accounts = accounts_result.scalars().all()

            # Get behavioral patterns
            patterns_query = select(BehavioralPattern).where(BehavioralPattern.user_id == user_id)
            patterns_result = await self.db_session.execute(patterns_query)
            patterns = patterns_result.scalars().all()

            return {
                "user_profile": user.to_dict(),
                "accounts": [account.to_dict() for account in accounts],
                "transactions": transactions,
                "behavioral_patterns": [pattern.to_dict() for pattern in patterns],
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
            # Calculate date range
            end_date = datetime.now()
            if time_range == "7d":
                start_date = end_date - timedelta(days=7)
            elif time_range == "30d":
                start_date = end_date - timedelta(days=30)
            elif time_range == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)  # Default to 30 days

            # Query transactions
            query = (
                select(Transaction)
                .where(Transaction.user_id == user_id)
                .where(Transaction.transaction_date >= start_date)
                .where(Transaction.transaction_date <= end_date)
                .where(Transaction.is_active == True)  # noqa: E712
                .order_by(desc(Transaction.transaction_date))
            )

            result = await self.db_session.execute(query)
            transactions = result.scalars().all()

            # Convert to dictionaries
            return [transaction.to_dict() for transaction in transactions]

        except Exception as e:
            logger.error(f"Failed to get user transactions: {str(e)}")
            raise

    async def _get_user_risk_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data for risk assessment."""
        try:
            # Get user profile
            user = await self.get_by_id(user_id)
            if not user:
                raise RepositoryError(f"User {user_id} not found")

            # Get recent transactions
            recent_transactions = await self._get_user_transactions(user_id, "30d")

            # Get account balances
            accounts_query = select(Account).where(Account.user_id == user_id)
            accounts_result = await self.db_session.execute(accounts_query)
            accounts = accounts_result.scalars().all()

            # Get behavioral patterns
            patterns_query = select(BehavioralPattern).where(BehavioralPattern.user_id == user_id)
            patterns_result = await self.db_session.execute(patterns_query)
            patterns = patterns_result.scalars().all()

            return {
                "user_profile": user.to_dict(),
                "recent_transactions": recent_transactions,
                "account_balances": [account.to_dict() for account in accounts],
                "behavioral_patterns": [pattern.to_dict() for pattern in patterns],
                "risk_indicators": await self._calculate_user_risk_indicators(user_id)
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

            # Analyze transaction patterns
            transactions = user_data.get("recent_transactions", [])
            if transactions:
                # Check for unusual spending patterns
                amounts = [float(t.get("amount", 0)) for t in transactions]
                avg_amount = sum(amounts) / len(amounts) if amounts else 0
                max_amount = max(amounts) if amounts else 0

                if max_amount > avg_amount * 3:  # Unusually high transaction
                    risk_factors.append({
                        "type": "high_value_transaction",
                        "description": f"Transaction amount {max_amount} is significantly higher than average {avg_amount}",
                        "risk_score": 0.3
                    })
                    overall_risk_score += 0.3

            # Check account balances
            accounts = user_data.get("account_balances", [])
            for account in accounts:
                balance = float(account.get("balance", 0))
                if balance < 0:  # Negative balance
                    risk_factors.append({
                        "type": "negative_balance",
                        "description": f"Account {account.get('account_number')} has negative balance",
                        "risk_score": 0.5
                    })
                    overall_risk_score += 0.5

            return {
                "overall_risk_score": min(overall_risk_score, 1.0),
                "risk_factors": risk_factors,
                "assessment_type": assessment_type
            }

        except Exception as e:
            logger.error(f"Failed to perform risk analysis: {str(e)}")
            raise

    # ==================== Helper Methods ====================

    async def _calculate_user_risk_indicators(self, user_id: int) -> Dict[str, Any]:
        """Calculate risk indicators for a user."""
        try:
            # Get recent transactions
            recent_transactions = await self._get_user_transactions(user_id, "30d")

            risk_indicators = {
                "high_value_transactions": 0,
                "international_transactions": 0,
                "unusual_times": 0,
                "multiple_locations": 0
            }

            if recent_transactions:
                amounts = [float(t.get("amount", 0)) for t in recent_transactions]
                avg_amount = sum(amounts) / len(amounts)
                
                for transaction in recent_transactions:
                    # High value transactions
                    if float(transaction.get("amount", 0)) > avg_amount * 2:
                        risk_indicators["high_value_transactions"] += 1
                    
                    # International transactions
                    if transaction.get("is_international", False):
                        risk_indicators["international_transactions"] += 1
                    
                    # Unusual times (between 10 PM and 6 AM)
                    transaction_date = transaction.get("transaction_date")
                    if transaction_date:
                        hour = datetime.fromisoformat(transaction_date).hour
                        if hour >= 22 or hour <= 6:
                            risk_indicators["unusual_times"] += 1
                
                # Multiple locations
                locations = set()
                for transaction in recent_transactions:
                    location = transaction.get("location_city", "Unknown")
                    locations.add(location)
                risk_indicators["multiple_locations"] = len(locations)

            return risk_indicators

        except Exception as e:
            logger.error(f"Failed to calculate risk indicators: {str(e)}")
            raise

    async def _determine_customer_segment(self, analytics: Dict[str, Any]) -> str:
        """Determine customer segment based on analytics."""
        try:
            financial_summary = analytics.get("financial_summary", {})
            total_balance = financial_summary.get("total_balance", 0)
            total_spending = financial_summary.get("total_spending", 0)
            transaction_count = financial_summary.get("total_transactions", 0)

            # Simple segmentation logic
            if total_balance > 100000 or total_spending > 50000:
                return "Premium"
            elif total_balance > 10000 or total_spending > 10000:
                return "Retail"
            elif transaction_count > 50:
                return "Active"
            else:
                return "Basic"

        except Exception as e:
            logger.error(f"Failed to determine customer segment: {str(e)}")
            return "Basic" 