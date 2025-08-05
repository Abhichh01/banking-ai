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
from app.core.exceptions import BranchAnalysisError, EmployeeManagementError

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

        query = query.where(Branch.status == BranchStatus.ACTIVE)
        query = query.options(selectinload(Branch.accounts))

        result = await self.db_session.execute(query)
        branches = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, branches, ttl=900)  # 15 minutes

        return branches

    async def get_branch_with_employees(
        self,
        branch_id: int,
        include_inactive: bool = False,
        use_cache: bool = True
    ) -> Optional[Branch]:
        """Get branch with employee details."""
        cache_key = f"branch_with_employees:{branch_id}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Branch).where(Branch.id == branch_id)

        if not include_inactive:
            query = query.where(Branch.status == BranchStatus.ACTIVE)

        query = query.options(
            selectinload(Branch.employees),
            selectinload(Branch.accounts)
        )

        result = await self.db_session.execute(query)
        branch = result.scalars().first()

        if branch and use_cache:
            await self.cache_manager.set(cache_key, branch, ttl=900)  # 15 minutes

        return branch

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
            raise BranchAnalysisError(f"Branch performance analysis failed: {str(e)}")

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
            raise BranchAnalysisError(f"Branch recommendation generation failed: {str(e)}")

    # ==================== Advanced Analytics Methods ====================

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
                raise BranchAnalysisError(f"Branch {branch_id} not found")

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
            raise BranchAnalysisError(f"Branch analytics failed: {str(e)}")

    async def get_branch_performance(
        self,
        branch_id: int,
        time_range: str = "90d"
    ) -> Dict[str, Any]:
        """Get branch performance metrics."""
        try:
            # Get branch analytics
            analytics = await self.get_branch_analytics(branch_id, time_range)

            # Calculate performance metrics
            performance_metrics = await self._calculate_branch_performance_metrics(analytics)

            return {
                "branch_id": branch_id,
                "time_range": time_range,
                "performance_metrics": performance_metrics,
                "recommendations": analytics.get("ai_insights", {}).get("recommendations", [])
            }

        except Exception as e:
            logger.error(f"Branch performance analysis failed: {str(e)}")
            raise BranchAnalysisError(f"Branch performance analysis failed: {str(e)}")

    async def get_branch_capacity_analysis(
        self,
        branch_id: int
    ) -> Dict[str, Any]:
        """Analyze branch capacity and utilization."""
        try:
            # Get branch with employees
            branch = await self.get_branch_with_employees(branch_id)
            if not branch:
                raise BranchAnalysisError(f"Branch {branch_id} not found")

            # Get branch accounts
            accounts = await self._get_branch_accounts(branch_id, "90d")

            # Calculate capacity metrics
            capacity_metrics = await self._calculate_capacity_metrics(branch, accounts)

            return {
                "branch_id": branch_id,
                "capacity_metrics": capacity_metrics,
                "utilization_analysis": await self._analyze_utilization(branch, accounts),
                "recommendations": await self._generate_capacity_recommendations(capacity_metrics)
            }

        except Exception as e:
            logger.error(f"Branch capacity analysis failed: {str(e)}")
            raise BranchAnalysisError(f"Branch capacity analysis failed: {str(e)}")

    # ==================== Employee Management Methods ====================

    async def get_branch_employees(
        self,
        branch_id: int,
        role: Optional[EmployeeRole] = None,
        is_active: bool = True,
        use_cache: bool = True
    ) -> List[Employee]:
        """Get employees for a branch with filtering."""
        cache_key = f"branch_employees:{branch_id}:{role.value if role else 'all'}:{is_active}"

        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached

        query = select(Employee).where(Employee.branch_id == branch_id)

        if role:
            query = query.where(Employee.role == role)
        if is_active:
            query = query.where(Employee.is_active == True)  # noqa: E712

        result = await self.db_session.execute(query)
        employees = result.scalars().all()

        if use_cache:
            await self.cache_manager.set(cache_key, employees, ttl=900)  # 15 minutes

        return employees

    async def analyze_employee_performance(
        self,
        branch_id: int,
        employee_id: int
    ) -> Dict[str, Any]:
        """Analyze employee performance using AI."""
        try:
            # Get employee data
            employee_data = await self._get_employee_data_for_analysis(branch_id, employee_id)

            # Analyze with AI
            analysis_result = await self.analyze_with_ai(
                employee_data,
                TaskType.BEHAVIORAL_ANALYSIS,
                TaskComplexity.MEDIUM
            )

            return analysis_result

        except Exception as e:
            logger.error(f"Employee performance analysis failed: {str(e)}")
            raise EmployeeManagementError(f"Employee performance analysis failed: {str(e)}")

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
            raise

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
                raise BranchAnalysisError(f"Branch {branch_id} not found")

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
            raise

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
            raise

    async def _get_branch_employees(
        self,
        branch_id: int
    ) -> List[Employee]:
        """Get branch employees."""
        try:
            return await self.get_branch_employees(branch_id)

        except Exception as e:
            logger.error(f"Failed to get branch employees: {str(e)}")
            raise

    async def _calculate_branch_metrics(
        self,
        accounts: List[Dict[str, Any]],
        employees: List[Employee],
        branch: Branch
    ) -> Dict[str, Any]:
        """Calculate branch metrics."""
        try:
            total_accounts = len(accounts)
            total_employees = len(employees)
            active_employees = len([e for e in employees if e.is_active])

            # Calculate total balance from accounts
            total_balance = sum(float(account.get("balance", 0)) for account in accounts)
            avg_balance = total_balance / total_accounts if total_accounts > 0 else 0

            return {
                "total_accounts": total_accounts,
                "total_employees": total_employees,
                "active_employees": active_employees,
                "total_balance": total_balance,
                "average_balance": avg_balance,
                "employee_utilization": active_employees / total_employees if total_employees > 0 else 0,
                "branch_capacity": {
                    "has_atm": branch.has_atm,
                    "has_locker": branch.has_locker,
                    "has_wifi": branch.has_wifi,
                    "is_24x7": branch.is_24x7,
                    "is_wheelchair_accessible": branch.is_wheelchair_accessible
                }
            }

        except Exception as e:
            logger.error(f"Failed to calculate branch metrics: {str(e)}")
            raise

    async def _analyze_branch_patterns(
        self,
        accounts: List[Dict[str, Any]],
        employees: List[Employee]
    ) -> Dict[str, Any]:
        """Analyze branch patterns."""
        try:
            # Analyze employee patterns
            employee_analysis = await self._analyze_employee_patterns(employees)

            # Analyze account patterns
            account_analysis = await self._analyze_account_patterns(accounts)

            return {
                "employee_analysis": employee_analysis,
                "account_analysis": account_analysis
            }

        except Exception as e:
            logger.error(f"Failed to analyze branch patterns: {str(e)}")
            raise

    async def _analyze_employee_patterns(
        self,
        employees: List[Employee]
    ) -> Dict[str, Any]:
        """Analyze employee patterns."""
        try:
            if not employees:
                return {}

            # Group by role
            role_distribution = {}
            for employee in employees:
                role = employee.role.value
                role_distribution[role] = role_distribution.get(role, 0) + 1

            # Calculate active vs inactive
            active_count = len([e for e in employees if e.is_active])
            inactive_count = len(employees) - active_count

            return {
                "total_employees": len(employees),
                "active_employees": active_count,
                "inactive_employees": inactive_count,
                "role_distribution": role_distribution,
                "average_tenure": await self._calculate_average_tenure(employees)
            }

        except Exception as e:
            logger.error(f"Failed to analyze employee patterns: {str(e)}")
            raise

    async def _analyze_account_patterns(
        self,
        accounts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze account patterns."""
        try:
            if not accounts:
                return {}

            # Calculate account statistics
            total_accounts = len(accounts)
            total_balance = sum(float(account.get("balance", 0)) for account in accounts)
            avg_balance = total_balance / total_accounts if total_accounts > 0 else 0

            return {
                "total_accounts": total_accounts,
                "total_balance": total_balance,
                "average_balance": avg_balance,
                "account_distribution": await self._calculate_account_distribution(accounts)
            }

        except Exception as e:
            logger.error(f"Failed to analyze account patterns: {str(e)}")
            raise

    async def _calculate_branch_performance_metrics(
        self,
        analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate branch performance metrics."""
        try:
            branch_metrics = analytics.get("branch_metrics", {})
            branch_analysis = analytics.get("branch_analysis", {})

            # Calculate performance indicators
            total_accounts = branch_metrics.get("total_accounts", 0)
            total_balance = branch_metrics.get("total_balance", 0)
            active_employees = branch_metrics.get("active_employees", 0)
            total_employees = branch_metrics.get("total_employees", 0)

            # Performance score (0-100)
            performance_score = 0
            if total_accounts > 100:
                performance_score += 30  # Good account base
            if total_balance > 1000000:
                performance_score += 30  # High total balance
            if active_employees / total_employees > 0.8 if total_employees > 0 else False:
                performance_score += 40  # Good employee utilization

            return {
                "performance_score": min(performance_score, 100),
                "account_health": "high" if total_accounts > 100 else "medium" if total_accounts > 50 else "low",
                "balance_health": "high" if total_balance > 1000000 else "medium" if total_balance > 500000 else "low",
                "employee_utilization": "high" if active_employees / total_employees > 0.8 else "medium" if active_employees / total_employees > 0.6 else "low"
            }

        except Exception as e:
            logger.error(f"Failed to calculate branch performance metrics: {str(e)}")
            raise

    async def _calculate_capacity_metrics(
        self,
        branch: Branch,
        accounts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate branch capacity metrics."""
        try:
            total_accounts = len(accounts)
            total_balance = sum(float(account.get("balance", 0)) for account in accounts)

            # Estimate capacity based on branch features
            estimated_capacity = 1000  # Base capacity
            if branch.has_atm:
                estimated_capacity += 500
            if branch.is_24x7:
                estimated_capacity += 300

            utilization_rate = total_accounts / estimated_capacity if estimated_capacity > 0 else 0

            return {
                "estimated_capacity": estimated_capacity,
                "current_utilization": total_accounts,
                "utilization_rate": utilization_rate,
                "available_capacity": estimated_capacity - total_accounts,
                "balance_per_account": total_balance / total_accounts if total_accounts > 0 else 0
            }

        except Exception as e:
            logger.error(f"Failed to calculate capacity metrics: {str(e)}")
            raise

    async def _analyze_utilization(
        self,
        branch: Branch,
        accounts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze branch utilization."""
        try:
            capacity_metrics = await self._calculate_capacity_metrics(branch, accounts)
            utilization_rate = capacity_metrics.get("utilization_rate", 0)

            return {
                "utilization_level": "high" if utilization_rate > 0.8 else "medium" if utilization_rate > 0.5 else "low",
                "capacity_status": "near_capacity" if utilization_rate > 0.9 else "optimal" if utilization_rate > 0.6 else "under_utilized",
                "recommendations": await self._generate_utilization_recommendations(utilization_rate, branch)
            }

        except Exception as e:
            logger.error(f"Failed to analyze utilization: {str(e)}")
            raise

    async def _get_employee_data_for_analysis(
        self,
        branch_id: int,
        employee_id: int
    ) -> Dict[str, Any]:
        """Get employee data for analysis."""
        try:
            # Get employee
            employee_query = select(Employee).where(
                and_(Employee.id == employee_id, Employee.branch_id == branch_id)
            )
            employee_result = await self.db_session.execute(employee_query)
            employee = employee_result.scalar_one_or_none()

            if not employee:
                raise EmployeeManagementError(f"Employee {employee_id} not found in branch {branch_id}")

            return {
                "employee_profile": employee.to_dict(),
                "branch_id": branch_id,
                "analysis_type": "employee_performance"
            }

        except Exception as e:
            logger.error(f"Failed to get employee data for analysis: {str(e)}")
            raise

    async def _calculate_average_tenure(
        self,
        employees: List[Employee]
    ) -> float:
        """Calculate average employee tenure."""
        try:
            if not employees:
                return 0.0

            total_tenure = 0
            for employee in employees:
                if employee.join_date:
                    tenure = (datetime.utcnow() - employee.join_date).days / 365.25
                    total_tenure += tenure

            return total_tenure / len(employees)

        except Exception as e:
            logger.error(f"Failed to calculate average tenure: {str(e)}")
            return 0.0

    async def _calculate_account_distribution(
        self,
        accounts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate account distribution."""
        try:
            if not accounts:
                return {}

            # Group by account type if available
            account_types = {}
            for account in accounts:
                account_type = account.get("account_type", "unknown")
                account_types[account_type] = account_types.get(account_type, 0) + 1

            return account_types

        except Exception as e:
            logger.error(f"Failed to calculate account distribution: {str(e)}")
            return {}

    async def _generate_capacity_recommendations(
        self,
        capacity_metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate capacity recommendations."""
        try:
            recommendations = []
            utilization_rate = capacity_metrics.get("utilization_rate", 0)

            if utilization_rate > 0.9:
                recommendations.append("Consider expanding branch capacity or opening new branches")
            elif utilization_rate < 0.3:
                recommendations.append("Consider optimizing branch operations or reducing staff")
            elif utilization_rate > 0.7:
                recommendations.append("Monitor capacity closely and plan for potential expansion")

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate capacity recommendations: {str(e)}")
            return []

    async def _generate_utilization_recommendations(
        self,
        utilization_rate: float,
        branch: Branch
    ) -> List[str]:
        """Generate utilization recommendations."""
        try:
            recommendations = []

            if utilization_rate > 0.9:
                recommendations.append("High utilization - consider capacity expansion")
            elif utilization_rate < 0.3:
                recommendations.append("Low utilization - consider operational optimization")
            elif not branch.has_atm and utilization_rate > 0.6:
                recommendations.append("Consider adding ATM services to improve capacity")

            return recommendations

        except Exception as e:
            logger.error(f"Failed to generate utilization recommendations: {str(e)}")
            return [] 