"""
Enhanced merchant repository with AI integration for merchant analysis and risk assessment.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, select, func, text, desc
from sqlalchemy.orm import selectinload

from app.models.merchant import Merchant, MerchantCategory, MerchantStatus
from app.schemas.merchant import MerchantCreate, MerchantUpdate
from app.repositories.enhanced_base import AIEnhancedRepository
from app.core.llm_orchestrator import TaskType, TaskComplexity
from app.core.exceptions import MerchantAnalysisError, RiskAssessmentError

logger = logging.getLogger(__name__)


class EnhancedMerchantRepository(AIEnhancedRepository[Merchant, MerchantCreate, MerchantUpdate]):
    """
    Enhanced merchant repository with AI-powered merchant analysis and risk assessment.
    
    Features:
    - AI-powered merchant risk assessment
    - Transaction pattern analysis
    - Merchant categorization and insights
    - Risk scoring and monitoring
    - Merchant performance analytics
    - Fraud detection integration
    """

    async def get_merchants_by_category(
        self,
        category: MerchantCategory,
        *,
        status: Optional[MerchantStatus] = None,
        risk_threshold: Optional[float] = None,
        use_cache: bool = True
    ) -> List[Merchant]:
        """Get merchants by category with optional filtering."""
        cache_key = f"merchants_by_category:{category}:{status}:{risk_threshold}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Merchant).where(Merchant.category == category)

        if status:
            query = query.where(Merchant.status == status)

        if risk_threshold is not None:
            query = query.where(Merchant.risk_score <= risk_threshold)

        query = query.order_by(desc(Merchant.risk_score))

        result = await self.db_session.execute(query)
        merchants = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, merchants, ttl=1800)  # 30 minutes

        return merchants

    async def get_merchants_by_location(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        *,
        use_cache: bool = True
    ) -> List[Merchant]:
        """Get merchants by location."""
        cache_key = f"merchants_by_location:{city}:{state}:{country}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Merchant)

        if city:
            query = query.where(Merchant.city == city)

        if state:
            query = query.where(Merchant.state == state)

        if country:
            query = query.where(Merchant.country == country)

        result = await self.db_session.execute(query)
        merchants = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, merchants, ttl=1800)  # 30 minutes

        return merchants

    async def analyze_merchant_risk(
        self,
        merchant_id: str,
        analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Analyze merchant risk using AI."""
        try:
            merchant = await self.get_by_id(merchant_id)
            if not merchant:
                raise MerchantAnalysisError(f"Merchant {merchant_id} not found")

            # Get merchant transaction data
            transaction_data = await self._get_merchant_transaction_data(merchant_id)

            # Analyze risk with AI
            risk_data = {
                "merchant_info": merchant.to_dict(),
                "transactions": transaction_data,
                "analysis_type": analysis_type
            }

            risk_analysis = await self.analyze_with_ai(
                risk_data,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            # Update merchant with new risk score
            new_risk_score = risk_analysis.get("risk_score", merchant.risk_score)
            await self.update(merchant, {
                "risk_score": new_risk_score,
                "is_high_risk": new_risk_score > 0.7,
                "last_reviewed": datetime.utcnow()
            })

            # Cache the analysis
            cache_key = f"merchant_risk_analysis:{merchant_id}:{analysis_type}"
            await self.cache_manager.set(cache_key, risk_analysis, ttl=3600)  # 1 hour

            return risk_analysis

        except Exception as e:
            logger.error(f"Merchant risk analysis failed: {str(e)}")
            raise RiskAssessmentError(f"Merchant risk analysis failed: {str(e)}")

    async def analyze_merchant_transactions(
        self,
        merchant_id: str,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Analyze merchant transaction patterns."""
        try:
            merchant = await self.get_by_id(merchant_id)
            if not merchant:
                raise MerchantAnalysisError(f"Merchant {merchant_id} not found")

            # Get merchant transaction data
            transaction_data = await self._get_merchant_transaction_data(merchant_id, time_range)

            # Analyze transaction patterns with AI
            transaction_analysis = await self.analyze_with_ai(
                {
                    "merchant_info": merchant.to_dict(),
                    "transactions": transaction_data,
                    "time_range": time_range
                },
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            # Cache the analysis
            cache_key = f"merchant_transaction_analysis:{merchant_id}:{time_range}"
            await self.cache_manager.set(cache_key, transaction_analysis, ttl=3600)  # 1 hour

            return transaction_analysis

        except Exception as e:
            logger.error(f"Merchant transaction analysis failed: {str(e)}")
            raise MerchantAnalysisError(f"Merchant transaction analysis failed: {str(e)}")

    async def get_high_risk_merchants(
        self,
        risk_threshold: float = 0.7,
        category: Optional[MerchantCategory] = None
    ) -> List[Merchant]:
        """Get high-risk merchants."""
        try:
            query = select(Merchant).where(Merchant.risk_score >= risk_threshold)

            if category:
                query = query.where(Merchant.category == category)

            query = query.order_by(desc(Merchant.risk_score))

            result = await self.db_session.execute(query)
            high_risk_merchants = result.scalars().all()

            return high_risk_merchants

        except Exception as e:
            logger.error(f"Failed to get high-risk merchants: {str(e)}")
            raise RiskAssessmentError(f"Failed to get high-risk merchants: {str(e)}")

    async def analyze_merchant_category_trends(
        self,
        category: MerchantCategory,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Analyze trends for a specific merchant category."""
        try:
            # Get merchants in category
            merchants = await self.get_merchants_by_category(category)

            # Get transaction data for all merchants in category
            category_transactions = []
            for merchant in merchants:
                merchant_transactions = await self._get_merchant_transaction_data(merchant.merchant_id, time_range)
                category_transactions.extend(merchant_transactions)

            # Analyze category trends with AI
            trend_data = {
                "category": category.value,
                "merchants": [merchant.to_dict() for merchant in merchants],
                "transactions": category_transactions,
                "time_range": time_range,
                "total_merchants": len(merchants),
                "total_transactions": len(category_transactions)
            }

            trend_analysis = await self.analyze_with_ai(
                trend_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return trend_analysis

        except Exception as e:
            logger.error(f"Merchant category trend analysis failed: {str(e)}")
            raise MerchantAnalysisError(f"Merchant category trend analysis failed: {str(e)}")

    async def detect_merchant_anomalies(
        self,
        merchant_id: str,
        threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in merchant behavior."""
        try:
            # Get merchant transaction data
            transaction_data = await self._get_merchant_transaction_data(merchant_id, "30d")

            # Detect anomalies using AI
            anomalies = await self.detect_anomalies(transaction_data, threshold)

            # Analyze anomalies for merchant-specific insights
            anomaly_analysis = await self.analyze_with_ai(
                {
                    "merchant_id": merchant_id,
                    "transactions": transaction_data,
                    "anomalies": anomalies,
                    "threshold": threshold
                },
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            return anomaly_analysis.get("merchant_anomalies", [])

        except Exception as e:
            logger.error(f"Merchant anomaly detection failed: {str(e)}")
            raise MerchantAnalysisError(f"Merchant anomaly detection failed: {str(e)}")

    async def get_merchant_performance_metrics(
        self,
        merchant_id: str,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Get comprehensive merchant performance metrics."""
        try:
            merchant = await self.get_by_id(merchant_id)
            if not merchant:
                raise MerchantAnalysisError(f"Merchant {merchant_id} not found")

            # Get merchant transaction data
            transaction_data = await self._get_merchant_transaction_data(merchant_id, time_range)

            # Calculate basic metrics
            total_transactions = len(transaction_data)
            total_amount = sum(t.get("amount", 0) for t in transaction_data)
            average_transaction = total_amount / total_transactions if total_transactions > 0 else 0

            # Analyze performance with AI
            performance_data = {
                "merchant_info": merchant.to_dict(),
                "transactions": transaction_data,
                "basic_metrics": {
                    "total_transactions": total_transactions,
                    "total_amount": total_amount,
                    "average_transaction": average_transaction,
                    "time_range": time_range
                }
            }

            performance_analysis = await self.analyze_with_ai(
                performance_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return performance_analysis

        except Exception as e:
            logger.error(f"Merchant performance analysis failed: {str(e)}")
            raise MerchantAnalysisError(f"Merchant performance analysis failed: {str(e)}")

    async def bulk_update_merchant_risk(
        self,
        merchant_ids: List[str],
        risk_threshold: float = 0.5
    ) -> int:
        """Bulk update merchant risk scores."""
        try:
            updated_count = 0

            for merchant_id in merchant_ids:
                try:
                    # Analyze merchant risk
                    risk_analysis = await self.analyze_merchant_risk(merchant_id)
                    new_risk_score = risk_analysis.get("risk_score", 0.0)

                    # Update merchant if risk score exceeds threshold
                    if new_risk_score > risk_threshold:
                        merchant = await self.get_by_id(merchant_id)
                        if merchant:
                            await self.update(merchant, {
                                "risk_score": new_risk_score,
                                "is_high_risk": new_risk_score > 0.7,
                                "last_reviewed": datetime.utcnow()
                            })
                            updated_count += 1

                except Exception as e:
                    logger.error(f"Failed to update risk for merchant {merchant_id}: {str(e)}")
                    continue

            logger.info(f"Bulk updated {updated_count} merchant risk scores")
            return updated_count

        except Exception as e:
            logger.error(f"Bulk merchant risk update failed: {str(e)}")
            raise RiskAssessmentError(f"Bulk merchant risk update failed: {str(e)}")

    async def get_merchant_statistics(
        self,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive merchant statistics."""
        try:
            # Get all merchants
            query = select(Merchant)
            result = await self.db_session.execute(query)
            merchants = result.scalars().all()

            # Calculate statistics
            total_merchants = len(merchants)
            active_merchants = len([m for m in merchants if m.status == MerchantStatus.ACTIVE])
            high_risk_merchants = len([m for m in merchants if m.is_high_risk])
            suspended_merchants = len([m for m in merchants if m.status == MerchantStatus.SUSPENDED])

            # Calculate average risk score
            risk_scores = [m.risk_score for m in merchants if m.risk_score is not None]
            avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

            # Get category distribution
            category_distribution = await self._calculate_category_distribution(merchants)

            statistics = {
                "time_range": time_range,
                "total_merchants": total_merchants,
                "active_merchants": active_merchants,
                "high_risk_merchants": high_risk_merchants,
                "suspended_merchants": suspended_merchants,
                "average_risk_score": avg_risk_score,
                "risk_rate": (high_risk_merchants / total_merchants * 100) if total_merchants > 0 else 0.0,
                "category_distribution": category_distribution
            }

            return statistics

        except Exception as e:
            logger.error(f"Failed to get merchant statistics: {str(e)}")
            raise MerchantAnalysisError(f"Failed to get merchant statistics: {str(e)}")

    # ==================== Abstract Method Implementations ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for merchant analysis."""
        try:
            # Get user's transaction data with merchant information
            transaction_data = await self._get_user_transaction_data(user_id, time_range or "90d")
            
            # Extract merchant information from transactions
            merchants = {}
            for transaction in transaction_data:
                merchant_id = transaction.get("merchant_id")
                if merchant_id:
                    if merchant_id not in merchants:
                        merchants[merchant_id] = {
                            "merchant_id": merchant_id,
                            "transactions": [],
                            "total_amount": 0,
                            "transaction_count": 0
                        }
                    merchants[merchant_id]["transactions"].append(transaction)
                    merchants[merchant_id]["total_amount"] += transaction.get("amount", 0)
                    merchants[merchant_id]["transaction_count"] += 1

            return {
                "user_id": user_id,
                "data_type": data_type,
                "time_range": time_range,
                "merchants": list(merchants.values()),
                "transactions": transaction_data,
                "total_merchants": len(merchants),
                "total_transactions": len(transaction_data)
            }

        except Exception as e:
            logger.error(f"Failed to get user data for analysis: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _get_user_transactions(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user's transaction data with merchant information."""
        try:
            # This would typically query the transaction repository
            # For now, return mock data with merchant information
            return [
                {
                    "id": "1",
                    "amount": 100.0,
                    "category": "groceries",
                    "timestamp": datetime.utcnow(),
                    "location": "New York",
                    "status": "completed",
                    "merchant_id": "MERCH001",
                    "merchant_name": "Local Grocery Store"
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get user transactions: {str(e)}")
            return []

    async def _get_user_risk_data(self, user_id: int) -> Dict[str, Any]:
        """Get user's merchant-related risk data."""
        try:
            # Get user's transaction data
            transactions = await self._get_user_transaction_data(user_id, "90d")
            
            # Calculate merchant-related risk metrics
            unique_merchants = len(set(t.get("merchant_id") for t in transactions if t.get("merchant_id")))
            high_risk_merchants = len([t for t in transactions if t.get("merchant_risk_score", 0) > 0.7])
            total_amount = sum(t.get("amount", 0) for t in transactions)

            return {
                "user_id": user_id,
                "unique_merchants": unique_merchants,
                "high_risk_merchants": high_risk_merchants,
                "total_amount": total_amount,
                "merchant_risk_rate": (high_risk_merchants / unique_merchants * 100) if unique_merchants > 0 else 0.0,
                "transactions": transactions
            }

        except Exception as e:
            logger.error(f"Failed to get user risk data: {str(e)}")
            return {"user_id": user_id, "error": str(e)}

    async def _analyze_spending_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze spending patterns for merchant analysis."""
        try:
            if not transactions:
                return {"patterns": [], "merchant_insights": []}

            # Calculate basic metrics
            total_amount = sum(t.get("amount", 0) for t in transactions)
            transaction_count = len(transactions)
            
            # Group by merchant
            merchant_patterns = {}
            for transaction in transactions:
                merchant_id = transaction.get("merchant_id", "unknown")
                amount = transaction.get("amount", 0)
                
                if merchant_id not in merchant_patterns:
                    merchant_patterns[merchant_id] = {
                        "merchant_id": merchant_id,
                        "total_amount": 0,
                        "transaction_count": 0,
                        "transactions": []
                    }
                
                merchant_patterns[merchant_id]["total_amount"] += amount
                merchant_patterns[merchant_id]["transaction_count"] += 1
                merchant_patterns[merchant_id]["transactions"].append(transaction)

            # Find merchant insights
            merchant_insights = []
            
            # Check for merchant concentration
            if len(merchant_patterns) < 5:
                merchant_insights.append("Concentrated spending with few merchants")
            
            # Check for high-value merchants
            high_value_merchants = [m for m in merchant_patterns.values() if m["total_amount"] > total_amount * 0.3]
            if high_value_merchants:
                merchant_insights.append(f"High-value merchants: {len(high_value_merchants)}")

            return {
                "patterns": {
                    "total_amount": total_amount,
                    "transaction_count": transaction_count,
                    "merchant_patterns": merchant_patterns,
                    "unique_merchants": len(merchant_patterns)
                },
                "merchant_insights": merchant_insights
            }

        except Exception as e:
            logger.error(f"Failed to analyze spending patterns: {str(e)}")
            return {"patterns": [], "merchant_insights": [], "error": str(e)}

    async def _analyze_temporal_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns for merchant analysis."""
        try:
            if not transactions:
                return {"temporal_patterns": [], "merchant_insights": []}

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

            # Find merchant temporal insights
            merchant_insights = []
            
            # Check for peak merchant activity times
            peak_hours = sorted(hourly_patterns.items(), key=lambda x: x[1], reverse=True)[:3]
            if peak_hours:
                merchant_insights.append(f"Peak merchant activity hours: {peak_hours}")

            return {
                "temporal_patterns": {
                    "hourly_distribution": hourly_patterns,
                    "daily_distribution": daily_patterns,
                    "peak_hours": peak_hours
                },
                "merchant_insights": merchant_insights
            }

        except Exception as e:
            logger.error(f"Failed to analyze temporal patterns: {str(e)}")
            return {"temporal_patterns": [], "merchant_insights": [], "error": str(e)}

    async def _analyze_geographic_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze geographic patterns for merchant analysis."""
        try:
            if not transactions:
                return {"geographic_patterns": [], "merchant_insights": []}

            # Group by location
            location_patterns = {}
            
            for transaction in transactions:
                location = transaction.get("location", "unknown")
                amount = transaction.get("amount", 0)
                location_patterns[location] = location_patterns.get(location, 0) + amount

            # Find merchant geographic insights
            merchant_insights = []
            
            # Check for location diversity
            if len(location_patterns) > 10:
                merchant_insights.append("High geographic diversity in merchant usage")
            elif len(location_patterns) < 3:
                merchant_insights.append("Concentrated merchant usage in few locations")

            return {
                "geographic_patterns": {
                    "location_breakdown": location_patterns,
                    "total_locations": len(location_patterns)
                },
                "merchant_insights": merchant_insights
            }

        except Exception as e:
            logger.error(f"Failed to analyze geographic patterns: {str(e)}")
            return {"geographic_patterns": [], "merchant_insights": [], "error": str(e)}

    async def _perform_risk_analysis(
        self,
        user_data: Dict[str, Any],
        assessment_type: str
    ) -> Dict[str, Any]:
        """Perform risk analysis for merchant-related data."""
        try:
            merchants = user_data.get("merchants", [])
            
            # Calculate risk metrics
            total_merchants = len(merchants)
            high_risk_merchants = len([m for m in merchants if m.get("merchant_risk_score", 0) > 0.7])
            total_amount = sum(m.get("total_amount", 0) for m in merchants)

            # Calculate risk score
            risk_score = 0.0
            risk_factors = []

            if high_risk_merchants > 0:
                risk_score += 0.4
                risk_factors.append("High-risk merchants detected")

            if total_merchants > 20:
                risk_score += 0.2
                risk_factors.append("High number of unique merchants")

            if total_amount > 10000:
                risk_score += 0.2
                risk_factors.append("High transaction volume")

            # Normalize risk score
            risk_score = min(risk_score, 1.0)

            return {
                "overall_risk_score": risk_score,
                "risk_factors": risk_factors,
                "merchant_metrics": {
                    "total_merchants": total_merchants,
                    "high_risk_merchants": high_risk_merchants,
                    "total_amount": total_amount
                }
            }

        except Exception as e:
            logger.error(f"Failed to perform risk analysis: {str(e)}")
            return {"overall_risk_score": 0.0, "risk_factors": [], "error": str(e)}

    # ==================== Helper Methods ====================

    async def _get_merchant_transaction_data(
        self,
        merchant_id: str,
        time_range: str = "90d"
    ) -> List[Dict[str, Any]]:
        """Get transaction data for a specific merchant."""
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
                    "status": "completed",
                    "merchant_id": merchant_id
                }
            ]

        except Exception as e:
            logger.error(f"Failed to get merchant transaction data: {str(e)}")
            return []

    async def _calculate_category_distribution(
        self,
        merchants: List[Merchant]
    ) -> Dict[str, int]:
        """Calculate merchant category distribution."""
        try:
            distribution = {}

            for merchant in merchants:
                category = merchant.category.value if merchant.category else "unknown"
                distribution[category] = distribution.get(category, 0) + 1

            return distribution

        except Exception as e:
            logger.error(f"Failed to calculate category distribution: {str(e)}")
            return {}
            
    # ==================== API Endpoint Methods ====================
    
    async def get_merchant_transactions(
        self,
        merchant_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for a specific merchant with pagination.
        
        Args:
            merchant_id: The ID of the merchant
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            
        Returns:
            List of transaction records
        """
        try:
            # Import Transaction model here to avoid circular imports
            from app.models.transaction import Transaction
            
            # Build query for transactions related to this merchant
            query = (
                select(Transaction)
                .where(Transaction.merchant_id == merchant_id)
                .order_by(Transaction.timestamp.desc())
                .offset(skip)
                .limit(limit)
            )
            
            # Execute query
            result = await self.db_session.execute(query)
            transactions = result.scalars().all()
            
            # Convert to dictionaries
            return [transaction.to_dict() for transaction in transactions]
            
        except Exception as e:
            logger.error(f"Error retrieving merchant transactions: {str(e)}")
            raise
    
    async def count_merchant_transactions(self, merchant_id: str) -> int:
        """
        Count the total number of transactions for a merchant.
        
        Args:
            merchant_id: The ID of the merchant
            
        Returns:
            Total count of transactions
        """
        try:
            # Import Transaction model here to avoid circular imports
            from app.models.transaction import Transaction
            
            # Build count query
            query = select(func.count()).select_from(Transaction).where(Transaction.merchant_id == merchant_id)
            
            # Execute query
            result = await self.db_session.execute(query)
            count = result.scalar_one()
            
            return count
            
        except Exception as e:
            logger.error(f"Error counting merchant transactions: {str(e)}")
            raise
    
    async def get_popular_categories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular merchant categories by transaction volume and count.
        
        Args:
            limit: Maximum number of categories to return
            
        Returns:
            List of categories with transaction statistics
        """
        try:
            # Import Transaction model here to avoid circular imports
            from app.models.transaction import Transaction
            
            # Build query for category statistics
            query = (
                select(
                    Merchant.category,
                    func.count(Transaction.id).label('transaction_count'),
                    func.sum(Transaction.amount).label('total_amount')
                )
                .join(
                    Transaction, Transaction.merchant_id == Merchant.merchant_id
                )
                .group_by(
                    Merchant.category
                )
                .order_by(
                    func.count(Transaction.id).desc()
                )
                .limit(limit)
            )
            
            # Execute query
            result = await self.db_session.execute(query)
            categories = result.all()
            
            # Format the results
            return [
                {
                    "category": category.value if hasattr(category, 'value') else str(category),
                    "transaction_count": int(transaction_count),
                    "total_amount": float(total_amount)
                }
                for category, transaction_count, total_amount in categories
            ]
            
        except Exception as e:
            logger.error(f"Error retrieving popular merchant categories: {str(e)}")
            raise