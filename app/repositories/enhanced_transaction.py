"""
Enhanced Transaction Repository with AI integration and advanced analytics.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple, Union
from uuid import UUID

from sqlalchemy import and_, or_, func, select, text, update, case, between, desc, asc
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.transaction import (
    Transaction, 
    TransactionType, 
    TransactionStatus,
    TransactionCategory,
    Merchant
)
from app.models.account import Account
from app.models.card import Card
from app.models.user import User
from app.repositories.enhanced_base import AIEnhancedRepository
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionFilter,
    TransactionSummary
)
from app.core.exceptions import (
    InsufficientFundsError,
    TransactionLimitExceeded,
    TransactionValidationError,
    FraudDetectionError,
    AIAnalysisError
)
from app.core.utils import generate_reference_id
from app.core.llm_orchestrator import TaskType, TaskComplexity

logger = logging.getLogger(__name__)


class EnhancedTransactionRepository(AIEnhancedRepository[Transaction, TransactionCreate, TransactionUpdate]):
    """
    Enhanced transaction repository with AI integration and advanced analytics.
    
    Features:
    - AI-powered fraud detection
    - Behavioral pattern analysis
    - Real-time risk assessment
    - Advanced transaction analytics
    - Intelligent caching
    """
    
    def __init__(
        self, 
        db_session: AsyncSession,
        llm_orchestrator=None,
        cache_manager=None
    ):
        super().__init__(Transaction, db_session, llm_orchestrator, cache_manager)
    
    # ==================== Enhanced CRUD Operations ====================
    
    async def get_by_reference_id(
        self, 
        reference_id: str,
        include_inactive: bool = False,
        load_relationships: bool = True,
        use_cache: bool = True
    ) -> Optional[Transaction]:
        """Get a transaction by its reference ID with caching."""
        cache_key = f"transaction_ref:{reference_id}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached
        
        query = select(Transaction).where(Transaction.reference_id == reference_id)
        
        if not include_inactive:
            query = query.where(Transaction.is_active == True)  # noqa: E712
            
        if load_relationships:
            query = query.options(
                selectinload(Transaction.account),
                selectinload(Transaction.merchant),
                selectinload(Transaction.card)
            )
            
        result = await self.db_session.execute(query)
        transaction = result.scalars().first()
        
        if transaction and use_cache:
            await self.cache_manager.set(cache_key, transaction, ttl=1800)  # 30 minutes
            
        return transaction

    async def get_account_transactions(
        self,
        account_id: int,
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        category: Optional[TransactionCategory] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        reference: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        use_cache: bool = True
    ) -> Tuple[List[Transaction], int]:
        """Get transactions for a specific account with advanced filtering and caching."""
        # Create cache key based on all parameters
        cache_params = {
            "account_id": account_id,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "transaction_type": transaction_type.value if transaction_type else None,
            "status": status.value if status else None,
            "category": category.value if category else None,
            "min_amount": str(min_amount) if min_amount else None,
            "max_amount": str(max_amount) if max_amount else None,
            "reference": reference,
            "skip": skip,
            "limit": limit
        }
        cache_key = f"account_transactions:{json.dumps(cache_params, sort_keys=True)}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached
        
        query = select(Transaction).where(Transaction.account_id == account_id)
        
        # Apply date filters
        if start_date:
            query = query.where(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.where(Transaction.transaction_date <= end_date)
            
        # Apply other filters
        if transaction_type:
            query = query.where(Transaction.transaction_type == transaction_type)
        if status:
            query = query.where(Transaction.status == status)
        if category:
            query = query.where(Transaction.transaction_category == category)
        if min_amount:
            query = query.where(Transaction.amount >= min_amount)
        if max_amount:
            query = query.where(Transaction.amount <= max_amount)
        if reference:
            query = query.where(Transaction.reference_id.contains(reference))
            
        # Handle soft delete
        if not include_inactive:
            query = query.where(Transaction.is_active == True)  # noqa: E712
            
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db_session.execute(count_query)
        total_count = count_result.scalar()
        
        # Apply pagination and ordering
        query = query.order_by(desc(Transaction.transaction_date))
        query = query.offset(skip).limit(limit)
        
        result = await self.db_session.execute(query)
        transactions = result.scalars().all()
        
        result_tuple = (transactions, total_count)
        
        if use_cache:
            await self.cache_manager.set(cache_key, result_tuple, ttl=900)  # 15 minutes
            
        return result_tuple

    async def create_transaction(
        self, 
        obj_in: TransactionCreate,
        *,
        commit: bool = True,
        perform_ai_analysis: bool = True
    ) -> Transaction:
        """Create a new transaction with AI analysis and fraud detection."""
        try:
            # Generate reference ID if not provided
            if not obj_in.reference_id:
                obj_in.reference_id = generate_reference_id()
            
            # Validate account balance
            await self._validate_account_balance(obj_in)
            
            # Create transaction
            transaction = await self.create(obj_in)
            
            # Perform AI analysis if requested
            if perform_ai_analysis:
                await self._perform_transaction_ai_analysis(transaction)
            
            # Update account balance
            await self._update_account_balance(transaction)
            
            if commit:
                await self.db_session.commit()
            
            return transaction
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create transaction: {str(e)}")
            raise

    # ==================== AI Integration Methods ====================
    
    async def analyze_transaction_with_ai(
        self, 
        transaction: Transaction,
        analysis_type: TaskType = TaskType.RISK_ASSESSMENT
    ) -> Dict[str, Any]:
        """Analyze a transaction using AI for fraud detection and risk assessment."""
        try:
            # Prepare transaction data for AI analysis
            transaction_data = await self._prepare_transaction_data_for_ai(transaction)
            
            # Perform AI analysis
            analysis_result = await self.analyze_with_ai(
                transaction_data, 
                analysis_type,
                TaskComplexity.HIGH
            )
            
            # Update transaction with AI insights
            await self._update_transaction_with_ai_insights(transaction, analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI analysis failed for transaction {transaction.id}: {str(e)}")
            raise AIAnalysisError(f"Transaction AI analysis failed: {str(e)}")

    async def detect_fraud_patterns(
        self, 
        user_id: int,
        time_range: str = "30d"
    ) -> List[Dict[str, Any]]:
        """Detect fraud patterns in user transactions using AI."""
        try:
            # Get user transactions
            transactions = await self._get_user_transactions(user_id, time_range)
            
            if not transactions:
                return []
            
            # Detect anomalies using AI
            anomalies = await self.detect_anomalies(transactions, threshold=0.8)
            
            # Filter fraud-related anomalies
            fraud_patterns = [
                anomaly for anomaly in anomalies
                if anomaly.get("type") in ["spending", "geographic", "temporal", "amount"]
                and anomaly.get("severity") in ["medium", "high"]
            ]
            
            return fraud_patterns
            
        except Exception as e:
            logger.error(f"Fraud pattern detection failed for user {user_id}: {str(e)}")
            raise FraudDetectionError(f"Fraud pattern detection failed: {str(e)}")

    async def assess_transaction_risk(
        self, 
        transaction: Transaction
    ) -> Dict[str, Any]:
        """Assess risk for a specific transaction."""
        try:
            # Get transaction context
            context_data = await self._get_transaction_context(transaction)
            
            # Perform risk assessment
            risk_assessment = await self.analyze_with_ai(
                context_data,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )
            
            # Update transaction risk score
            risk_score = risk_assessment.get("risk_score", 0.0)
            await self._update_transaction_risk_score(transaction, risk_score)
            
            return risk_assessment
            
        except Exception as e:
            logger.error(f"Risk assessment failed for transaction {transaction.id}: {str(e)}")
            raise

    # ==================== Advanced Analytics Methods ====================
    
    async def get_transaction_analytics(
        self,
        user_id: int,
        time_range: str = "30d",
        group_by: str = "category"
    ) -> Dict[str, Any]:
        """Get comprehensive transaction analytics for a user."""
        cache_key = f"transaction_analytics:{user_id}:{time_range}:{group_by}"
        
        # Check cache first
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            # Get user transactions
            transactions = await self._get_user_transactions(user_id, time_range)
            
            if not transactions:
                return {
                    "user_id": user_id,
                    "time_range": time_range,
                    "total_transactions": 0,
                    "total_amount": 0.0,
                    "analytics": {}
                }
            
            # Calculate basic metrics
            total_transactions = len(transactions)
            total_amount = sum(t.get("amount", 0) for t in transactions)
            
            # Group transactions
            grouped_data = await self._group_transactions(transactions, group_by)
            
            # Generate AI insights
            ai_insights = await self.generate_insights(user_id, "transaction", time_range)
            
            analytics_result = {
                "user_id": user_id,
                "time_range": time_range,
                "total_transactions": total_transactions,
                "total_amount": float(total_amount),
                "grouped_data": grouped_data,
                "ai_insights": ai_insights,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            await self.cache_manager.set(cache_key, analytics_result, ttl=3600)  # 1 hour
            
            return analytics_result
            
        except Exception as e:
            logger.error(f"Transaction analytics failed for user {user_id}: {str(e)}")
            raise

    async def get_spending_patterns(
        self,
        user_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Analyze spending patterns for a user."""
        try:
            # Get user transactions
            transactions = await self._get_user_transactions(user_id, time_range)
            
            if not transactions:
                return {
                    "user_id": user_id,
                    "time_range": time_range,
                    "patterns": {},
                    "insights": []
                }
            
            # Analyze spending patterns
            spending_analysis = await self._analyze_spending_patterns(transactions)
            
            # Generate AI insights
            ai_insights = await self.generate_insights(user_id, "spending", time_range)
            
            return {
                "user_id": user_id,
                "time_range": time_range,
                "patterns": spending_analysis,
                "ai_insights": ai_insights,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Spending pattern analysis failed for user {user_id}: {str(e)}")
            raise

    # ==================== Performance Optimization Methods ====================
    
    async def bulk_create_transactions(
        self, 
        transactions: List[TransactionCreate],
        batch_size: int = 1000,
        perform_ai_analysis: bool = False
    ) -> List[Transaction]:
        """Bulk create transactions with optional AI analysis."""
        created_transactions = []
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            
            # Create transactions in batch
            batch_objects = [Transaction(**t.dict()) for t in batch]
            self.db_session.add_all(batch_objects)
            await self.db_session.commit()
            
            # Refresh objects to get IDs
            for obj in batch_objects:
                await self.db_session.refresh(obj)
            
            # Perform AI analysis if requested
            if perform_ai_analysis:
                for transaction in batch_objects:
                    await self._perform_transaction_ai_analysis(transaction)
            
            created_transactions.extend(batch_objects)
        
        # Invalidate caches
        await self._invalidate_related_caches()
        
        return created_transactions

    # ==================== Implementation of Abstract Methods ====================
    
    async def _get_user_data_for_analysis(
        self, 
        user_id: int, 
        data_type: str, 
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for AI analysis."""
        try:
            # Get user transactions
            transactions = await self._get_user_transactions(user_id, time_range or "30d")
            
            # Get user profile
            user_query = select(User).where(User.id == user_id)
            user_result = await self.db_session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            # Get account information
            accounts_query = select(Account).where(Account.user_id == user_id)
            accounts_result = await self.db_session.execute(accounts_query)
            accounts = accounts_result.scalars().all()
            
            return {
                "user": user.to_dict() if user else {},
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
            accounts_query = select(Account).where(Account.user_id == user_id)
            accounts_result = await self.db_session.execute(accounts_query)
            accounts = accounts_result.scalars().all()
            
            return {
                "user_profile": user.to_dict() if user else {},
                "recent_transactions": recent_transactions,
                "account_balances": [account.to_dict() for account in accounts],
                "risk_indicators": await self._calculate_risk_indicators(user_id)
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
    
    async def _validate_account_balance(self, transaction: TransactionCreate) -> None:
        """Validate that account has sufficient balance for transaction."""
        if transaction.transaction_type == TransactionType.DEBIT:
            account_query = select(Account).where(Account.id == transaction.account_id)
            account_result = await self.db_session.execute(account_query)
            account = account_result.scalar_one_or_none()
            
            if account and float(account.balance) < float(transaction.amount):
                raise InsufficientFundsError(
                    f"Insufficient funds in account {account.account_number}",
                    account_id=account.account_number,
                    required_amount=float(transaction.amount)
                )

    async def _update_account_balance(self, transaction: Transaction) -> None:
        """Update account balance after transaction."""
        if transaction.account_id:
            account_query = select(Account).where(Account.id == transaction.account_id)
            account_result = await self.db_session.execute(account_query)
            account = account_result.scalar_one_or_none()
            
            if account:
                if transaction.transaction_type == TransactionType.DEBIT:
                    account.balance -= transaction.amount
                else:
                    account.balance += transaction.amount
                
                await self.db_session.commit()

    async def _perform_transaction_ai_analysis(self, transaction: Transaction) -> None:
        """Perform AI analysis on a transaction."""
        try:
            analysis_result = await self.analyze_transaction_with_ai(transaction)
            
            # Update transaction with AI insights
            if analysis_result:
                transaction.risk_score = analysis_result.get("risk_score", 0.0)
                transaction.tags = analysis_result.get("tags", {})
                
                # Check for fraud flags
                if analysis_result.get("fraud_detected", False):
                    transaction.fraud_flag = True
                    
        except Exception as e:
            logger.error(f"AI analysis failed for transaction {transaction.id}: {str(e)}")

    async def _prepare_transaction_data_for_ai(self, transaction: Transaction) -> Dict[str, Any]:
        """Prepare transaction data for AI analysis."""
        return {
            "transaction_id": transaction.id,
            "amount": float(transaction.amount),
            "transaction_type": transaction.transaction_type.value,
            "transaction_category": transaction.transaction_category.value,
            "merchant_name": transaction.merchant_name,
            "merchant_category": transaction.merchant_category,
            "location_city": transaction.location_city,
            "location_country": transaction.location_country,
            "channel": transaction.channel.value,
            "is_international": transaction.is_international,
            "is_contactless": transaction.is_contactless,
            "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None
        }

    async def _update_transaction_with_ai_insights(
        self, 
        transaction: Transaction, 
        analysis_result: Dict[str, Any]
    ) -> None:
        """Update transaction with AI analysis insights."""
        try:
            # Update risk score
            if "risk_score" in analysis_result:
                transaction.risk_score = analysis_result["risk_score"]
            
            # Update tags
            if "tags" in analysis_result:
                transaction.tags = analysis_result["tags"]
            
            # Update fraud flag
            if analysis_result.get("fraud_detected", False):
                transaction.fraud_flag = True
            
            await self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update transaction with AI insights: {str(e)}")

    async def _update_transaction_risk_score(
        self, 
        transaction: Transaction, 
        risk_score: float
    ) -> None:
        """Update transaction risk score."""
        try:
            transaction.risk_score = risk_score
            await self.db_session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update transaction risk score: {str(e)}")

    async def _get_transaction_context(self, transaction: Transaction) -> Dict[str, Any]:
        """Get context data for transaction analysis."""
        try:
            # Get user data
            user_query = select(User).where(User.id == transaction.user_id)
            user_result = await self.db_session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            # Get recent transactions
            recent_transactions_query = (
                select(Transaction)
                .where(Transaction.user_id == transaction.user_id)
                .where(Transaction.transaction_date >= transaction.transaction_date - timedelta(days=30))
                .order_by(desc(Transaction.transaction_date))
                .limit(10)
            )
            recent_result = await self.db_session.execute(recent_transactions_query)
            recent_transactions = recent_result.scalars().all()
            
            return {
                "current_transaction": await self._prepare_transaction_data_for_ai(transaction),
                "user_profile": user.to_dict() if user else {},
                "recent_transactions": [await self._prepare_transaction_data_for_ai(t) for t in recent_transactions]
            }
            
        except Exception as e:
            logger.error(f"Failed to get transaction context: {str(e)}")
            raise

    async def _group_transactions(
        self, 
        transactions: List[Dict[str, Any]], 
        group_by: str
    ) -> Dict[str, Any]:
        """Group transactions by specified criteria."""
        try:
            grouped = {}
            
            for transaction in transactions:
                if group_by == "category":
                    key = transaction.get("transaction_category", "Other")
                elif group_by == "type":
                    key = transaction.get("transaction_type", "Other")
                elif group_by == "merchant":
                    key = transaction.get("merchant_name", "Other")
                else:
                    key = "Other"
                
                if key not in grouped:
                    grouped[key] = {
                        "count": 0,
                        "total_amount": 0.0,
                        "transactions": []
                    }
                
                grouped[key]["count"] += 1
                grouped[key]["total_amount"] += float(transaction.get("amount", 0))
                grouped[key]["transactions"].append(transaction)
            
            return grouped
            
        except Exception as e:
            logger.error(f"Failed to group transactions: {str(e)}")
            raise

    async def _calculate_risk_indicators(self, user_id: int) -> Dict[str, Any]:
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