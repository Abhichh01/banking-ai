"""
Enhanced Account Repository with AI integration and financial analysis.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account, AccountType, AccountStatus
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.repositories.enhanced_base import AIEnhancedRepository
from app.schemas.account import AccountCreate, AccountUpdate
from app.core.llm_orchestrator import TaskType, TaskComplexity
# Exception imports removed for MVP
# All custom exceptions replaced with standard logging

logger = logging.getLogger(__name__)


class EnhancedAccountRepository(AIEnhancedRepository[Account, AccountCreate, AccountUpdate]):
    """
    Enhanced account repository with AI integration and financial analysis.
    
    Features:
    - Account balance analysis
    - Transaction pattern analysis
    - Financial health assessment
    - Account performance metrics
    """

    def __init__(
        self,
        db_session: AsyncSession,
        llm_orchestrator=None,
        cache_manager=None
    ):
        super().__init__(Account, db_session, llm_orchestrator, cache_manager)

    # ==================== Enhanced CRUD Operations ====================

    async def get_by_account_number(
        self,
        account_number: str,
        include_inactive: bool = False,
        load_relationships: bool = True,
        use_cache: bool = True
    ) -> Optional[Account]:
        """Get an account by account number with caching."""
        cache_key = f"account_number:{account_number}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Account).where(Account.account_number == account_number)

        if not include_inactive:
            query = query.where(Account.is_active == True)  # noqa: E712

        if load_relationships:
            query = query.options(
                selectinload(Account.user),
                selectinload(Account.transactions)
            )

        result = await self.db_session.execute(query)
        account = result.scalars().first()

        if account and use_cache:
            await self.cache_manager.set(cache_key, account, ttl=1800)  # 30 minutes

        return account

    async def get_user_accounts(
        self,
        user_id: int,
        account_type: Optional[AccountType] = None,
        status: Optional[AccountStatus] = None,
        include_inactive: bool = False,
        use_cache: bool = True
    ) -> List[Account]:
        """Get all accounts for a user with filtering."""
        cache_key = f"user_accounts:{user_id}:{account_type.value if account_type else 'all'}:{status.value if status else 'all'}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Account).where(Account.user_id == user_id)

        if account_type:
            query = query.where(Account.account_type == account_type)
        if status:
            query = query.where(Account.status == status)
        if not include_inactive:
            query = query.where(Account.is_active == True)  # noqa: E712

        query = query.options(selectinload(Account.transactions))

        result = await self.db_session.execute(query)
        accounts = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, accounts, ttl=900)  # 15 minutes

        return accounts

    async def get_account_with_transactions(
        self,
        account_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_inactive: bool = False,
        use_cache: bool = True
    ) -> Optional[Account]:
        """Get account with recent transactions."""
        cache_key = f"account_with_transactions:{account_id}:{start_date}:{end_date}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Account).where(Account.id == account_id)

        if not include_inactive:
            query = query.where(Account.is_active == True)  # noqa: E712

        query = query.options(
            selectinload(Account.transactions),
            selectinload(Account.user)
        )

        result = await self.db_session.execute(query)
        account = result.scalars().first()

        if account and use_cache:
            await self.cache_manager.set(cache_key, account, ttl=900)  # 15 minutes

        return account

    # ==================== AI Integration Methods ====================

    async def analyze_account_health(
        self,
        account_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Analyze account financial health using AI."""
        try:
            # Get account data
            account_data = await self._get_account_data_for_analysis(account_id, "health", time_range)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                account_data,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Account health analysis failed: {str(e)}")
            return {}

    async def generate_account_recommendations(
        self,
        account_id: int,
        recommendation_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate personalized recommendations for account."""
        try:
            # Get account data
            account_data = await self._get_account_data_for_analysis(account_id, "recommendation")

            # Generate AI recommendations
            recommendations = await self.analyze_with_ai(
                account_data,
                TaskType.FINANCIAL_RECOMMENDATION,
                TaskComplexity.HIGH
            )

            return recommendations

        except Exception as e:
            logger.error(f"Account recommendation generation failed: {str(e)}")
            return {}

    # ==================== Advanced Analytics Methods ====================

    async def get_account_analytics(
        self,
        account_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for an account."""
        cache_key = f"account_analytics:{account_id}:{time_range}"
        
        try:
            # Get account
            account = await self.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return {}

            # Get account transactions
            transactions = await self._get_account_transactions(account_id, time_range)

            # Calculate financial metrics
            financial_metrics = await self._calculate_financial_metrics(transactions, account)

            # Analyze transaction patterns
            transaction_analysis = await self._analyze_transaction_patterns(transactions)

            # Generate AI insights
            ai_insights = await self.analyze_account_health(account_id, time_range)

            analytics_result = {
                "account_id": account_id,
                "time_range": time_range,
                "account_info": {
                    "account_number": account.account_number,
                    "account_type": account.account_type.value,
                    "status": account.status.value,
                    "balance": float(account.balance),
                    "currency": account.currency
                },
                "financial_metrics": financial_metrics,
                "transaction_analysis": transaction_analysis,
                "ai_insights": ai_insights,
                "generated_at": datetime.utcnow().isoformat()
            }

            # Cache the result
            await self.cache_manager.set(cache_key, analytics_result, ttl=3600)  # 1 hour

            return analytics_result
        except Exception as e:
            logger.error(f"Account analytics failed: {str(e)}")
            return {}

    async def get_account_performance(
        self,
        account_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Get account performance metrics."""
        try:
            # Get account analytics
            analytics = await self.get_account_analytics(account_id, time_range)

            # Calculate performance metrics
            performance_metrics = await self._calculate_performance_metrics(analytics)

            return {
                "account_id": account_id,
                "time_range": time_range,
                "performance_metrics": performance_metrics,
                "recommendations": analytics.get("ai_insights", {}).get("recommendations", [])
            }

        except Exception as e:
            logger.error(f"Account performance analysis failed: {str(e)}")
            return None

    async def get_account_balance_history(
        self,
        account_id: int,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get account balance history."""
        try:
            # Get account transactions
            transactions = await self._get_account_transactions(account_id, f"{days}d")

            # Calculate balance history
            balance_history = await self._calculate_balance_history(transactions, account_id)

            return balance_history

        except Exception as e:
            logger.error(f"Account balance history failed: {str(e)}")
            return None

    # ==================== Implementation of Abstract Methods ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for AI analysis (for account context)."""
        try:
            # Get user profile
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db_session.execute(user_query)
            user = user_result.scalar_one_or_none()

            # Get user accounts
            accounts = await self.get_user_accounts(user_id)

            # Get user transactions
            transactions = await self._get_user_transactions(user_id, time_range or "30d")

            return {
                "user_profile": user.to_dict() if user else {},
                "accounts": [account.to_dict() for account in accounts],
                "transactions": transactions,
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
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db_session.execute(user_query)
            user = user_result.scalar_one_or_none()

            # Get recent transactions
            recent_transactions = await self._get_user_transactions(user_id, "30d")

            # Get account balances
            accounts = await self.get_user_accounts(user_id)

            return {
                "user_profile": user.to_dict() if user else {},
                "recent_transactions": recent_transactions,
                "account_balances": [account.to_dict() for account in accounts],
                "risk_indicators": await self._calculate_account_risk_indicators(user_id)
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

    # ==================== Account-Specific Methods ====================

    async def _get_account_data_for_analysis(
        self,
        account_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get account data for AI analysis."""
        try:
            # Get account
            account = await self.get_by_id(account_id)
            if not account:
                logger.error(f"Account {account_id} not found")
                return None

            # Get account transactions
            transactions = await self._get_account_transactions(account_id, time_range or "30d")

            # Get user data
            user_data = await self._get_user_data_for_analysis(account.user_id, data_type, time_range)

            return {
                "account_profile": account.to_dict(),
                "transactions": transactions,
                "user_data": user_data,
                "data_type": data_type,
                "time_range": time_range
            }

        except Exception as e:
            logger.error(f"Failed to get account data for analysis: {str(e)}")
            raise

    async def _get_account_transactions(
        self,
        account_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get account transactions for analysis."""
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
                .where(Transaction.account_id == account_id)
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
            logger.error(f"Failed to get account transactions: {str(e)}")
            raise

    async def _calculate_financial_metrics(
        self,
        transactions: List[Dict[str, Any]],
        account: Account
    ) -> Dict[str, Any]:
        """Calculate financial metrics for account."""
        try:
            if not transactions:
                return {
                    "total_income": 0.0,
                    "total_expenses": 0.0,
                    "net_flow": 0.0,
                    "transaction_count": 0,
                    "average_transaction": 0.0
                }

            # Calculate income and expenses
            income = sum(float(t.get("amount", 0)) for t in transactions if t.get("transaction_type") == "CREDIT")
            expenses = sum(float(t.get("amount", 0)) for t in transactions if t.get("transaction_type") == "DEBIT")
            net_flow = income - expenses

            # Calculate averages
            total_amount = sum(float(t.get("amount", 0)) for t in transactions)
            avg_transaction = total_amount / len(transactions) if transactions else 0

            return {
                "total_income": income,
                "total_expenses": expenses,
                "net_flow": net_flow,
                "transaction_count": len(transactions),
                "average_transaction": avg_transaction,
                "current_balance": float(account.balance)
            }

        except Exception as e:
            logger.error(f"Failed to calculate financial metrics: {str(e)}")
            raise

    async def _analyze_transaction_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze transaction patterns for account."""
        try:
            if not transactions:
                return {}

            # Analyze spending patterns
            spending_analysis = await self._analyze_spending_patterns(transactions)

            # Analyze temporal patterns
            temporal_analysis = await self._analyze_temporal_patterns(transactions)

            # Analyze geographic patterns
            geographic_analysis = await self._analyze_geographic_patterns(transactions)

            return {
                "spending_analysis": spending_analysis,
                "temporal_analysis": temporal_analysis,
                "geographic_analysis": geographic_analysis
            }

        except Exception as e:
            logger.error(f"Failed to analyze transaction patterns: {str(e)}")
            raise

    async def _calculate_performance_metrics(
        self,
        analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate performance metrics for account."""
        try:
            financial_metrics = analytics.get("financial_metrics", {})
            transaction_analysis = analytics.get("transaction_analysis", {})

            # Calculate performance indicators
            net_flow = financial_metrics.get("net_flow", 0)
            transaction_count = financial_metrics.get("transaction_count", 0)
            avg_transaction = financial_metrics.get("average_transaction", 0)

            # Performance score (0-100)
            performance_score = 0
            if net_flow > 0:
                performance_score += 40  # Positive cash flow
            if transaction_count > 10:
                performance_score += 30  # Active account
            if avg_transaction > 100:
                performance_score += 30  # Good transaction value

            return {
                "performance_score": min(performance_score, 100),
                "cash_flow_health": "positive" if net_flow > 0 else "negative",
                "activity_level": "high" if transaction_count > 20 else "medium" if transaction_count > 10 else "low",
                "transaction_value": "high" if avg_transaction > 200 else "medium" if avg_transaction > 100 else "low"
            }

        except Exception as e:
            logger.error(f"Failed to calculate performance metrics: {str(e)}")
            raise

    async def _calculate_balance_history(
        self,
        transactions: List[Dict[str, Any]],
        account_id: int
    ) -> List[Dict[str, Any]]:
        """Calculate balance history for account."""
        try:
            if not transactions:
                return []

            # Sort transactions by date
            sorted_transactions = sorted(transactions, key=lambda x: x.get("transaction_date", ""))
            
            balance_history = []
            running_balance = 0.0

            for transaction in sorted_transactions:
                amount = float(transaction.get("amount", 0))
                transaction_type = transaction.get("transaction_type")
                
                if transaction_type == "CREDIT":
                    running_balance += amount
                elif transaction_type == "DEBIT":
                    running_balance -= amount

                balance_history.append({
                    "date": transaction.get("transaction_date"),
                    "balance": running_balance,
                    "transaction_amount": amount,
                    "transaction_type": transaction_type
                })

            return balance_history

        except Exception as e:
            logger.error(f"Failed to calculate balance history: {str(e)}")
            raise

    async def _calculate_account_risk_indicators(self, user_id: int) -> Dict[str, Any]:
        """Calculate risk indicators for account."""
        try:
            # Get user accounts
            accounts = await self.get_user_accounts(user_id)

            risk_indicators = {
                "negative_balance_accounts": 0,
                "low_balance_accounts": 0,
                "inactive_accounts": 0
            }

            for account in accounts:
                balance = float(account.balance)
                
                if balance < 0:
                    risk_indicators["negative_balance_accounts"] += 1
                elif balance < 100:  # Low balance threshold
                    risk_indicators["low_balance_accounts"] += 1

                # Check for inactive accounts (no transactions in last 30 days)
                recent_transactions = await self._get_account_transactions(account.id, "30d")
                if not recent_transactions:
                    risk_indicators["inactive_accounts"] += 1

            return risk_indicators

        except Exception as e:
            logger.error(f"Failed to calculate account risk indicators: {str(e)}")
            raise 