"""
Enhanced base repository with AI integration, caching, and advanced analytics.
"""
from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Tuple
from uuid import UUID

from sqlalchemy import and_, delete, select, update, func, text
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import ModelBase
from app.core.llm_orchestrator import LLMOrchestrator, LLMRequest, TaskType, TaskComplexity
# Exception imports removed for MVP
# All custom exceptions replaced with standard logging

# Type variables
ModelType = TypeVar("ModelType", bound=ModelBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=dict)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=dict)

logger = logging.getLogger(__name__)


class CacheManager:
    """Simple in-memory cache manager (can be replaced with Redis)."""
    
    def __init__(self):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._default_ttl = 3600  # 1 hour
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        """Set value in cache."""
        ttl = ttl or self._default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)
    
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
    
    async def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()


class AIEnhancedRepository(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Enhanced base repository with AI integration, caching, and advanced analytics.
    
    This repository extends the basic CRUD operations with:
    - AI-powered analysis and insights
    - Intelligent caching for performance
    - Advanced query capabilities
    - Behavioral pattern analysis
    - Risk assessment integration
    """
    
    def __init__(
        self, 
        model: Type[ModelType], 
        db_session: Union[Session, AsyncSession],
        llm_orchestrator: Optional[LLMOrchestrator] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        self.model = model
        self.db_session = db_session
        self.llm_orchestrator = llm_orchestrator or LLMOrchestrator()
        self.cache_manager = cache_manager or CacheManager()
        
    # ==================== Basic CRUD Operations ====================
    
    async def get_by_id(
        self, 
        id: Union[int, str, UUID],
        *, 
        include_inactive: bool = False,
        load_relationships: bool = False,
        use_cache: bool = True
    ) -> Optional[ModelType]:
        """Get a record by ID with optional caching."""
        cache_key = f"{self.model.__name__.lower()}:{id}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached
        
        query = select(self.model).where(self.model.id == id)
        
        if hasattr(self.model, "is_active") and not include_inactive:
            query = query.where(self.model.is_active == True)  # noqa: E712
            
        if load_relationships and hasattr(self.model, "__mapper__"):
            for relationship in self.model.__mapper__.relationships:
                query = query.options(selectinload(relationship.key))
                
        result = await self.db_session.execute(query)
        record = result.scalar_one_or_none()
        
        if record and use_cache:
            await self.cache_manager.set(cache_key, record, ttl=1800)  # 30 minutes
            
        return record

    async def get_multi(
        self,
        *, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False,
        load_relationships: bool = False,
        use_cache: bool = True,
        **filters: Any,
    ) -> List[ModelType]:
        """Get multiple records with filtering, pagination, and caching."""
        # Create cache key based on filters
        filter_str = json.dumps(sorted(filters.items()), sort_keys=True)
        cache_key = f"{self.model.__name__.lower()}_multi:{filter_str}:{skip}:{limit}"
        
        if use_cache:
            cached = await self.cache_manager.get(cache_key)
            if cached:
                return cached
        
        query = select(self.model)
        
        # Apply filters
        if filters:
            conditions = [
                getattr(self.model, key) == value 
                for key, value in filters.items()
                if hasattr(self.model, key)
            ]
            if conditions:
                query = query.where(and_(*conditions))
                
        # Handle soft delete
        if hasattr(self.model, "is_active") and not include_inactive:
            query = query.where(self.model.is_active == True)  # noqa: E712
            
        # Eager load relationships if requested
        if load_relationships and hasattr(self.model, "__mapper__"):
            for relationship in self.model.__mapper__.relationships:
                query = query.options(selectinload(relationship.key))
                
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db_session.execute(query)
        records = result.scalars().all()
        
        if use_cache:
            await self.cache_manager.set(cache_key, records, ttl=900)  # 15 minutes
            
        return records

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record with cache invalidation."""
        db_obj = self.model(**obj_in)
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        
        # Invalidate related caches
        await self._invalidate_related_caches()
        
        return db_obj

    async def update(
        self, 
        db_obj: ModelType, 
        obj_in: Union[UpdateSchemaType, dict[str, Any]]
    ) -> ModelType:
        """Update a record with cache invalidation."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        
        # Invalidate related caches
        await self._invalidate_related_caches()
        
        return db_obj

    async def delete(self, db_obj: ModelType) -> None:
        """Delete a record with cache invalidation."""
        await self.db_session.delete(db_obj)
        await self.db_session.commit()
        
        # Invalidate related caches
        await self._invalidate_related_caches()

    # ==================== AI Integration Methods ====================
    
    async def analyze_with_ai(
        self, 
        data: Dict[str, Any], 
        analysis_type: TaskType,
        complexity: TaskComplexity = TaskComplexity.MEDIUM
    ) -> Dict[str, Any]:
        """Analyze data using AI models."""
        try:
            prompt = self._create_analysis_prompt(data, analysis_type)
            
            request = LLMRequest(
                prompt=prompt,
                task_type=analysis_type,
                complexity=complexity,
                context=data
            )
            
            response = await self.llm_orchestrator.process_request(request)
            
            return self._parse_ai_response(response, analysis_type)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {}

    async def generate_insights(
        self, 
        user_id: int, 
        data_type: str,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI insights for user data."""
        try:
            # Get user data
            user_data = await self._get_user_data_for_analysis(user_id, data_type, time_range)
            
            # Determine analysis type based on data type
            analysis_type = self._get_analysis_type_for_data(data_type)
            
            # Analyze with AI
            analysis_result = await self.analyze_with_ai(user_data, analysis_type)
            
            # Cache the insights
            cache_key = f"insights:{user_id}:{data_type}:{time_range or 'all'}"
            await self.cache_manager.set(cache_key, analysis_result, ttl=3600)
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {str(e)}")
            return {}

    async def detect_anomalies(
        self, 
        data: List[Dict[str, Any]], 
        threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in data using AI."""
        try:
            prompt = self._create_anomaly_detection_prompt(data, threshold)
            
            request = LLMRequest(
                prompt=prompt,
                task_type=TaskType.RISK_ASSESSMENT,
                complexity=TaskComplexity.HIGH,
                context={"data": data, "threshold": threshold}
            )
            
            response = await self.llm_orchestrator.process_request(request)
            
            return self._parse_anomaly_response(response)
            
        except Exception as e:
            logger.error(f"Anomaly detection failed: {str(e)}")
            return []

    # ==================== Advanced Analytics Methods ====================
    
    async def get_behavioral_analytics(
        self, 
        user_id: int, 
        time_range: str = "30d"
    ) -> Dict[str, Any]:
        """Get comprehensive behavioral analytics for a user."""
        cache_key = f"behavioral_analytics:{user_id}:{time_range}"
        
        # Check cache first
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            # Get user transactions
            transactions = await self._get_user_transactions(user_id, time_range)
            
            # Analyze spending patterns
            spending_analysis = await self._analyze_spending_patterns(transactions)
            
            # Analyze temporal patterns
            temporal_analysis = await self._analyze_temporal_patterns(transactions)
            
            # Analyze geographic patterns
            geographic_analysis = await self._analyze_geographic_patterns(transactions)
            
            # Generate AI insights
            ai_insights = await self.generate_insights(user_id, "behavioral", time_range)
            
            analytics_result = {
                "user_id": user_id,
                "time_range": time_range,
                "spending_analysis": spending_analysis,
                "temporal_analysis": temporal_analysis,
                "geographic_analysis": geographic_analysis,
                "ai_insights": ai_insights,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            await self.cache_manager.set(cache_key, analytics_result, ttl=7200)  # 2 hours
            
            return analytics_result
            
        except Exception as e:
            logger.error(f"Behavioral analytics failed: {str(e)}")
            return {}

    async def get_risk_assessment(
        self, 
        user_id: int, 
        assessment_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Get comprehensive risk assessment for a user."""
        cache_key = f"risk_assessment:{user_id}:{assessment_type}"
        
        # Check cache first
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return cached
        
        try:
            # Get user data for risk assessment
            user_data = await self._get_user_risk_data(user_id)
            
            # Perform risk analysis
            risk_analysis = await self._perform_risk_analysis(user_data, assessment_type)
            
            # Generate AI risk insights
            ai_risk_insights = await self.analyze_with_ai(
                user_data, 
                TaskType.RISK_ASSESSMENT,
                TaskComplexity.HIGH
            )
            
            risk_result = {
                "user_id": user_id,
                "assessment_type": assessment_type,
                "risk_score": risk_analysis.get("overall_risk_score", 0.0),
                "risk_factors": risk_analysis.get("risk_factors", []),
                "ai_insights": ai_risk_insights,
                "assessment_date": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            await self.cache_manager.set(cache_key, risk_result, ttl=3600)  # 1 hour
            
            return risk_result
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {str(e)}")
            return {}

    # ==================== Performance Optimization Methods ====================
    
    async def bulk_create(
        self, 
        objects: List[CreateSchemaType],
        batch_size: int = 1000
    ) -> List[ModelType]:
        """Bulk create records for better performance."""
        created_objects = []
        
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            batch_objects = [self.model(**obj) for obj in batch]
            
            self.db_session.add_all(batch_objects)
            await self.db_session.commit()
            
            # Refresh objects to get IDs
            for obj in batch_objects:
                await self.db_session.refresh(obj)
            
            created_objects.extend(batch_objects)
        
        # Invalidate caches
        await self._invalidate_related_caches()
        
        return created_objects

    async def bulk_update(
        self, 
        filter_criteria: Dict[str, Any],
        update_data: Dict[str, Any]
    ) -> int:
        """Bulk update records matching criteria."""
        query = update(self.model).where(
            and_(*[getattr(self.model, key) == value for key, value in filter_criteria.items()])
        ).values(**update_data)
        
        result = await self.db_session.execute(query)
        await self.db_session.commit()
        
        # Invalidate caches
        await self._invalidate_related_caches()
        
        return result.rowcount

    # ==================== Cache Management Methods ====================
    
    async def _invalidate_related_caches(self) -> None:
        """Invalidate related caches when data changes."""
        # This is a simple implementation - can be enhanced based on specific needs
        cache_patterns = [
            f"{self.model.__name__.lower()}:*",
            f"{self.model.__name__.lower()}_multi:*",
            "insights:*",
            "behavioral_analytics:*",
            "risk_assessment:*"
        ]
        
        # In a real implementation with Redis, you would use pattern-based deletion
        # For now, we'll just clear the entire cache
        await self.cache_manager.clear()

    # ==================== Helper Methods ====================
    
    def _create_analysis_prompt(self, data: Dict[str, Any], analysis_type: TaskType) -> str:
        """Create analysis prompt based on data and analysis type."""
        if analysis_type == TaskType.BEHAVIORAL_ANALYSIS:
            return self._create_behavioral_analysis_prompt(data)
        elif analysis_type == TaskType.RISK_ASSESSMENT:
            return self._create_risk_assessment_prompt(data)
        elif analysis_type == TaskType.FINANCIAL_RECOMMENDATION:
            return self._create_recommendation_prompt(data)
        else:
            return self._create_general_analysis_prompt(data)

    def _create_behavioral_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create prompt for behavioral analysis."""
        return f"""
        Analyze the following customer transaction data for behavioral patterns:
        
        Data: {json.dumps(data, indent=2)}
        
        Please provide:
        1. Spending pattern analysis
        2. Behavioral insights
        3. Risk indicators
        4. Recommendations
        
        Format the response as JSON with the following structure:
        {{
            "spending_patterns": {{}},
            "behavioral_insights": [],
            "risk_indicators": [],
            "recommendations": []
        }}
        """

    def _create_risk_assessment_prompt(self, data: Dict[str, Any]) -> str:
        """Create prompt for risk assessment."""
        return f"""
        Assess the risk level for the following customer data:
        
        Data: {json.dumps(data, indent=2)}
        
        Please provide:
        1. Overall risk score (0-1)
        2. Risk factors
        3. Risk level (Low/Medium/High)
        4. Mitigation recommendations
        
        Format the response as JSON with the following structure:
        {{
            "risk_score": 0.0,
            "risk_level": "Low",
            "risk_factors": [],
            "mitigation_recommendations": []
        }}
        """

    def _create_recommendation_prompt(self, data: Dict[str, Any]) -> str:
        """Create prompt for financial recommendations."""
        return f"""
        Generate personalized financial recommendations based on:
        
        Data: {json.dumps(data, indent=2)}
        
        Please provide:
        1. Product recommendations
        2. Behavioral recommendations
        3. Savings suggestions
        4. Investment advice
        
        Format the response as JSON with the following structure:
        {{
            "product_recommendations": [],
            "behavioral_recommendations": [],
            "savings_suggestions": [],
            "investment_advice": []
        }}
        """

    def _create_general_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """Create general analysis prompt."""
        return f"""
        Analyze the following data and provide insights:
        
        Data: {json.dumps(data, indent=2)}
        
        Please provide a comprehensive analysis with actionable insights.
        """

    def _create_anomaly_detection_prompt(self, data: List[Dict[str, Any]], threshold: float) -> str:
        """Create prompt for anomaly detection."""
        return f"""
        Detect anomalies in the following transaction data with threshold {threshold}:
        
        Data: {json.dumps(data, indent=2)}
        
        Please identify:
        1. Unusual spending patterns
        2. Geographic anomalies
        3. Temporal anomalies
        4. Amount anomalies
        
        Format the response as JSON with the following structure:
        {{
            "anomalies": [
                {{
                    "type": "spending|geographic|temporal|amount",
                    "description": "",
                    "confidence": 0.0,
                    "severity": "low|medium|high"
                }}
            ]
        }}
        """

    def _parse_ai_response(self, response: Any, analysis_type: TaskType) -> Dict[str, Any]:
        """Parse AI response based on analysis type."""
        try:
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Try to parse as JSON
            if isinstance(content, str):
                return json.loads(content)
            else:
                return content
                
        except json.JSONDecodeError:
            # If not JSON, return as text
            return {"analysis": content, "type": analysis_type.value}

    def _parse_anomaly_response(self, response: Any) -> List[Dict[str, Any]]:
        """Parse anomaly detection response."""
        try:
            parsed = self._parse_ai_response(response, TaskType.RISK_ASSESSMENT)
            return parsed.get("anomalies", [])
        except Exception:
            return []

    def _get_analysis_type_for_data(self, data_type: str) -> TaskType:
        """Get appropriate analysis type for data type."""
        mapping = {
            "behavioral": TaskType.BEHAVIORAL_ANALYSIS,
            "risk": TaskType.RISK_ASSESSMENT,
            "recommendation": TaskType.FINANCIAL_RECOMMENDATION,
            "transaction": TaskType.BEHAVIORAL_ANALYSIS,
            "spending": TaskType.BEHAVIORAL_ANALYSIS,
            "fraud": TaskType.RISK_ASSESSMENT
        }
        return mapping.get(data_type, TaskType.GENERAL_QUERY)

    # ==================== Abstract Methods (to be implemented by subclasses) ====================
    
    @abstractmethod
    async def _get_user_data_for_analysis(self, user_id: int, data_type: str, time_range: Optional[str] = None) -> Dict[str, Any]:
        """Get user data for AI analysis."""
        pass

    @abstractmethod
    async def _get_user_transactions(self, user_id: int, time_range: str) -> List[Dict[str, Any]]:
        """Get user transactions for analysis."""
        pass

    @abstractmethod
    async def _get_user_risk_data(self, user_id: int) -> Dict[str, Any]:
        """Get user data for risk assessment."""
        pass

    @abstractmethod
    async def _analyze_spending_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze spending patterns."""
        pass

    @abstractmethod
    async def _analyze_temporal_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns."""
        pass

    @abstractmethod
    async def _analyze_geographic_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze geographic patterns."""
        pass

    @abstractmethod
    async def _perform_risk_analysis(self, user_data: Dict[str, Any], assessment_type: str) -> Dict[str, Any]:
        """Perform risk analysis."""
        pass 