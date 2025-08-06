"""
Enhanced branch repository with AI integration for branch analytics and management.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, select, func, text, desc
from sqlalchemy.orm import selectinload

from app.models.branch import Branch, BranchType, BranchStatus, Employee, EmployeeRole
from app.schemas.branch import BranchCreate, BranchUpdate
from app.repositories.enhanced_base import AIEnhancedRepository
from app.core.llm_orchestrator import TaskType, TaskComplexity

logger = logging.getLogger(__name__)


class EnhancedBranchRepository(AIEnhancedRepository[Branch, BranchCreate, BranchUpdate]):
    """
    Enhanced branch repository with AI-powered branch analytics and management.
    
    Features:
    - AI-powered branch performance analysis
    - Employee management and analytics
    - Branch capacity and utilization analysis
    - Geographic analysis and optimization
    - Customer service analytics
    - Branch risk assessment
    """

    def __init__(
        self,
        db_session,
        llm_orchestrator=None,
        cache_manager=None
    ):
        super().__init__(Branch, db_session, llm_orchestrator, cache_manager)

    # ==================== Enhanced CRUD Operations ====================

    async def get_by_branch_code(
        self,
        branch_code: str,
        include_inactive: bool = False,
        load_relationships: bool = True,
        use_cache: bool = True
    ) -> Optional[Branch]:
        """Get a branch by branch code with caching."""
        cache_key = f"branch_code:{branch_code}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Branch).where(Branch.branch_code == branch_code)

        if not include_inactive:
            query = query.where(Branch.status == BranchStatus.ACTIVE)

        if load_relationships:
            query = query.options(
                selectinload(Branch.accounts),
                selectinload(Branch.employees)
            )

        result = await self.db_session.execute(query)
        branch = result.scalars().first()

        if branch and use_cache:
            await self.cache_manager.set(cache_key, branch, ttl=1800)  # 30 minutes

        return branch

    async def get_branches_by_location(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        branch_type: Optional[BranchType] = None,
        use_cache: bool = True
    ) -> List[Branch]:
        """Get branches by location with filtering."""
        cache_key = f"branches_location:{city}:{state}:{country}:{branch_type.value if branch_type else 'all'}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Branch)

        if city:
            query = query.where(Branch.city == city)
        if state:
            query = query.where(Branch.state == state)
        if country:
            query = query.where(Branch.country == country)
        if branch_type:
            query = query.where(Branch.branch_type == branch_type)

        # Always filter for active branches
        query = query.where(Branch.status == BranchStatus.ACTIVE)

        result = await self.db_session.execute(query)
        branches = result.scalars().all()

        if branches and use_cache:
            await self.cache_manager.set(cache_key, branches, ttl=1800)  # 30 minutes

        return branches

    # ==================== AI Integration Methods ====================

    async def analyze_branch_performance(
        self,
        branch_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Analyze branch performance using AI."""
        try:
            # Get branch data
            branch_data = await self._get_branch_data_for_analysis(branch_id, "performance", time_range)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                branch_data,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Branch performance analysis failed: {str(e)}")
            return {}

    async def generate_branch_recommendations(
        self,
        branch_id: int,
        recommendation_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Generate AI recommendations for branch optimization."""
        try:
            # Get branch data
            branch_data = await self._get_branch_data_for_analysis(branch_id, "recommendation")

            # Generate AI recommendations
            recommendations = await self.analyze_with_ai(
                branch_data,
                TaskType.FINANCIAL_RECOMMENDATION,
                TaskComplexity.HIGH
            )

            return recommendations

        except Exception as e:
            logger.error(f"Branch recommendation generation failed: {str(e)}")
            return {}

    async def analyze_branch_risk(
        self,
        branch_id: int
    ) -> Dict[str, Any]:
        """Analyze branch risk factors using AI."""
        try:
            # Get branch data
            branch_data = await self._get_branch_data_for_analysis(branch_id, "risk")

            # Analyze with AI
            risk_analysis = await self.analyze_with_ai(
                branch_data,
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )

            return risk_analysis

        except Exception as e:
            logger.error(f"Branch risk analysis failed: {str(e)}")
            return {}

    async def predict_branch_growth(
        self,
        branch_id: int,
        forecast_period: str = "6m"
    ) -> Dict[str, Any]:
        """Predict branch growth using AI."""
        try:
            # Get branch data
            branch_data = await self._get_branch_data_for_analysis(branch_id, "growth")

            # Add forecast period
            branch_data["forecast_period"] = forecast_period

            # Analyze with AI
            growth_prediction = await self.analyze_with_ai(
                branch_data,
                TaskType.PREDICTIVE_ANALYTICS,
                TaskComplexity.HIGH
            )

            return growth_prediction

        except Exception as e:
            logger.error(f"Branch growth prediction failed: {str(e)}")
            return {}

    async def analyze_branch_customer_service(
        self,
        branch_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Analyze branch customer service quality."""
        try:
            # Get branch data
            branch_data = await self._get_branch_data_for_analysis(branch_id, "customer_service", time_range)

            # Analyze with AI
            service_analysis = await self.analyze_with_ai(
                branch_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return service_analysis

        except Exception as e:
            logger.error(f"Branch customer service analysis failed: {str(e)}")
            return {}

    async def analyze_employee_performance(
        self,
        branch_id: int,
        employee_id: int
    ) -> Dict[str, Any]:
        """Analyze employee performance using AI."""
        try:
            # Get employee data
            employee_data = {}
            
            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                employee_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Employee performance analysis failed: {str(e)}")
            return {}

    # ==================== Implementation of Abstract Methods ====================

    async def _get_user_data_for_analysis(
        self,
        user_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get user data for AI analysis (for branch context)."""
        try:
            # This method is not directly applicable for branches
            # but required by the abstract base class
            return {
                "data_type": data_type,
                "time_range": time_range,
                "branch_context": True
            }

        except Exception as e:
            logger.error(f"Failed to get user data for analysis: {str(e)}")
            return {}

    async def _get_user_transactions(
        self,
        user_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get user transactions for analysis (not applicable for branches)."""
        return []

    async def _get_user_risk_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data for risk assessment (not applicable for branches)."""
        return {}
        
    async def _analyze_spending_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze spending patterns (not applicable for branches)."""
        return {}

    async def _analyze_temporal_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze temporal patterns (not applicable for branches)."""
        return {}

    async def _analyze_geographic_patterns(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze geographic patterns (not applicable for branches)."""
        return {}

    async def _perform_risk_analysis(
        self,
        user_data: Dict[str, Any],
        assessment_type: str
    ) -> Dict[str, Any]:
        """Perform risk analysis (not applicable for branches)."""
        return {}

    # ==================== Branch-Specific Methods ====================

    async def _get_branch_data_for_analysis(
        self,
        branch_id: int,
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get branch data for AI analysis."""
        try:
            # Get branch
            branch = await self.get_by_id(branch_id)
            if not branch:
                logger.error(f"Branch {branch_id} not found")
                return {}

            # Get branch accounts
            accounts = await self._get_branch_accounts(branch_id, time_range or "30d")

            # Get branch employees
            employees = await self._get_branch_employees(branch_id)

            return {
                "branch_profile": branch.to_dict(),
                "accounts": accounts,
                "employees": [employee.to_dict() for employee in employees],
                "data_type": data_type,
                "time_range": time_range
            }

        except Exception as e:
            logger.error(f"Failed to get branch data for analysis: {str(e)}")
            return {}

    async def _get_branch_accounts(
        self,
        branch_id: int,
        time_range: str
    ) -> List[Dict[str, Any]]:
        """Get branch accounts for analysis."""
        try:
            # This would typically query accounts associated with the branch
            # For now, return empty list as account-branch relationship needs to be implemented
            return []

        except Exception as e:
            logger.error(f"Failed to get branch accounts: {str(e)}")
            return []

    async def _get_branch_employees(
        self,
        branch_id: int
    ) -> List[Employee]:
        """Get branch employees."""
        try:
            return await self.get_branch_employees(branch_id)

        except Exception as e:
            logger.error(f"Failed to get branch employees: {str(e)}")
            return []

    async def _calculate_branch_metrics(
        self,
        accounts: List[Dict[str, Any]],
        employees: List[Employee],
        branch: Branch
    ) -> Dict[str, Any]:
        """Calculate branch performance metrics."""
        try:
            # Calculate metrics
            metrics = {
                "total_accounts": len(accounts),
                "total_employees": len(employees),
                "accounts_per_employee": len(accounts) / max(len(employees), 1),
                "branch_utilization": 0.0,  # Placeholder
                "operational_efficiency": 0.0,  # Placeholder
                "customer_satisfaction": 0.0,  # Placeholder
            }

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate branch metrics: {str(e)}")
            return {}

    async def _analyze_branch_patterns(
        self,
        accounts: List[Dict[str, Any]],
        employees: List[Employee]
    ) -> Dict[str, Any]:
        """Analyze branch operational patterns."""
        try:
            # Analyze patterns
            patterns = {
                "account_growth": {},
                "employee_efficiency": {},
                "transaction_volume": {},
                "peak_hours": {},
                "service_utilization": {}
            }

            return patterns

        except Exception as e:
            logger.error(f"Failed to analyze branch patterns: {str(e)}")
            return {}

    async def get_branch_analytics(
        self,
        branch_id: int,
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive branch analytics."""
        cache_key = f"branch_analytics:{branch_id}:{time_range}"

        # Check cache first
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return cached

        try:
            # Get branch
            branch = await self.get_by_id(branch_id)
            if not branch:
                logger.error(f"Branch {branch_id} not found")
                return {}

            # Get branch accounts
            accounts = await self._get_branch_accounts(branch_id, time_range)

            # Get branch employees
            employees = await self._get_branch_employees(branch_id)

            # Calculate branch metrics
            branch_metrics = await self._calculate_branch_metrics(accounts, employees, branch)

            # Analyze branch patterns
            branch_analysis = await self._analyze_branch_patterns(accounts, employees)
            
            # Generate AI insights
            ai_insights = await self.analyze_branch_performance(branch_id, time_range)

            analytics_result = {
                "branch_id": branch_id,
                "time_range": time_range,
                "branch_info": {
                    "branch_code": branch.branch_code,
                    "name": branch.name,
                    "branch_type": branch.branch_type.value,
                    "status": branch.status.value,
                    "city": branch.city,
                    "state": branch.state,
                    "full_address": branch.full_address
                },
                "branch_metrics": branch_metrics,
                "branch_analysis": branch_analysis,
                "ai_insights": ai_insights,
                "generated_at": datetime.utcnow().isoformat()
            }

            # Cache the result
            await self.cache_manager.set(cache_key, analytics_result, ttl=3600)  # 1 hour

            return analytics_result

        except Exception as e:
            logger.error(f"Branch analytics failed: {str(e)}")
            return {}

    async def get_branch_employees(
        self,
        branch_id: int,
        role: Optional[EmployeeRole] = None,
        active_only: bool = True
    ) -> List[Employee]:
        """Get employees assigned to a branch."""
        try:
            query = select(Employee).where(Employee.branch_id == branch_id)

            if role:
                query = query.where(Employee.role == role)

            if active_only:
                query = query.where(Employee.is_active == True)

            result = await self.db_session.execute(query)
            employees = result.scalars().all()

            return employees

        except Exception as e:
            logger.error(f"Failed to get branch employees: {str(e)}")
            return []

    async def get_branch_employee_count(
        self,
        branch_id: int,
        role: Optional[EmployeeRole] = None,
        active_only: bool = True
    ) -> int:
        """Get count of employees assigned to a branch."""
        try:
            query = select(func.count(Employee.id)).where(Employee.branch_id == branch_id)

            if role:
                query = query.where(Employee.role == role)

            if active_only:
                query = query.where(Employee.is_active == True)

            result = await self.db_session.execute(query)
            count = result.scalar_one()

            return count

        except Exception as e:
            logger.error(f"Failed to get branch employee count: {str(e)}")
            return 0

    async def analyze_branch_staffing(
        self,
        branch_id: int
    ) -> Dict[str, Any]:
        """Analyze branch staffing needs and efficiency."""
        try:
            # Get branch data
            branch = await self.get_by_id(branch_id)
            if not branch:
                logger.error(f"Branch {branch_id} not found")
                return {}

            # Get employees
            employees = await self.get_branch_employees(branch_id)
            
            # Analyze with AI
            staffing_analysis = await self.analyze_with_ai(
                {
                    "branch_profile": branch.to_dict(),
                    "employees": [employee.to_dict() for employee in employees],
                    "branch_type": branch.branch_type.value,
                    "branch_size": branch.size if hasattr(branch, 'size') else "unknown"
                },
                TaskType.RESOURCE_OPTIMIZATION,
                TaskComplexity.MEDIUM
            )

            return staffing_analysis

        except Exception as e:
            logger.error(f"Branch staffing analysis failed: {str(e)}")
            return {}
