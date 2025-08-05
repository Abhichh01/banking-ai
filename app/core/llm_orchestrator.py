"""LLM Orchestrator for intelligent model selection and management."""

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from app.core.config import get_settings

settings = get_settings()

# Configure logging
logger = logging.getLogger(__name__)

class TaskType(str, Enum):
    """Types of tasks the LLM can perform."""
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    FINANCIAL_RECOMMENDATION = "financial_recommendation"
    RISK_ASSESSMENT = "risk_assessment"
    GENERAL_QUERY = "general_query"

class TaskComplexity(str, Enum):
    """Complexity levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class LLMRequest(BaseModel):
    """Request structure for LLM processing."""
    prompt: str
    task_type: TaskType
    complexity: TaskComplexity = TaskComplexity.MEDIUM
    context: Optional[Dict[str, Any]] = None
    temperature: float = 0.7
    max_tokens: int = 1000

class LLMResponse(BaseModel):
    """Response structure from LLM processing."""
    content: str
    model_used: str
    tokens_used: int
    processing_time: float
    metadata: Dict[str, Any] = {}

class LLMOrchestrator:
    """
    Intelligent LLM orchestrator that selects optimal models based on task requirements.
    Implements fallback mechanisms, performance tracking, and cost optimization.
    """
    
    def __init__(self):
        """Initialize the LLM orchestrator with model configurations."""
        self.models = self._initialize_models()
        self.model_metrics = {model_id: {"success": 0, "errors": 0, "avg_time": 0} 
                            for model_id in self.models.keys()}
    
    def _initialize_models(self) -> Dict[str, Dict]:
        """Initialize available LLM models with their configurations."""
        return {
            "gpt-4o": {
                "provider": "openai",
                "capabilities": {
                    TaskType.BEHAVIORAL_ANALYSIS: TaskComplexity.HIGH,
                    TaskType.FINANCIAL_RECOMMENDATION: TaskComplexity.HIGH,
                    TaskType.RISK_ASSESSMENT: TaskComplexity.HIGH,
                    TaskType.GENERAL_QUERY: TaskComplexity.HIGH,
                },
                "cost_per_token": 0.00001,
                "max_tokens": 128000,
                "api_key": settings.OPENAI_API_KEY,
            },
            "claude-3-sonnet-20240229": {
                "provider": "anthropic",
                "capabilities": {
                    TaskType.BEHAVIORAL_ANALYSIS: TaskComplexity.HIGH,
                    TaskType.FINANCIAL_RECOMMENDATION: TaskComplexity.MEDIUM,
                    TaskType.RISK_ASSESSMENT: TaskComplexity.HIGH,
                    TaskType.GENERAL_QUERY: TaskComplexity.HIGH,
                },
                "cost_per_token": 0.000015,
                "max_tokens": 200000,
                "api_key": settings.ANTHROPIC_API_KEY,
            },
            "llama-3-70b": {
                "provider": "local",
                "capabilities": {
                    TaskType.BEHAVIORAL_ANALYSIS: TaskComplexity.MEDIUM,
                    TaskType.FINANCIAL_RECOMMENDATION: TaskComplexity.LOW,
                    TaskType.RISK_ASSESSMENT: TaskComplexity.MEDIUM,
                    TaskType.GENERAL_QUERY: TaskComplexity.MEDIUM,
                },
                "cost_per_token": 0.0,  # Local model
                "max_tokens": 8000,
                "model_path": settings.LOCAL_MODEL_PATH,
            }
        }
    
    async def process_request(self, request: LLMRequest) -> LLMResponse:
        """
        Process an LLM request with intelligent model selection and fallback.
        
        Args:
            request: The LLM request to process.
            
        Returns:
            LLMResponse: The response from the selected model.
            
        Raises:
            ValueError: If no suitable model is found for the task.
        """
        start_time = datetime.utcnow()
        
        # Select the best model for the task
        model_id = self._select_model(request.task_type, request.complexity)
        if not model_id:
            raise ValueError(f"No suitable model found for task type {request.task_type} "
                           f"with complexity {request.complexity}")
        
        logger.info(f"Selected model {model_id} for {request.task_type} task")
        
        try:
            # Process the request with the selected model
            response = await self._call_model(model_id, request)
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()
            
            # Update metrics
            self._update_metrics(model_id, success=True, processing_time=processing_time)
            
            return LLMResponse(
                content=response,
                model_used=model_id,
                tokens_used=len(response.split()),  # Approximation
                processing_time=processing_time,
                metadata={"model_id": model_id}
            )
            
        except Exception as e:
            logger.error(f"Error processing request with {model_id}: {str(e)}")
            self._update_metrics(model_id, success=False)
            
            # Try fallback model if available
            fallback_model = self._get_fallback_model(model_id, request.task_type)
            if fallback_model and fallback_model != model_id:
                logger.info(f"Trying fallback model {fallback_model}")
                return await self.process_request(request)  # Retry with fallback
                
            raise  # Re-raise if no fallback available or fallback also failed
    
    def _select_model(self, task_type: TaskType, complexity: TaskComplexity) -> Optional[str]:
        """Select the most appropriate model for the given task and complexity."""
        # Simple implementation - can be enhanced with more sophisticated logic
        for model_id, model_config in self.models.items():
            if task_type in model_config["capabilities"]:
                if model_config["capabilities"][task_type].value >= complexity.value:
                    return model_id
        return None
    
    def _get_fallback_model(self, current_model: str, task_type: TaskType) -> Optional[str]:
        """Get a fallback model if the current one fails."""
        # Simple round-robin fallback - can be enhanced
        model_ids = list(self.models.keys())
        try:
            current_idx = model_ids.index(current_model)
            next_idx = (current_idx + 1) % len(model_ids)
            return model_ids[next_idx]
        except ValueError:
            return None
    
    def _update_metrics(self, model_id: str, success: bool, processing_time: float = 0):
        """Update performance metrics for a model."""
        if model_id not in self.model_metrics:
            self.model_metrics[model_id] = {"success": 0, "errors": 0, "avg_time": 0}
            
        metrics = self.model_metrics[model_id]
        
        if success:
            metrics["success"] += 1
            # Update average processing time using moving average
            total_requests = metrics["success"] + metrics["errors"]
            metrics["avg_time"] = (
                (metrics["avg_time"] * (total_requests - 1) + processing_time) 
                / total_requests
            )
        else:
            metrics["errors"] += 1
    
    async def _call_model(self, model_id: str, request: LLMRequest) -> str:
        """
        Make the actual API call to the specified model.
        
        This is a placeholder that would be implemented with actual API calls
        to the respective LLM providers.
        """
        model_config = self.models[model_id]
        
        # In a real implementation, this would make actual API calls to the respective providers
        if model_config["provider"] == "openai":
            # Call OpenAI API
            return f"Response from {model_id} for {request.task_type} task"
        elif model_config["provider"] == "anthropic":
            # Call Anthropic API
            return f"Response from {model_id} for {request.task_type} task"
        elif model_config["provider"] == "local":
            # Call local model
            return f"Response from local {model_id} for {request.task_type} task"
        else:
            raise ValueError(f"Unsupported model provider: {model_config['provider']}")
